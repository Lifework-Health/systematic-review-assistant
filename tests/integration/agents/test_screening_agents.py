"""Integration tests for screening_agents.py."""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
import streamlit as st
from langchain_core.callbacks import CallbackManagerForChainRun
from langchain_core.outputs import RunInfo
from langchain_core.runnables import RunnableBinding, RunnableParallel

from sr_assistant.app.agents import screening_agents
from sr_assistant.app.agents.screening_agents import (
    chain_on_error_listener_cb,
    screen_abstracts_chain_on_end_cb,
)
from sr_assistant.core.models import PubMedResult, SystematicReview
from sr_assistant.core.schemas import ScreeningResponse, ScreeningResult
from sr_assistant.core.types import ScreeningDecisionType, ScreeningStrategyType


@pytest.fixture
def mock_pubmed_result() -> PubMedResult:
    """Create a mock PubMed result for testing."""
    return PubMedResult(
        pmid="12345",
        title="Test Study on Machine Learning",
        journal="Journal of Testing",
        year="2023",
        abstract="This is a test abstract about machine learning and its applications.",
        authors="Test Author",
        keywords=["machine learning", "testing"],
        mesh_terms=["Artificial Intelligence", "Software Testing"],
        publication_types=["Journal Article"],
    )


@pytest.fixture
def mock_systematic_review() -> SystematicReview:
    """Create a mock systematic review for testing."""
    return SystematicReview(
        title="Test Review",
        background="Testing background for systematic review",
        research_question="What are the effects of machine learning on testing?",
        inclusion_criteria="Studies must be about machine learning and testing",
        exclusion_criteria="Studies not in English, studies before 2000",
    )


@pytest.fixture
def mock_edge_case_pubmed_result() -> PubMedResult:
    """Create a mock PubMed result with missing fields to test edge cases."""
    return PubMedResult(
        pmid="54321",
        title="",
        journal="",
        year="",
        abstract="",
        authors="",
        keywords=[],
        mesh_terms=[],
        publication_types=[],
    )


@pytest.fixture
def mock_non_relevant_pubmed_result() -> PubMedResult:
    """Create a mock PubMed result that should be excluded."""
    return PubMedResult(
        pmid="98765",
        title="Impact of Diet on Heart Disease",
        journal="Journal of Cardiology",
        year="1995",  # Before 2000, should be excluded
        abstract="This study examines the relationship between diet and heart disease.",
        authors="Heart Researcher",
        keywords=["diet", "heart disease", "nutrition"],
        mesh_terms=["Diet", "Heart Diseases", "Nutrition"],
        publication_types=["Journal Article"],
    )


def test_screen_abstracts_chain(mock_pubmed_result, mock_systematic_review):
    """Test that screen_abstracts_chain correctly processes a single abstract."""
    # Prepare input for the chain
    chain_input = screening_agents.make_screen_abstracts_chain_input(
        [mock_pubmed_result], mock_systematic_review
    )

    # Run the chain with batch
    results = screening_agents.screen_abstracts_chain.batch(
        inputs=chain_input["inputs"],
        config=chain_input["config"],
    )
    assert len(results) == 1
    result = results[0]

    # Verify the output structure
    assert isinstance(result, dict)
    assert "conservative" in result
    assert "comprehensive" in result

    # Check conservative reviewer result
    assert isinstance(result["conservative"], ScreeningResult)
    assert hasattr(result["conservative"], "decision")
    assert hasattr(result["conservative"], "confidence_score")
    assert hasattr(result["conservative"], "rationale")
    assert 0 <= result["conservative"].confidence_score <= 1
    assert hasattr(result["conservative"], "id")
    assert hasattr(result["conservative"], "review_id")
    assert hasattr(result["conservative"], "pubmed_result_id")
    assert hasattr(result["conservative"], "trace_id")
    assert hasattr(result["conservative"], "model_name")
    assert hasattr(result["conservative"], "screening_strategy")
    assert hasattr(result["conservative"], "start_time")
    assert hasattr(result["conservative"], "end_time")
    assert hasattr(result["conservative"], "response_metadata")

    # Check comprehensive reviewer result
    assert isinstance(result["comprehensive"], ScreeningResult)
    assert hasattr(result["comprehensive"], "decision")
    assert hasattr(result["comprehensive"], "confidence_score")
    assert hasattr(result["comprehensive"], "rationale")
    assert 0 <= result["comprehensive"].confidence_score <= 1
    assert hasattr(result["comprehensive"], "id")
    assert hasattr(result["comprehensive"], "review_id")
    assert hasattr(result["comprehensive"], "pubmed_result_id")
    assert hasattr(result["comprehensive"], "trace_id")
    assert hasattr(result["comprehensive"], "model_name")
    assert hasattr(result["comprehensive"], "screening_strategy")
    assert hasattr(result["comprehensive"], "start_time")
    assert hasattr(result["comprehensive"], "end_time")
    assert hasattr(result["comprehensive"], "response_metadata")


