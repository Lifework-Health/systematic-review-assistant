"""Screening prompts and agents/chains. Also Streamlit chat UI agent(s).

These are not agents, just chains.

Considering we're using OpenAI for the prototype, it doesn't make sense to use two
different models to emulate human reviewers. Instead, we'll use the same model but
with two different prompts to better simulate human reviewers.

One is "conservative" and the other is "comprehensive"..

The key differences are in:

1. How they interpret missing information
2. What constitutes sufficient evidence
3. Confidence scoring interpretation
4. Threshold for uncertainty

Both get the same criteria and be asked for the same structured output, but their
interpretation frameworks differ. This should give us meaningful differences in
screening decisions while maintaining high-quality assessment.

## Concurrency

As we run with Streamlit for the prototype, concurrency could be handled either with
a threadpool executor, TaskGroup, or a queue with, e.g., Supabase edge function workers.
For this initial prototype, we'll stay within Streamlit and leverage LangChain
runnables' parallel and batching capabilities, which use a threadpool executor
under the hood.

## TODO

- Either move types here or from here to core.types/schemas. Not both.
"""

from __future__ import annotations

import os
import typing as t
import uuid
from copy import deepcopy
from datetime import datetime, timezone

import streamlit as st
from langchain_community.callbacks.manager import get_openai_callback
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig, RunnableParallel
from langchain_openai import ChatOpenAI
from loguru import logger
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    TypeAdapter,
    model_validator,
)

import sr_assistant.app.utils as ut
from sr_assistant.core import models, schemas
from sr_assistant.core.schemas import (
    ScreeningResolutionSchema,
    ScreeningResponse,
    ScreeningResult,
)
from sr_assistant.core.types import ScreeningStrategyType

if t.TYPE_CHECKING:
    from langchain_community.callbacks.openai_info import OpenAICallbackHandler
    from langchain_core.tracers.schemas import Run


# Resolver model and chain for resolving disagreements between reviewers
RESOLVER_MODEL = ChatOpenAI(
    model=os.getenv("SRA_RESOLVER_MODEL", "o3-mini-high"),
    api_key=SecretStr(os.getenv("OPENAI_API_KEY") or ""),
    temperature=0.0,
)

resolver_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """\
You are an expert systematic review screening assistant, built to resolve disputes between reviewers with confidence.

We've two reviewers disagreeing on whether a given PubMed search result should be included in a systematic review.

one is using a "comprehensive" screening strategy, and the other is using a "conservative" screening strategy. These prioritize sensitivity and accuracy as different human reviewers might.

You will be given the search result, the systematic review, and the two reviewers' screening results.""",
        ),
        (
            "human",
            """\
<search_result>
{search_result}
</search_result>

<systematic_review>
{systematic_review}
</systematic_review>

<comprehensive_reviewer_result>
{comprehensive_reviewer_result}
</comprehensive_reviewer_result>

<conservative_reviewer_result>
{conservative_reviewer_result}
</conservative_reviewer_result>

<resolver_output>
{resolver_output}
</resolver_output>""",
        ),
    ]
)

# Create resolver chain with structured output
resolver_model_struct_output = RESOLVER_MODEL.with_structured_output(
    ScreeningResolutionSchema
)
resolver_chain = resolver_prompt | resolver_model_struct_output


