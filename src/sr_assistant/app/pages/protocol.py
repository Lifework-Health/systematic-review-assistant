from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import cast

import streamlit as st
from dotenv import find_dotenv, load_dotenv
from langchain_core.runnables import RunnableConfig
from loguru import logger
from sqlmodel import select
from streamlit.delta_generator import DeltaGenerator

from sr_assistant.core.models import CriteriaFramework, SystematicReview
from sr_assistant.core.schemas import PicosSuggestions, SuggestionResult
from sr_assistant.step1.suggestion_agent import SuggestionAgent

load_dotenv(find_dotenv(), override=True)


def init_agent_config() -> RunnableConfig:
    if "agent_config" in st.session_state:
        return cast(RunnableConfig, st.session_state.agent_config)

    config = RunnableConfig(
        recursion_limit=1000, configurable={"thread_id": str(uuid.uuid4())}
    )
    st.session_state.agent_config = config
    return config


def init_suggestion_agent() -> SuggestionAgent:
    """Initialize the suggestion agent."""
    return SuggestionAgent(model="gpt-4o", temperature=0.0)


@logger.catch(Exception, message="Error building review model from PICO")
def build_review_model_from_pico(response_widget: DeltaGenerator) -> SystematicReview:
    """Builds the SystematicReview model using PICO fields."""
    # --- Combine PICO into structured criteria (example) ---
    # This is a simple approach; might need refinement based on how
    # screening agents expect criteria.
    inclusion_criteria_parts = []
    # exclusion_criteria_parts = [] # Removed unused variable

    if st.session_state.pico_population:
        inclusion_criteria_parts.append(
            f"Population: {st.session_state.pico_population}"
        )
    if st.session_state.pico_intervention:
        inclusion_criteria_parts.append(
            f"Intervention: {st.session_state.pico_intervention}"
        )
    if st.session_state.pico_comparison:
        inclusion_criteria_parts.append(
            f"Comparison: {st.session_state.pico_comparison}"
        )
    if st.session_state.pico_outcome:
        inclusion_criteria_parts.append(f"Outcome: {st.session_state.pico_outcome}")

    # Construct simple inclusion/exclusion strings for now
    # TODO: Revisit how to best store/represent this for downstream use
    inclusion_criteria = (
        "; ".join(inclusion_criteria_parts)
        if inclusion_criteria_parts
        else "Not specified"
    )
    # Use the separately entered exclusion criteria
    # Get the value, treat empty string like None for defaulting
    exclusion_criteria_value = st.session_state.get("exclusion_criteria")
    exclusion_criteria = (
        exclusion_criteria_value if exclusion_criteria_value else "Not specified"
    )

    logger.info(
        f"Building review model with PICO derived criteria: Incl={inclusion_criteria}, Excl={exclusion_criteria}"
    )

    review = SystematicReview(
        id=st.session_state.review_id,
        background=st.session_state.background,
        research_question=st.session_state.research_question,
        inclusion_criteria=inclusion_criteria,  # Use combined PICO string
        exclusion_criteria=exclusion_criteria,  # Use the potentially defaulted value
        # Store raw PICO components in the framework field for structured data
        criteria_framework=CriteriaFramework.PICO,  # Use the enum member
        criteria_framework_answers={
            "population": st.session_state.pico_population,
            "intervention": st.session_state.pico_intervention,
            "comparison": st.session_state.pico_comparison,
            "outcome": st.session_state.pico_outcome,
        },
    )
    response_widget.success("SystematicReview model built from PICO successfully")
    return review


def persist_review(model: SystematicReview) -> SystematicReview:
    """Persists the SystematicReview model, updating PICO fields."""
    with st.session_state.session_factory() as session:
        # Check if record exists in DB
        stmt = select(SystematicReview).where(SystematicReview.id == model.id)
        db_model = session.exec(stmt).first()

        if db_model:
            # Update existing record
            logger.debug(f"Updating existing review {model.id}")
            db_model.background = model.background
            db_model.research_question = model.research_question
            # Update derived criteria fields
            db_model.inclusion_criteria = model.inclusion_criteria
            db_model.exclusion_criteria = model.exclusion_criteria
            # Update structured PICO fields
            db_model.criteria_framework = model.criteria_framework
            db_model.criteria_framework_answers = model.criteria_framework_answers
            db_model.updated_at = datetime.now(timezone.utc)  # Add update timestamp
            persisted_model = db_model
        else:
            # Add as new record
            logger.debug(f"Adding new review {model.id}")
            session.add(model)
            persisted_model = model

        session.commit()
        session.refresh(persisted_model)
        logger.info(f"Persisted review {persisted_model.id}")
        return persisted_model