def test_screen_abstracts_batch(
    mock_pubmed_result, mock_systematic_review, monkeypatch
):
    """Test that screen_abstracts_batch correctly processes a batch of abstracts."""

    # Mock Streamlit session state
    class MockSessionState:
        def __init__(self):
            self.screen_abstracts_chain = screening_agents.screen_abstracts_chain
            self.screen_abstracts_results = []
            self.screen_abstracts_errors = []
            self.screen_abstracts_batch_idx = 0

    monkeypatch.setattr(st, "session_state", MockSessionState())

    # Create a batch of 2 identical results for testing
    batch = [mock_pubmed_result, mock_pubmed_result]
    batch_idx = 0

    # Run the batch screening
    result = screening_agents.screen_abstracts_batch(
        batch, batch_idx, mock_systematic_review
    )

    # Verify the output
    assert result is not None
    results, cb = result

    # Check batch results
    assert len(results) == 2
    for res in results:
        # Verify result structure
        assert hasattr(res, "search_result")
        assert hasattr(res, "conservative_result")
        assert hasattr(res, "comprehensive_result")

        # Check search result
        assert isinstance(res.search_result, PubMedResult)
        assert res.search_result.pmid == mock_pubmed_result.pmid

        # Check conservative result
        assert isinstance(res.conservative_result, ScreeningResult)
        assert hasattr(res.conservative_result, "decision")
        assert hasattr(res.conservative_result, "confidence_score")
        assert hasattr(res.conservative_result, "rationale")
        assert 0 <= res.conservative_result.confidence_score <= 1
        assert hasattr(res.conservative_result, "id")
        assert hasattr(res.conservative_result, "review_id")
        assert hasattr(res.conservative_result, "pubmed_result_id")
        assert hasattr(res.conservative_result, "trace_id")
        assert hasattr(res.conservative_result, "model_name")
        assert hasattr(res.conservative_result, "screening_strategy")
        assert hasattr(res.conservative_result, "start_time")
        assert hasattr(res.conservative_result, "end_time")
        assert hasattr(res.conservative_result, "response_metadata")

        # Check comprehensive result
        assert isinstance(res.comprehensive_result, ScreeningResult)
        assert hasattr(res.comprehensive_result, "decision")
        assert hasattr(res.comprehensive_result, "confidence_score")
        assert hasattr(res.comprehensive_result, "rationale")
        assert 0 <= res.comprehensive_result.confidence_score <= 1
        assert hasattr(res.comprehensive_result, "id")
        assert hasattr(res.comprehensive_result, "review_id")
        assert hasattr(res.comprehensive_result, "pubmed_result_id")
        assert hasattr(res.comprehensive_result, "trace_id")
        assert hasattr(res.comprehensive_result, "model_name")
        assert hasattr(res.comprehensive_result, "screening_strategy")
        assert hasattr(res.comprehensive_result, "start_time")
        assert hasattr(res.comprehensive_result, "end_time")
        assert hasattr(res.comprehensive_result, "response_metadata")

    # Verify OpenAI callback handler
    assert hasattr(cb, "total_tokens")
    assert hasattr(cb, "total_cost")
    assert cb.total_tokens > 0