def make_resolver_chain_input(
    pubmed_result: models.PubMedResult,
    review: models.SystematicReview,
    conservative_result: ScreeningResult,
    comprehensive_result: ScreeningResult,
) -> dict[str, str]:
    """Create input for resolver_chain.

    Args:
        pubmed_result: The PubMed search result with conflicting screening decisions
        review: The systematic review
        conservative_result: The screening result from the conservative reviewer
        comprehensive_result: The screening result from the comprehensive reviewer

    Returns:
        dict: Input variables for the resolver prompt
    """
    # Format search result for the prompt
    search_result = f"""
Title: {pubmed_result.title}
PMID: {pubmed_result.pmid}
Journal: {pubmed_result.journal}
Year: {pubmed_result.year}
Abstract: {pubmed_result.abstract}
"""

    # Format systematic review for the prompt
    systematic_review = f"""
Research Question: {review.research_question}
Background: {review.background or "Not provided"}
# Use correct fields based on model update
Criteria Framework: {review.criteria_framework.value if review.criteria_framework else "N/A"}
Criteria Answers: {review.criteria_framework_answers if review.criteria_framework_answers else "{}"}
Exclusion Criteria: {review.exclusion_criteria}
"""

    # Format conservative result for the prompt
    conservative_reviewer_result = f"""
Decision: {conservative_result.decision}
Confidence Score: {conservative_result.confidence_score}
Rationale: {conservative_result.rationale}
"""
    if conservative_result.extracted_quotes:
        conservative_reviewer_result += (
            f"Extracted Quotes: {', '.join(conservative_result.extracted_quotes)}\n"
        )

    # Format comprehensive result for the prompt
    comprehensive_reviewer_result = f"""
Decision: {comprehensive_result.decision}
Confidence Score: {comprehensive_result.confidence_score}
Rationale: {comprehensive_result.rationale}
"""
    if comprehensive_result.extracted_quotes:
        comprehensive_reviewer_result += (
            f"Extracted Quotes: {', '.join(comprehensive_result.extracted_quotes)}\n"
        )

    return {
        "search_result": search_result,
        "systematic_review": systematic_review,
        "conservative_reviewer_result": conservative_reviewer_result,
        "comprehensive_reviewer_result": comprehensive_reviewer_result,
    }


def resolve_screening_conflict(
    pubmed_result: models.PubMedResult,
    review: models.SystematicReview,
    conservative_result: ScreeningResult,
    comprehensive_result: ScreeningResult,
) -> models.ScreeningResolution:
    """Resolve conflicting screening decisions between conservative and comprehensive reviewers.

    Args:
        pubmed_result: PubMed search result with conflicting screening decisions
        review: Systematic review
        conservative_result: Screening result from the conservative reviewer
        comprehensive_result: Screening result from the comprehensive reviewer

    Returns:
        models.ScreeningResolution: The resolution decision

    Raises:
        Exception: If the resolver chain fails
    """
    logger.info(
        f"Resolving screening conflict for PMID: {pubmed_result.pmid}, conservative: {conservative_result.decision}, comprehensive: {comprehensive_result.decision}"
    )

    # Create chain input
    chain_input = make_resolver_chain_input(
        pubmed_result=pubmed_result,
        review=review,
        conservative_result=conservative_result,
        comprehensive_result=comprehensive_result,
    )

    # Track execution time and invoke chain
    start_time = datetime.now(tz=timezone.utc)

    try:
        with get_openai_callback() as cb:
            # Invoke the resolver chain
            # Use Any for result until converted to schema
            result = resolver_chain.invoke(
                chain_input,
                config=RunnableConfig(
                    tags=[
                        "sra:resolver",
                        f"sra:review_id:{review.id}",
                        f"sra:pubmed_result_id:{pubmed_result.id}",
                    ],
                    metadata={
                        "review_id": str(review.id),
                        "pubmed_result_id": str(pubmed_result.id),
                        "conservative_result_id": str(conservative_result.id),
                        "comprehensive_result_id": str(comprehensive_result.id),
                    },
                ),
            )

        end_time = datetime.now(tz=timezone.utc)
        logger.info(
            f"Resolver chain completed in {(end_time - start_time).total_seconds():.2f}s, "
            + f"tokens: {cb.total_tokens}, cost: ${cb.total_cost:.4f}"
        )

        # Convert result to proper schema if needed
        if not isinstance(result, ScreeningResolutionSchema):
            result = ScreeningResolutionSchema.model_validate(result)

        # Create ScreeningResolution model
        resolution = models.ScreeningResolution(
            id=uuid.uuid4(),
            review_id=review.id,
            pubmed_result_id=pubmed_result.id,
            conservative_result_id=conservative_result.id,
            comprehensive_result_id=comprehensive_result.id,
            resolver_decision=result.resolver_decision,
            resolver_reasoning=result.resolver_reasoning,
            resolver_confidence_score=result.resolver_confidence_score,
            resolver_model_name=RESOLVER_MODEL.model_name,
            start_time=start_time,
            end_time=end_time,
            trace_id=None,
            response_metadata={
                "tokens": {
                    "total": cb.total_tokens,
                    "prompt": cb.prompt_tokens,
                    "completion": cb.completion_tokens,
                },
                "cost": cb.total_cost,
            },
        )

        logger.info(
            f"Resolution: {resolution.resolver_decision}, confidence: {resolution.resolver_confidence_score}"
        )

        return resolution

    except Exception as e:
        logger.exception(
            f"Error resolving screening conflict for PMID: {pubmed_result.pmid}",
            exc_info=e,
        )
        raise


