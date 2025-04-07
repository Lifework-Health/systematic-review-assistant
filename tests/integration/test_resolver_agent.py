"""Integration tests for the screening conflict resolver feature."""

import os

import pytest
from dotenv import load_dotenv
from sqlmodel import Session, create_engine

from sr_assistant.app.agents.screening_agents import resolve_screening_conflict
from sr_assistant.core.models import (
    PubMedResult,
    ScreeningResolution,
)
from sr_assistant.core.repositories import (
    PubMedResultRepository,
    ScreenAbstractResultRepository,
    ScreeningResolutionRepository,
    SystematicReviewRepository,
)
from sr_assistant.core.types import ScreeningDecisionType

# Use a separate test database
load_dotenv(".env.test", override=True)
DATABASE_URL = os.getenv("SRA_DATABASE_URL", os.getenv("DATABASE_URL", ""))
if not DATABASE_URL or "sra_integration_test" not in DATABASE_URL:
    pytest.skip(
        "Skipping resolver integration tests: DATABASE_URL for testing not set or invalid.",
        allow_module_level=True,
    )


# Fixture for the database engine
@pytest.fixture(scope="module")
def engine():
    # Create a new engine for the test module
    test_engine = create_engine(
        DATABASE_URL, echo=False
    )  # Set echo=True for debugging SQL
    # Ensure tables are created (assuming test_models_and_gen_data handled cleanup/creation)
    # SQLModel.metadata.create_all(test_engine)
    return test_engine
    # Optional: Cleanup after tests if needed, though test_models_and_gen_data might handle it
    # SQLModel.metadata.drop_all(test_engine)


# Fixture for repositories
@pytest.fixture(scope="function")  # Use function scope for isolation
def repositories(engine):
    from sqlmodel import sessionmaker

    test_session_factory = sessionmaker(
        autocommit=False, autoflush=False, bind=engine, class_=Session
    )
    return {
        "review": SystematicReviewRepository(session_factory=test_session_factory),
        "pubmed": PubMedResultRepository(session_factory=test_session_factory),
        "screening": ScreenAbstractResultRepository(
            session_factory=test_session_factory
        ),
        "resolution": ScreeningResolutionRepository(
            session_factory=test_session_factory
        ),
    }


# Fixture to find a conflicting PubMedResult from the test data
@pytest.fixture(scope="function")
def conflicting_pubmed_result(repositories):
    pubmed_repo = repositories["pubmed"]
    review_repo = repositories["review"]
    reviews = review_repo.get_all(limit=1)
    if not reviews:
        pytest.fail("No systematic reviews found in test data.")
    review_id = reviews[0].id

    pubmed_results = pubmed_repo.get_by_review_id(review_id)
    if not pubmed_results:
        pytest.fail(f"No PubMed results found for review {review_id} in test data.")

    conflict = None
    for pm_res in pubmed_results:
        # Reload with screening results
        pm_res_full = pubmed_repo.get_with_screening_results(pm_res.id)
        if (
            pm_res_full
            and pm_res_full.conservative_result
            and pm_res_full.comprehensive_result
            and pm_res_full.conservative_result.decision
            != pm_res_full.comprehensive_result.decision
            # Only handle INCLUDE vs EXCLUDE conflicts as per PRD v1
            and {
                pm_res_full.conservative_result.decision,
                pm_res_full.comprehensive_result.decision,
            }
            == {ScreeningDecisionType.INCLUDE, ScreeningDecisionType.EXCLUDE}
        ):
            conflict = pm_res_full
            break

    if not conflict:
        pytest.fail(
            "No conflicting PubMed results (INCLUDE vs EXCLUDE) found in test data."
        )

    # Ensure relationships are loaded for the test function
    # (Might be redundant if get_with_screening_results loads them eagerly)
    assert conflict.conservative_result is not None
    assert conflict.comprehensive_result is not None
    assert conflict.review is not None
    return conflict


# --- Integration Test --- #


@pytest.mark.integration
def test_resolve_screening_conflict_integration(
    conflicting_pubmed_result: PubMedResult,
    repositories,
):
    """Test the full resolve_screening_conflict flow, including DB interaction."""
    pubmed_repo = repositories["pubmed"]
    resolution_repo = repositories["resolution"]

    # Ensure initial state: no resolution exists
    assert conflicting_pubmed_result.resolution_id is None
    assert conflicting_pubmed_result.final_decision is None
    existing_resolution = resolution_repo.get_by_pubmed_id(conflicting_pubmed_result.id)
    assert existing_resolution is None

    # --- Act --- #
    try:
        # Use the actual agent function
        resolution_model = resolve_screening_conflict(
            pubmed_result=conflicting_pubmed_result,
            review=conflicting_pubmed_result.review,  # Access loaded review
            conservative_result=conflicting_pubmed_result.conservative_result,
            comprehensive_result=conflicting_pubmed_result.comprehensive_result,
        )
    except Exception as e:
        pytest.fail(f"resolve_screening_conflict raised an exception: {e}")

    # --- Assert: Check the returned model --- #
    assert isinstance(resolution_model, ScreeningResolution)
    assert resolution_model.id is not None
    assert resolution_model.pubmed_result_id == conflicting_pubmed_result.id
    assert resolution_model.review_id == conflicting_pubmed_result.review_id
    assert (
        resolution_model.conservative_result_id
        == conflicting_pubmed_result.conservative_result_id
    )
    assert (
        resolution_model.comprehensive_result_id
        == conflicting_pubmed_result.comprehensive_result_id
    )
    assert resolution_model.resolver_decision in ScreeningDecisionType
    assert isinstance(resolution_model.resolver_reasoning, str)
    assert resolution_model.resolver_reasoning != ""
    assert 0.0 <= resolution_model.resolver_confidence_score <= 1.0
    assert (
        resolution_model.resolver_model_name is not None
    )  # Should be populated by the function

    # --- Assert: Check database state after resolution --- #

    # 1. Check if ScreeningResolution was saved
    saved_resolution = resolution_repo.get_by_id(resolution_model.id)
    assert saved_resolution is not None
    assert saved_resolution.id == resolution_model.id
    assert saved_resolution.pubmed_result_id == conflicting_pubmed_result.id
    assert saved_resolution.resolver_decision == resolution_model.resolver_decision
    assert saved_resolution.resolver_reasoning == resolution_model.resolver_reasoning
    assert (
        saved_resolution.resolver_confidence_score
        == resolution_model.resolver_confidence_score
    )

    # 2. Check if PubMedResult was updated
    updated_pubmed_result = pubmed_repo.get_by_id(conflicting_pubmed_result.id)
    assert updated_pubmed_result is not None
    assert updated_pubmed_result.resolution_id == saved_resolution.id
    assert updated_pubmed_result.final_decision == saved_resolution.resolver_decision