if "review_status" not in st.session_state:
    st.session_state["review_status"] = "draft"

# Set up page
st.title("Define Research Question & Criteria")
st.write("Review status: ", st.session_state.review_status)

# Initialize session state variables
# HACK: This should come from the Review model, but because of streamlit and needing to
# keep this constant, we've to initialize the reviews_id here. It's like a session ID.
if "review_id" not in st.session_state:
    st.session_state["review_id"] = uuid.uuid4()
# Inject review_id to shared logger extra, is log_records table it's a fk to systematic_reviews.id
# and this way all logs for a review are easy to query and show/export.
if "logger_extra_configured" not in st.session_state:
    logger.configure(extra={"review_id": st.session_state.review_id})
    st.session_state.logger_extra_configured = True

# Initialize session state variables for PICO if they don't exist
if "pico_population" not in st.session_state:
    st.session_state["pico_population"] = ""
if "pico_intervention" not in st.session_state:
    st.session_state["pico_intervention"] = ""
if "pico_comparison" not in st.session_state:
    st.session_state["pico_comparison"] = ""
if "pico_outcome" not in st.session_state:
    st.session_state["pico_outcome"] = ""
# Keep existing ones
if "background" not in st.session_state:
    st.session_state["background"] = ""
if "research_question" not in st.session_state:
    st.session_state["research_question"] = ""
# Initialize exclusion criteria if not present
if "exclusion_criteria" not in st.session_state:
    st.session_state["exclusion_criteria"] = ""

# Remove old criteria initialization if present (optional, depends on cleanup needs)
# if "inclusion_criteria" in st.session_state: del st.session_state["inclusion_criteria"]

if "llm_suggestions" not in st.session_state:
    st.session_state["llm_suggestions"] = ""
if "suggestions_agent" not in st.session_state:
    st.session_state["suggestions_agent"] = init_suggestion_agent()

# Layout for input fields and LLM feedback
col1, col2 = st.columns(2)

with col1:
    notification_widget = st.empty()
    review_model_widget = st.empty()
    # st.write("TODO: PICO(T/S), FINER, chat, ...") # Removed TODO
    st.subheader("Define Your Protocol")
    st.session_state.background = st.text_area(
        label="Brief introduction/Background",
        value=st.session_state.background,
        height=150,
        help="Provide context for the review, why it's needed, and the overall aim.",
    )
    st.session_state.research_question = st.text_area(
        label="Research Question",
        value=st.session_state.research_question,
        height=100,
        placeholder="E.g. 'Does intervention X improve outcome Y in population Z?'",
        help="The central question the systematic review aims to answer.",
    )

    st.divider()
    st.subheader("PICO Criteria")
    # Replace old criteria text areas with PICO fields
    st.session_state.pico_population = st.text_area(
        "**P**opulation / Problem",
        value=st.session_state.pico_population,
        height=75,
        placeholder="E.g., Adults > 18 with type 2 diabetes",
        help="Describe the patient population or problem being addressed.",
    )
    st.session_state.pico_intervention = st.text_area(
        "**I**ntervention / Exposure",
        value=st.session_state.pico_intervention,
        height=75,
        placeholder="E.g., Metformin 1000mg daily",
        help="Describe the intervention, treatment, or exposure of interest.",
    )
    st.session_state.pico_comparison = st.text_area(
        "**C**omparison / Control",
        value=st.session_state.pico_comparison,
        height=75,
        placeholder="E.g., Placebo or standard care",
        help="Describe the alternative or control group being compared to the intervention.",
    )
    st.session_state.pico_outcome = st.text_area(
        "**O**utcome",
        value=st.session_state.pico_outcome,
        height=75,
        placeholder="E.g., Reduction in HbA1c levels",
        help="Describe the primary outcome(s) being measured.",
    )

    st.divider()
    # Keep exclusion criteria separate for now as PICO doesn't define them
    st.session_state.exclusion_criteria = st.text_area(
        label="Explicit Exclusion Criteria (Optional)",
        value=st.session_state.get("exclusion_criteria", ""),  # Use get for safety
        placeholder="E.g., Non-human studies, Case reports, Studies not in English",
        height=100,
        help="Specific criteria used to exclude studies (complementary to PICO).",
    )

    validate_button = st.button("Validate & Suggest Improvements")