class ScreenAbstractsChainOutputDict(t.TypedDict):
    """Final output from screen_abstracts_chain RunnableParallel call.

    Attributes:
        conservative (ScreeningResult|ScreeningResponse|t.Any): The conservative screening
            strategy result. Should be a `ScreeningResult`
            but may be `ScreeningResponse` if ``on_end`` listener failed parsing
            :class:`langsmith.RunTree`s. Or `typing.Any` depending on listener input
            RunTree. Caller should handle this.
        comprehensive (ScreeningResult|ScreeningResponse|t.Any): Same as above, but for
            comprehensive strategy.
    """

    conservative: ScreeningResult | ScreeningResponse | t.Any
    comprehensive: ScreeningResult | ScreeningResponse | t.Any


class ScreenAbstractsChainInput(BaseModel):
    """screen_abstracts_chain() prompt input variables.

    Attributes:
        background (str | None), optional: Background of the systematic review.
        research_question (str): Research question of the systematic review.
        inclusion_criteria (str): Inclusion criteria of the systematic review.
        exclusion_criteria (str): Exclusion criteria of the systematic review.
        title (str): Title of the PubMed search result.
        journal (str): Journal of the PubMed search result.
        year (str): Year of the PubMed search result.
        abstract (str): Abstract of the PubMed search result.

    Todo:
        - Use prompt .get_input_schema():
            ``ScreenAbstractsChainInput = prompt.get_input_schema()``
            or sublass as we want config (can it be passed?)

    Note:
        Update when prompt changes
    """

    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        extra="ignore",
    )
    # Protocol
    background: str | None = Field(default="<no background provided>")
    research_question: str
    inclusion_criteria: str
    exclusion_criteria: str
    # Search result
    title: str
    journal: str
    year: str
    abstract: str


class ScreenAbstractsChainInputDict(t.TypedDict):
    """Represents ScreenAbstractsChainInput.model_dump(). For type checking reasons.

    Attributes:
        background (str | None), optional: Background of the systematic review.
        research_question (str): Research question of the systematic review.
        inclusion_criteria (str): Inclusion criteria of the systematic review.
        exclusion_criteria (str): Exclusion criteria of the systematic review.
        title (str): Title of the PubMed search result.
        journal (str): Journal of the PubMed search result.
        year (str): Year of the PubMed search result.
        abstract (str): Abstract of the PubMed search result.

    Todo:
        - Generate from schema

    Note:
        Update when prompt changes

    """

    background: t.NotRequired[str]
    research_question: str
    inclusion_criteria: str
    exclusion_criteria: str
    title: str
    journal: str
    year: str
    abstract: str


screen_abstracts_chain_input_dict_adapter = TypeAdapter(ScreenAbstractsChainInputDict)
"""TODO: .validate_python() in screening wrapper"""


class ScreenAbstractsChainBatchInputDict(t.TypedDict):
    """chain.batch(**this_input).

    Attributes:
        inputs (list[ScreenAbstractsChainInput])
        config (list[RunnableConfig])
    """

    inputs: list[ScreenAbstractsChainInputDict]
    config: list[RunnableConfig]


class ScreeningError(BaseModel):
    """Screening error.

    Attributes:
        search_result (PubMedResult): PubMed search result associated with this screening error
        error (t.Any): Error encountered during screening
        message (str | None): Human-readable error message. Default is None.
    """

    search_result: models.PubMedResult = Field(
        description="PubMed search result associated with this screening error"
    )
    error: t.Any = Field(description="Error encountered during screening")
    message: str | None = Field(
        default=None, description="Human-readable error message"
    )

    @model_validator(mode="after")
    def _validate_error_and_message(self) -> t.Self:  # this is an instance method
        if isinstance(self.error, ScreeningResult) and self.message is None:
            msg = "ScreeningResult should always have a message"
            logger.warning(msg)
            self.message = msg
        if isinstance(self.error, ScreeningResponse) and self.message is None:
            msg = "Chain on_end failed, this is nested chain's screening output"
            logger.warning(msg)
            self.message = msg
        return self