def test_chain_prompts():
    """Test that chain prompts are correctly configured."""
    # Test conservative reviewer prompt
    assert "conservative" in screening_agents.conservative_reviewer_prompt_text.lower()
    assert (
        "systematic reviewer"
        in screening_agents.conservative_reviewer_prompt_text.lower()
    )

    # Test comprehensive reviewer prompt
    assert (
        "comprehensive" in screening_agents.comprehensive_reviewer_prompt_text.lower()
    )
    assert (
        "systematic reviewer"
        in screening_agents.comprehensive_reviewer_prompt_text.lower()
    )

    # Test task prompt
    assert "research question" in screening_agents.task_prompt_text.lower()
    assert "inclusion criteria" in screening_agents.task_prompt_text.lower()
    assert "exclusion criteria" in screening_agents.task_prompt_text.lower()
    assert "abstract" in screening_agents.task_prompt_text.lower()


def test_chain_structure():
    """Test that the chain is correctly structured."""
    chain = screening_agents.screen_abstracts_chain

    # Verify the top-level object is a RunnableBinding (due to .with_listeners)
    assert isinstance(chain, RunnableBinding), (
        "Chain should be wrapped by RunnableBinding due to .with_listeners"
    )

    # Access the original RunnableParallel bound by the listeners
    bound_parallel_chain = chain.bound
    assert isinstance(bound_parallel_chain, RunnableParallel), (
        "The bound object should be the original RunnableParallel"
    )

    # Check that conservative and comprehensive steps exist in the parallel chain
    # Use steps__ as suggested by the AttributeError
    assert "conservative" in bound_parallel_chain.steps__
    assert "comprehensive" in bound_parallel_chain.steps__

    # Note: Directly verifying the attached listeners is difficult without relying on internals.
    # Checking the type and the bound steps confirms the basic structure.


def test_different_strategy_results(mock_pubmed_result, mock_systematic_review):
    """Test that conservative and comprehensive strategies produce different results."""
    # Prepare input for the chain
    chain_input = screening_agents.make_screen_abstracts_chain_input(
        [mock_pubmed_result], mock_systematic_review
    )

    # Run the chain with batch
    results = screening_agents.screen_abstracts_chain.batch(
        inputs=chain_input["inputs"],
        config=chain_input["config"],
    )
    assert len(results) == 1
    result = results[0]

    # Extract the decisions and confidence scores
    conservative_decision = result["conservative"].decision
    conservative_confidence = result["conservative"].confidence_score
    conservative_rationale = result["conservative"].rationale

    comprehensive_decision = result["comprehensive"].decision
    comprehensive_confidence = result["comprehensive"].confidence_score
    comprehensive_rationale = result["comprehensive"].rationale

    # Print the decisions for debugging
    print(
        f"Conservative decision: {conservative_decision}, confidence: {conservative_confidence}"
    )
    print(f"Conservative rationale: {conservative_rationale}")
    print(
        f"Comprehensive decision: {comprehensive_decision}, confidence: {comprehensive_confidence}"
    )
    print(f"Comprehensive rationale: {comprehensive_rationale}")

    # The results might be the same in some cases, but the rationales should differ
    # We can't assert they're always different due to model randomness
    # But we can check that they contain strategy-specific language

    # At minimum, the confidence and rationales should differ even if decisions are the same
    if conservative_decision == comprehensive_decision:
        # Check at least one of these conditions is true
        assert (
            abs(conservative_confidence - comprehensive_confidence) > 0.05
            or conservative_rationale != comprehensive_rationale
        )