with col2:
    st.subheader("LLM Suggestions")
    suggestions_spinner = st.empty()
    if st.session_state["llm_suggestions"]:
        st.markdown(st.session_state["llm_suggestions"])
    else:
        st.write("No suggestions yet. Click the 'Validate' button to get feedback.")

# LLM Interaction
if validate_button:
    with suggestions_spinner.container():
        st.info("Generating suggestions...")
        # Build a temporary model just to pass to the agent (doesn't need PICO yet)
        temp_review_data = SystematicReview(
            id=st.session_state.review_id,  # Use current ID
            background=st.session_state.get(
                "background", ""
            ),  # Default to empty string
            research_question=st.session_state.get(
                "research_question", ""
            ),  # Default to empty string
            # Pass empty/placeholder for criteria as agent uses background/question
            inclusion_criteria="",
            exclusion_criteria="",
        )
        with st.spinner("Analyzing protocol and suggesting PICO..."):
            suggestion_result: SuggestionResult = st.session_state[
                "suggestions_agent"
            ].get_suggestions(temp_review_data)

            pico_suggestions: PicosSuggestions | None = suggestion_result.get("pico")
            general_suggestions: str = suggestion_result.get(
                "raw_response", "No suggestions provided."
            )  # Display critique

            if pico_suggestions:
                # Update session state only if the field is currently empty
                if not st.session_state.pico_population and pico_suggestions.population:
                    st.session_state.pico_population = pico_suggestions.population
                    logger.info("Prefilled PICO Population.")
                if (
                    not st.session_state.pico_intervention
                    and pico_suggestions.intervention
                ):
                    st.session_state.pico_intervention = pico_suggestions.intervention
                    logger.info("Prefilled PICO Intervention.")
                if not st.session_state.pico_comparison and pico_suggestions.comparison:
                    st.session_state.pico_comparison = pico_suggestions.comparison
                    logger.info("Prefilled PICO Comparison.")
                if not st.session_state.pico_outcome and pico_suggestions.outcome:
                    st.session_state.pico_outcome = pico_suggestions.outcome
                    logger.info("Prefilled PICO Outcome.")

            # Store the general critique for display
            st.session_state["llm_suggestions"] = general_suggestions

            # Rerun to show updated fields and suggestions text
            st.rerun()

st.subheader("Save Protocol")
st.write(
    "Once you are happy with the question and criteria, click the 'Save Protocol' button."
)


if st.button("Save Protocol"):
    # Add validation for PICO fields if desired
    if not st.session_state.research_question:
        notification_widget.warning("Please define a research question")
        st.stop()
    # Example: Make Population mandatory
    elif not st.session_state.pico_population:
        notification_widget.warning("Please define the Population/Problem (PICO)")
        st.stop()
    else:
        # Use the new build function
        review = build_review_model_from_pico(review_model_widget)
        if not review:
            st.session_state.review_status = "validation error"
            st.rerun()
        st.session_state.review = review
        st.session_state.review_status = f"saved at {datetime.now(tz=timezone.utc)}"

        with st.status("Saving protocol to database ...", expanded=True):
            try:
                review = persist_review(review)
                st.session_state.review = (
                    review  # Ensure session state has the latest persisted version
                )
                st.write(
                    "Saved protocol to database, review status: ",
                    st.session_state.review_status,
                )
                st.json(review.model_dump(mode="json"))
                st.page_link(
                    "pages/search.py",
                    label="Next: PubMed Search",
                    icon=":material/search:",
                )
            except Exception as e:
                logger.exception("Failed to persist review to database.")
                st.error(f"Failed to save protocol: {e}")

# Remove old build_review_model function if no longer needed
# def build_review_model(response_widget: DeltaGenerator) -> SystematicReview:
#     review = SystematicReview(
#         id=st.session_state.review_id,
#         background=st.session_state.background,
#         research_question=st.session_state.research_question,
#         inclusion_criteria=st.session_state.inclusion_criteria,
#         exclusion_criteria=st.session_state.exclusion_criteria,
#     )
#     response_widget.success("SystematicReview model built successfully")
#     return review