class ScreenAbstractResultTuple(t.NamedTuple):
    """Tuple of pubmed result and its screening results.

    Attributes:
        search_result (PubMedResult): PubMed search result associated with this screening
        conservative_result (ScreeningResult | ScreeningError): Screening result for conservative strategy
        comprehensive_result (ScreeningResult | ScreeningError): Screening result for comprehensive strategy
    """

    search_result: models.PubMedResult
    conservative_result: ScreeningResult | ScreeningError
    comprehensive_result: ScreeningResult | ScreeningError


@logger.catch(onerror=lambda exc: st.error(exc) if ut.in_streamlit() else None)  # pyright: ignore [reportArgumentType]
def chain_on_error_listener_cb(error: BaseException, **kwargs: t.Any) -> None:
    """Listener for Runnable sequence on_error events."""
    run_obj = kwargs.get("run")
    run_id = getattr(run_obj, "id", "unknown")
    run_name = getattr(run_obj, "name", "unknown")
    cb_logger = logger.bind(run_id=run_id, run_name=run_name)
    # Use logger.exception to include traceback
    cb_logger.exception(
        f"Error during chain execution: run_id={run_id}, error={error!r}, kwargs={kwargs!r}",
        error=error,
        kwargs=kwargs,
    )
    # Optionally log child runs if needed, checking if run_obj exists and has child_runs
    if run_obj and hasattr(run_obj, "child_runs") and run_obj.child_runs:
        cb_logger.error("Associated run object: {run_obj!r}", run_obj=run_obj)
        for cr in run_obj.child_runs:
            cb_cr_logger = logger.bind(
                run_id=getattr(cr, "id", "unknown"),
                run_name=getattr(cr, "name", "unknown"),
                parent_run_id=run_id,
                parent_run_name=run_name,
            )
            cb_cr_logger.error("Associated child run: {cr!r}", cr=cr)