def test_non_relevant_abstract(mock_non_relevant_pubmed_result, mock_systematic_review):
    """Test that a non-relevant abstract is correctly classified as exclude."""
    # Prepare input for the chain
    chain_input = screening_agents.make_screen_abstracts_chain_input(
        [mock_non_relevant_pubmed_result], mock_systematic_review
    )

    # Run the chain with batch
    results = screening_agents.screen_abstracts_chain.batch(
        inputs=chain_input["inputs"],
        config=chain_input["config"],
    )
    assert len(results) == 1
    result = results[0]

    # At least one of the strategies should exclude the paper
    # (due to year before 2000 in exclusion criteria)
    conservative_decision = result["conservative"].decision
    comprehensive_decision = result["comprehensive"].decision

    # Print decisions for debugging
    print(f"Conservative decision for non-relevant abstract: {conservative_decision}")
    print(f"Comprehensive decision for non-relevant abstract: {comprehensive_decision}")

    # At least one should be EXCLUDE or UNCERTAIN (not both INCLUDE)
    assert not (
        conservative_decision == ScreeningDecisionType.INCLUDE
        and comprehensive_decision == ScreeningDecisionType.INCLUDE
    )


def test_edge_case_handling(mock_edge_case_pubmed_result, mock_systematic_review):
    """Test that the chain handles edge cases with missing data."""
    # Prepare input for the chain
    chain_input = screening_agents.make_screen_abstracts_chain_input(
        [mock_edge_case_pubmed_result], mock_systematic_review
    )

    # Run the chain with batch
    results = screening_agents.screen_abstracts_chain.batch(
        inputs=chain_input["inputs"],
        config=chain_input["config"],
    )
    assert len(results) == 1
    result = results[0]

    # The chain should complete without errors even with empty data
    assert "conservative" in result
    assert "comprehensive" in result

    # Results should reflect uncertainty due to missing data
    conservative_result = result["conservative"]
    comprehensive_result = result["comprehensive"]

    print(f"Conservative decision for edge case: {conservative_result.decision}")
    print(f"Comprehensive decision for edge case: {comprehensive_result.decision}")

    # With minimal information, decisions should be UNCERTAIN or EXCLUDE, not INCLUDE
    # Conservative reviewers should never include with such limited data
    assert conservative_result.decision != ScreeningDecisionType.INCLUDE

    # Comprehensive might include in some cases, but should have low confidence if it does
    if comprehensive_result.decision == ScreeningDecisionType.INCLUDE:
        assert comprehensive_result.confidence_score < 0.8