@logger.catch(onerror=lambda exc: st.error(exc) if ut.in_streamlit() else None)  # pyright: ignore [reportArgumentType]
def screen_abstracts_chain_on_end_cb(run_obj: Run) -> None:  # noqa: C901
    """Listener for screening batch run on_end hook.

    See `.with_listeners <https://python.langchain.com/api_reference/_modules/langchain_core/runnables/base.html#RunnableBinding.with_listeners>`_

    Modifications to the `Run`|`RunTree` persist and no need to return anything. It's a
    Pydantic v1 model.

    Todo:
        - More metadata extraction
    """
    cr_logger = logger.bind(run_id=run_obj.id, run_name=run_obj.name)
    cr_logger.debug(f"screen_abstracts_chain_on_end_cb got RunTree: {run_obj!r}")
    if not run_obj.outputs:
        cr_logger.warning(f"No outputs for run: {run_obj!r}")
        return
    # Each child run is one screening chain invocation within RunnableParallel. This
    # parent RunTree is the RunnableParallel itself.
    for cr in run_obj.child_runs:
        cr_logger = logger.bind(
            run_id=cr.id,
            run_name=cr.name,
            parent_run_id=run_obj.id,
            parent_run_name=run_obj.name,
        )
        cr_logger.debug(f"screen_abstracts_chain_on_end_cb got child run: {cr!r}")
        if cr.outputs is None:
            cr_logger.warning(f"No outputs for child run: {cr!r}")
            continue
        # Can't pass the strategy in the invocation metadata as its parallel.
        # So run tags populated by LC/LS is the only way to get it. `map:key:...` is
        # a kwarg key in RunnableParallel input dict.
        output_key: ScreeningStrategyType
        if isinstance(cr.tags, list):
            maybe_output_key = next(
                (
                    t.removeprefix("map:key:")
                    for t in cr.tags
                    if t.startswith("map:key:")
                ),
                None,
            )
            if maybe_output_key in ScreeningStrategyType:
                output_key = ScreeningStrategyType(maybe_output_key)
                cr_logger.debug(f"Output key for run: {cr.id!r} is {output_key}")
            else:
                cr_logger.error("Unknown output key for run")
                continue
        else:
            cr_logger.error(f"No tags for run: {cr.id!r}, tags: {cr.tags!r}")
            continue
        orig_resp_model = cr.outputs.get("output")
        if not isinstance(orig_resp_model, ScreeningResponse):
            # We simply return the output as is and let caller make it a ScreeningError
            cr_logger.error(f"Unknown response type: {orig_resp_model!r}")
            continue
        review_id = cr.metadata.get("review_id")
        if not review_id:
            cr_logger.error(f"Missing review_id in metadata: {cr.metadata!r}")
            continue
        review_id = uuid.UUID(review_id)
        pubmed_result_id = cr.metadata.get("pubmed_result_id")
        if not pubmed_result_id:
            cr_logger.error(f"Missing pubmed_result_id in metadata: {cr.metadata!r}")
            continue
        pubmed_result_id = uuid.UUID(pubmed_result_id)
        result_id = cr.id
        trace_id = cr.trace_id  # this is shared between invocations with same input
        inputs = cr.inputs
        start_time = cr.start_time
        end_time = cr.end_time
        if not end_time:
            cr_logger.warning("No end time for run: {cr!r}, setting to now")
            end_time = datetime.now(tz=timezone.utc)
        resp_metadata = {}  # FIXME: these don't work
        invocation_params = {}
        for ccr in cr.child_runs:
            # TODO: parse model_id from openai metadata
            if ccr.run_type == "chat_model":
                resp_metadata = ccr.extra.get("metadata", {})
                if not resp_metadata:
                    cr_logger.warning(
                        "No response metadata for chat_model child child run: {ccr!r}",
                        ccr=ccr,
                    )
                invocation_params = ccr.extra.get("invocation_params", {})
                if not invocation_params:
                    cr_logger.warning(
                        "No invocation_params for chat_model child child run:  {ccr!r}",
                        ccr=ccr,
                    )
                cr_logger.debug(f"chat_model child child run: {ccr!r}")
        model_name = resp_metadata.get(
            "ls_model_name", invocation_params.get("model_name", "not_found")
        )
        screening_result = ScreeningResult(
            id=result_id,
            trace_id=trace_id,  # this is shared between invocations with same input
            review_id=review_id,
            pubmed_result_id=pubmed_result_id,
            start_time=start_time,
            end_time=end_time,
            model_name=model_name,
            screening_strategy=output_key,
            response_metadata=dict(
                inputs=inputs,
                run_name=run_obj.name,
                **resp_metadata,
                **invocation_params,
            ),
            **orig_resp_model.model_dump(),
        )
        cr.metadata["screening_strategy"] = output_key

        strategy_tag = f"sra:screening_strategy:{output_key}"
        cr.tags.append(strategy_tag)
        if run_obj.tags and strategy_tag not in run_obj.tags:
            run_obj.tags.append(strategy_tag)

        if output_key not in run_obj.outputs:
            logger.warning(
                f"Missing output key: {output_key!r} in {run_obj.outputs!r}, assigning as new key ..."
            )
        run_obj.outputs[output_key] = screening_result


@logger.catch(onerror=lambda exc: st.error(exc) if ut.in_streamlit() else None)  # pyright: ignore [reportArgumentType]
def make_screen_abstracts_chain_input(
    pubmed_results_batch: list[models.PubMedResult],
    review: models.SystematicReview,
) -> ScreenAbstractsChainBatchInputDict:
    """Create input for a batch to be passed to abstracts screening chain.

    chain.batch(**input) input as returned from this function.

    TODO: We pass the same input and config to both reviewers, is it possible
          to bind configs to the sub chains such that metadata from the parallel
          chain doesn't overwrite anything?

          Currently reviewer/strategy must be looked up in the listner as it's
          populated by the chain in the RunTree.outputs keys and RunTree.tags.

    Args:
        pubmed_results_batch (list[models.PubMedResult]): list of pubmed results to be screened
        review (models.SystematicReview): systematic review associated with these pubmed results

    Returns:
        ScreenAbstractsChainBatchInputDict: dict of list of prompt inputs and list of RunnableConfigs.
            Can be passed directly to chain.batch(**this)
    """
    logger.info(f"Creating batch input for {len(pubmed_results_batch)} pubmed results")
    chain_inputs: list[
        ScreenAbstractsChainInputDict
    ] = []  # input is same regardless of strategy, same prompt variables
    configs: list[RunnableConfig] = []
    for i, pubmed_result in enumerate(pubmed_results_batch):
        configs.append(
            RunnableConfig(
                run_name="screen_abstracts_chain",
                metadata={
                    "review_id": str(review.id),
                    "pubmed_result_id": str(pubmed_result.id),
                },
                tags=[
                    "sra:prototype",
                    "sra:streamlit",
                    "sra:step3",
                    f"sra:review_id:{review.id}",
                    f"sra:pubmed_result_id:{pubmed_result.id}",
                    f"sra:screen_abstracts_chain:i:{i}",
                ],  # sra:screening_strategy:comprehensive|conservative # added by listener
            )
        )
        chain_inputs.append(
            ScreenAbstractsChainInputDict(
                **ScreenAbstractsChainInput(
                    background=review.background,
                    research_question=review.research_question,
                    inclusion_criteria=review.inclusion_criteria,
                    exclusion_criteria=review.exclusion_criteria,
                    title=pubmed_result.title,
                    journal=pubmed_result.journal,
                    year=pubmed_result.year,
                    abstract=pubmed_result.abstract,
                ).model_dump()
            )
        )
        logger.info(
            f"Created chain input for pubmed result {i}: config: {configs[-1]!r}, input: {chain_inputs[-1]!r}"
        )
    return ScreenAbstractsChainBatchInputDict(inputs=chain_inputs, config=configs)


# Prompts for screening

conservative_reviewer_prompt_text = """\
You are a highly conservative systematic reviewer, focusing on methodological \
rigor and strict interpretation of inclusion criteria. Your priority is to avoid \
including studies that might not fully meet the criteria.

When assessing abstracts:
- Require explicit statements matching criteria
- Flag any methodological ambiguity
- Consider unclear reporting as potential exclusion
- Demand high specificity in study characteristics
- Interpret missing information as a reason for uncertainty

Confidence Scoring for Conservative Review:
- Score < 0.7: Mark as "uncertain" when any required information is implicit or missing
- Score 0.7-0.85: Clear criteria match but some details could be more explicit
- Score > 0.85: Only when all criteria are explicitly and unambiguously met"""

comprehensive_reviewer_prompt_text = """\
You are a comprehensive systematic reviewer, focusing on potential relevance and \
broader interpretation of inclusion criteria. Your priority is to avoid excluding \
potentially relevant studies.

When assessing abstracts:
- Consider both explicit and implicit indicators
- Look for contextual clues about methodology
- Interpret typical field conventions
- Allow for variance in reporting styles
- Seek reasons to include when borderline

Confidence Scoring for Comprehensive Review:
- Score < 0.7: Mark as "uncertain" only when critical information is completely absent
- Score 0.7-0.85: Can infer required information from context
- Score > 0.85: Clear match with criteria, either explicit or strongly implied"""


task_prompt_text = """\
# Review protocol outputs

## Background to review:
{background}

## Research Question:
{research_question}

## Inclusion Criteria:
{inclusion_criteria}

## Exclusion Criteria:
{exclusion_criteria}

Please assess the following abstract for inclusion in the systematic review:

Your rationale must explicitly connect abstract content to specific criteria. \
For uncertain decisions, clearly state what additional information would be needed \
to make a confident decision.

# Study details:

## Title:
{title}

## Publishing Year:
{year}

## Journal:
{journal}

## Abstract:
{abstract}"""

conservative_reviewer_prompt = ChatPromptTemplate.from_messages(
    [("system", conservative_reviewer_prompt_text), ("human", task_prompt_text)]
)

comprehensive_reviewer_prompt = ChatPromptTemplate.from_messages(
    [("system", comprehensive_reviewer_prompt_text), ("human", task_prompt_text)]
)

# TODO: probably no need for two of these, can reuse one
llm1 = ChatOpenAI(model="gpt-4o", temperature=0)
llm2 = ChatOpenAI(model="gpt-4o", temperature=0)