@patch("streamlit.session_state", MagicMock())
@patch("sr_assistant.app.agents.screening_agents.logger")
@patch("sr_assistant.app.agents.screening_agents.ScreeningResult")
def test_chain_on_end_callback_integration(
    MockScreeningResult, mock_logger, mock_pubmed_result, mock_systematic_review
):
    """Test the on_end callback correctly processes run outputs and metadata."""
    # --- Setup Mocks ---
    run_id = str(uuid.uuid4())
    review_id = str(uuid.uuid4())
    pubmed_result_id = str(mock_pubmed_result.id or uuid.uuid4())

    # Create mock raw responses (as if generated by the parallel chain branches)
    conservative_mock_response = ScreeningResponse(
        decision=ScreeningDecisionType.INCLUDE,
        confidence_score=0.85,
        rationale="Rationale for conservative",
    )
    comprehensive_mock_response = ScreeningResponse(
        decision=ScreeningDecisionType.UNCERTAIN,
        confidence_score=0.65,
        rationale="Rationale for comprehensive",
    )

    # Mock the parent Run object - state BEFORE on_end callback runs
    mock_run = MagicMock(spec=RunInfo)
    mock_run.id = run_id
    mock_run.name = "chain_run"
    mock_run.tags = []
    # Initialize outputs with the *raw* responses from the parallel branches
    mock_run.outputs = {
        "conservative": conservative_mock_response,
        "comprehensive": comprehensive_mock_response,
    }

    # Mock child runs (primarily needed for metadata and tags)
    mock_child_runs = []
    strategies_map = {
        ScreeningStrategyType.CONSERVATIVE: conservative_mock_response,
        ScreeningStrategyType.COMPREHENSIVE: comprehensive_mock_response,
    }

    for strategy, raw_response in strategies_map.items():
        mock_child_run = MagicMock()
        mock_child_run.id = str(uuid.uuid4())
        mock_child_run.name = f"{strategy.value}_child_run"
        # Tag is crucial for the callback to link child metadata to parent output key
        mock_child_run.tags = [f"map:key:{strategy.value}"]
        mock_child_run.metadata = {
            "review_id": review_id,
            "pubmed_result_id": pubmed_result_id,
        }
        mock_child_run.trace_id = str(uuid.uuid4())
        mock_child_run.start_time = datetime.now(timezone.utc)
        mock_child_run.end_time = datetime.now(timezone.utc)
        mock_child_run.inputs = {"input_data": f"input_{strategy.value}"}

        # Child run outputs are *not* directly used to create ScreeningResult,
        # but we can set them for completeness if needed for other logic.
        # The callback primarily uses the parent `run_obj.outputs` keyed by strategy.
        # We set it here anyway to be safe.
        mock_child_run.outputs = {"output": raw_response}

        # Mock the nested grandchild run (chat model) to get model name
        mock_grandchild_run = MagicMock()
        mock_grandchild_run.run_type = "chat_model"
        mock_grandchild_run.extra = {
            "metadata": {"ls_model_name": "mock_llm_model"},
            "invocation_params": {"model_name": "mock_invocation_model_name"},
        }
        mock_grandchild_run.inputs = {"messages": []}
        mock_grandchild_run.outputs = {"generations": []}

        mock_child_run.child_runs = [mock_grandchild_run]
        mock_child_runs.append(mock_child_run)

    mock_run.child_runs = mock_child_runs
    # --- End mock setup ---

    # Create mock instances that will be returned by the patched ScreeningResult constructor
    mock_conservative_result_instance = MagicMock(spec=ScreeningResult)
    mock_comprehensive_result_instance = MagicMock(spec=ScreeningResult)

    # Configure the side_effect to return different mocks based on strategy
    def screening_result_side_effect(*args, **kwargs):
        if kwargs.get("screening_strategy") == ScreeningStrategyType.CONSERVATIVE:
            return mock_conservative_result_instance
        if kwargs.get("screening_strategy") == ScreeningStrategyType.COMPREHENSIVE:
            return mock_comprehensive_result_instance
        return MagicMock(spec=ScreeningResult)

    MockScreeningResult.side_effect = screening_result_side_effect

    # Call the on_end callback
    screen_abstracts_chain_on_end_cb(mock_run)

    # Assertions: Check ScreeningResult constructor was CALLED correctly
    assert MockScreeningResult.call_count == 2

    calls = MockScreeningResult.call_args_list

    # Check Conservative call args
    conservative_call = next(
        (
            c
            for c in calls
            if c.kwargs.get("screening_strategy") == ScreeningStrategyType.CONSERVATIVE
        ),
        None,
    )
    assert conservative_call is not None, (
        "ScreeningResult call for CONSERVATIVE strategy not found"
    )
    conservative_kwargs = conservative_call.kwargs
    assert conservative_kwargs["model_name"] == "mock_llm_model"
    assert conservative_kwargs["review_id"] == uuid.UUID(review_id)
    assert conservative_kwargs["pubmed_result_id"] == uuid.UUID(pubmed_result_id)
    assert conservative_kwargs["decision"] == conservative_mock_response.decision
    assert (
        conservative_kwargs["confidence_score"]
        == conservative_mock_response.confidence_score
    )
    assert conservative_kwargs["rationale"] == conservative_mock_response.rationale
    assert "response_metadata" in conservative_kwargs
    assert conservative_kwargs["response_metadata"].get("inputs") == {
        "input_data": "input_conservative"
    }
    assert (
        conservative_kwargs["response_metadata"].get("ls_model_name")
        == "mock_llm_model"
    )

    # Check Comprehensive call args
    comprehensive_call = next(
        (
            c
            for c in calls
            if c.kwargs.get("screening_strategy") == ScreeningStrategyType.COMPREHENSIVE
        ),
        None,
    )
    assert comprehensive_call is not None, (
        "ScreeningResult call for COMPREHENSIVE strategy not found"
    )
    comprehensive_kwargs = comprehensive_call.kwargs
    assert comprehensive_kwargs["model_name"] == "mock_llm_model"
    assert comprehensive_kwargs["review_id"] == uuid.UUID(review_id)
    assert comprehensive_kwargs["pubmed_result_id"] == uuid.UUID(pubmed_result_id)
    assert comprehensive_kwargs["decision"] == comprehensive_mock_response.decision
    assert (
        comprehensive_kwargs["confidence_score"]
        == comprehensive_mock_response.confidence_score
    )
    assert comprehensive_kwargs["rationale"] == comprehensive_mock_response.rationale
    assert "response_metadata" in comprehensive_kwargs
    assert comprehensive_kwargs["response_metadata"].get("inputs") == {
        "input_data": "input_comprehensive"
    }

    # Verify that the parent mock_run.outputs was updated IN PLACE by the callback
    # with the objects returned by the patched constructor
    assert mock_run.outputs["conservative"] is mock_conservative_result_instance
    assert mock_run.outputs["comprehensive"] is mock_comprehensive_result_instance

    # Check logger calls still happened
    mock_logger.bind.assert_called()
    bound_logger_mock = mock_logger.bind.return_value
    assert bound_logger_mock.debug.call_count >= 2