# These return Pydantic models
llm1_with_structured_output = llm1.with_structured_output(schemas.ScreeningResponse)
llm2_with_structured_output = llm2.with_structured_output(schemas.ScreeningResponse)

screen_abstracts_chain = RunnableParallel(
    conservative=(
        conservative_reviewer_prompt | llm1_with_structured_output
    ).with_retry(
        stop_after_attempt=5,
        wait_exponential_jitter=True,
        retry_if_exception_type=(Exception,),
    ),
    comprehensive=(
        comprehensive_reviewer_prompt | llm2_with_structured_output
    ).with_retry(
        stop_after_attempt=5,
        wait_exponential_jitter=True,
        retry_if_exception_type=(Exception,),
    ),
).with_listeners(
    on_end=screen_abstracts_chain_on_end_cb,
    on_error=chain_on_error_listener_cb,
)  # .with_types(
#        output_type=ScreenAbstractsChainOutputDict # pyright: ignore [reportArgumentType]
# )

logger.info("chain: {!r}", screen_abstracts_chain)


class ScreenAbstractsBatchOutput(t.NamedTuple):
    """Output tuple of screen_abstracts_batch().

    Attributes:
        results (list[ScreenAbstractResultTuple]): list of screening results
        cb (OpenAICallbackHandler): callback handler

    Note:
        cb fields:
            cb.total_cost: float
            cb.total_tokens: int
            cb.prompt_tokens: int
            cb.prompt_tokens_cached: int
            cb.completion_tokens: int
            cb.reasoning_tokens: int
            cb.successful_requests: int

    """

    results: list[ScreenAbstractResultTuple]
    cb: OpenAICallbackHandler


@logger.catch(onerror=lambda exc: st.error(exc) if ut.in_streamlit() else None)  # pyright: ignore [reportArgumentType]
def screen_abstracts_batch(
    batch: list[models.PubMedResult], batch_idx: int, review: models.SystematicReview
) -> ScreenAbstractsBatchOutput | None:
    """Invoke screen_abstracts_chain on a batch of PubMed results.

    Results and errors are also written to ``st.session_state.screen_abstracts_results``
    and ``st.session_state.screen_abstracts_errors``.

    Caller should set ``st.session_state.screen_abstracts_batch_idx`` though it will
    be set if missing.

    Args:
        batch (list[PubMedResult]): list of pubmed results to be screened
        batch_idx (int): index of the batch
        review (SystematicReview): systematic review associated with this batch

    Returns:
        tuple[list[ScreenAbstractResultTuple], OpenAICallbackHandler]:
            list of screened pubmed results and OpenAI cb for the batch run.
            None if an uncaught exception occured (check the logs).
    """
    batch_logger = logger.bind(batch_idx=batch_idx)
    chain_inputs = make_screen_abstracts_chain_input(batch, review)
    chain_outputs: list[ScreenAbstractResultTuple] = []

    with get_openai_callback() as cb:
        res = st.session_state.screen_abstracts_chain.batch(**chain_inputs)
        if len(res) < len(batch):
            pad_size = len(batch) - len(res)
            res += [None] * pad_size
            batch_logger.warning(
                f"screen_abstracts_chain returned {len(res)} results, expected {len(batch)}, padding with None"
            )

        for i, parallel_invocation in enumerate(res):
            pubmed_result = batch[i]
            if isinstance(parallel_invocation, dict):
                conservative = parallel_invocation.get(
                    ScreeningStrategyType.CONSERVATIVE, parallel_invocation
                )
                comprehensive = parallel_invocation.get(
                    ScreeningStrategyType.COMPREHENSIVE, parallel_invocation
                )
            else:
                conservative = parallel_invocation
                comprehensive = parallel_invocation

            if not isinstance(conservative, ScreeningResult):
                conservative = ScreeningError(
                    search_result=pubmed_result,
                    error=conservative,
                )
                batch_logger.error(f"Conservative reviewer error: {conservative!r}")
            else:
                pubmed_result.conservative_result_id = conservative.id

            if not isinstance(comprehensive, ScreeningResult):
                comprehensive = ScreeningError(
                    search_result=pubmed_result,
                    error=comprehensive,
                )
                batch_logger.error(f"Comprehensive reviewer error: {comprehensive!r}")
            else:
                pubmed_result.comprehensive_result_id = comprehensive.id

            res_tuple = ScreenAbstractResultTuple(
                search_result=pubmed_result,
                conservative_result=conservative,
                comprehensive_result=comprehensive,
            )
            chain_outputs.append(res_tuple)

        return ScreenAbstractsBatchOutput(
            results=chain_outputs,
            cb=deepcopy(cb),
        )