@patch("streamlit.session_state", MagicMock())
@patch("sr_assistant.app.agents.screening_agents.logger")
def test_chain_on_error_callback_integration(mock_logger):
    """Test the on_error callback integration."""
    # --- Setup mock Run object similar to unit tests ---
    run_id = str(uuid.uuid4())
    mock_run = MagicMock(spec=RunInfo)
    mock_run.id = run_id
    mock_run.name = "error_run"
    mock_run.tags = []
    mock_run.inputs = {"input_data": "test"}
    mock_run.child_runs = []  # Initialize to avoid potential AttributeError later
    error = ValueError("Simulated LLM error")
    # Mock callback manager for context if needed by the callback
    mock_run_manager = MagicMock(spec=CallbackManagerForChainRun)

    # Call the on_error callback directly
    chain_on_error_listener_cb(error, run=mock_run, run_manager=mock_run_manager)

    # 1. Assert that logger.bind was called (to create cb_logger)
    mock_logger.bind.assert_called_once()

    # 2. Get the mock object that logger.bind returned (this is cb_logger)
    bound_logger_mock = mock_logger.bind.return_value

    # 3. Assert that .exception was called on this bound mock
    bound_logger_mock.exception.assert_called_once()

    # Optional: Verify the arguments passed to the exception call on the bound logger
    call_args, call_kwargs = bound_logger_mock.exception.call_args
    assert "Error during chain execution" in call_args[0]
    assert f"run_id={run_id}" in call_args[0]  # Check run_id extraction worked
    assert f"error={error!r}" in call_args[0]
    assert call_kwargs.get("error") == error
    assert "kwargs" in call_kwargs  # Check that kwargs were passed for logging

    # Also check if the subsequent .error call was made on the bound logger
    # depending on whether the mock run object has child_runs
    if mock_run.child_runs:
        assert (
            bound_logger_mock.error.called
        )  # Check if the error logging for child runs happened
    else:
        bound_logger_mock.error.assert_not_called()