# TODO: update
# @logger.catch(onerror=lambda exc: st.error(exc) if ut.in_streamlit() else None) # pyright: ignore [reportArgumentType]
# async def ascreen_abstracts_batch(batch: list[models.PubMedResult], batch_idx: int) -> ScreenAbstractsBatchOutput | None:
#    """Invoke screen_abstracts_chain on a batch of PubMed results.
#
#    Results and errors are also written to ``st.session_state.screen_abstracts_results``
#    and ``st.session_state.screen_abstracts_errors``.
#
#    Caller should set ``st.session_state.screen_abstracts_batch_idx`` though it will
#    be set if missing.
#
#    Args:
#        batch (list[models.PubMedResult]): list of pubmed results to be screened
#        batch_idx (int): index of the batch
#
#    Returns:
#        tuple[list[ScreenAbstractResultTuple], OpenAICallbackHandler]:
#            list of screened pubmed results and OpenAI cb for the batch run.
#            None if an uncaught exception occured (check the logs).
#    """
#    ut.init_state_key("screen_abstracts_batch_idx", batch_idx)
#    ut.init_state_key("screen_abstracts_results", [])
#    ut.init_state_key("screen_abstracts_errors", [])
#    ut.init_state_key("screen_abstracts_chain", screen_abstracts_chain)
#    #ut.init_state_key("screen_abstracts_total_tokens", 0)
#    #ut.init_state_key("screen_abstracts_successful_requests", 0)
#    #ut.init_state_key("screen_abstracts_total_cost", 0.0)
#
#    batch_logger = logger.bind(batch_idx=batch_idx)
#    chain_inputs = make_screen_abstracts_chain_input(batch)
#    chain_outputs: list[ScreenAbstractResultTuple] = []
#
#    with get_openai_callback() as cb:
#        res =  await st.session_state.screen_abstracts_chain.abatch(**chain_inputs)
#    if len(res) != len(batch):
#        pad_size = len(batch) - len(res)
#        res += [None] * pad_size
#        batch_logger.warning(f"screen_abstracts_chain returned {len(res)} results, expected {len(batch)}")
#    for i, parallel_invocation in enumerate(res):
#        if isinstance(parallel_invocation, dict):
#            conservative = parallel_invocation.get(ScreeningStrategyType.CONSERVATIVE, parallel_invocation)
#            comprehensive = parallel_invocation.get(ScreeningStrategyType.COMPREHENSIVE, parallel_invocation)
#        else:
#            conservative = parallel_invocation
#            comprehensive = parallel_invocation
#        if not isinstance(conservative, ScreeningResult):
#            conservative = ScreeningError(
#                search_result=batch[i],
#                error=conservative,
#            )
#            if ut.is_streamlit():
#                st.session_state.screen_abstracts_errors.append(conservative)
#            batch_logger.warning(f"Conservative reviewer error: {conservative!r}")
#        else:
#            if ut.is_streamlit():
#                st.session_state.screen_abstracts_results.append(conservative)
#
#        if not isinstance(comprehensive, ScreeningResult):
#            comprehensive = ScreeningError(
#                search_result=batch[i],
#                error=comprehensive,
#            )
#            if ut.is_streamlit():
#                st.session_state.screen_abstracts_errors.append(comprehensive)
#            batch_logger.warning(f"Comprehensive reviewer error: {comprehensive!r}")
#        else:
#            if ut.is_streamlit():
#                st.session_state.screen_abstracts_results.append(comprehensive)
#
#        res_tuple = ScreenAbstractResultTuple(
#            search_result=batch[i],
#            conservative_result=conservative,
#            comprehensive_result=comprehensive,
#        )
#        chain_outputs.append(res_tuple)
#    return ScreenAbstractsBatchOutput(
#        results=chain_outputs,
#        cb=cb,
#    )
