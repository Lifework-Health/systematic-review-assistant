"""Integration tests for resolver functionality and database interactions."""

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy import select
from sqlmodel import Session, select

# Assuming models are adjusted for resolver (ScreeningResolution, fields in PubMedResult)
# These imports might need adjustment based on the final model locations/definitions
from sr_assistant.core.models import (
    PubMedResult,
    ScreenAbstractResult,
    ScreeningResolution,
    SystematicReview,
)
from sr_assistant.core.types import (
    CriteriaFramework,
    ScreeningDecisionType,
    ScreeningStrategyType,
)


@pytest.fixture(scope="function")
def seed_data(db_session: Session):
    """Seeds the database with a review, a pubmed result, and conflicting screenings."""
    # Initialize without id, use correct framework fields
    review = SystematicReview(
        research_question="Test RQ for Resolver",
        criteria_framework=CriteriaFramework.PICO,
        criteria_framework_answers={
            "population": "Patients with condition X",
            "intervention": "Treatment Y",
            "comparison": "Placebo or standard care",
            "outcome": "Improvement in metric Z",
        },
        inclusion_criteria="",
        exclusion_criteria="Exclude comorbidities A, B",
    )
    db_session.add(review)
    db_session.commit()
    db_session.refresh(review)

    # Initialize with id=None for linter
    pubmed_res = PubMedResult(
        id=None,
        review_id=review.id,
        query="Test query",
        pmid="RESOLVER_TEST_1",
        title="Resolver Test Article",
        abstract="Abstract for resolver test.",
        journal="Test Journal",
        year="2023",
    )
    db_session.add(pubmed_res)
    db_session.commit()
    db_session.refresh(pubmed_res)

    trace_id = uuid.uuid4()
    conservative_res = ScreenAbstractResult(
        id=uuid.uuid4(),
        review_id=review.id,
        pubmed_result_id=pubmed_res.id,
        trace_id=trace_id,
        decision=ScreeningDecisionType.INCLUDE,
        confidence_score=0.9,
        rationale="Conservative included.",
        screening_strategy=ScreeningStrategyType.CONSERVATIVE,
        model_name="test-cons-model",
        start_time=datetime.now(UTC),
        end_time=datetime.now(UTC),
        response_metadata={"test": "cons"},
        exclusion_reason_categories={},
    )
    comprehensive_res = ScreenAbstractResult(
        id=uuid.uuid4(),
        review_id=review.id,
        pubmed_result_id=pubmed_res.id,
        trace_id=trace_id,
        decision=ScreeningDecisionType.EXCLUDE,
        confidence_score=0.9,
        rationale="Comprehensive excluded.",
        extracted_quotes=["Excluded because..."],
        exclusion_reason_categories={"study_design_exclusion_reasons": ["NOT_RCT"]},
        screening_strategy=ScreeningStrategyType.COMPREHENSIVE,
        model_name="test-comp-model",
        start_time=datetime.now(UTC),
        end_time=datetime.now(UTC),
        response_metadata={"test": "comp"},
    )
    db_session.add_all([conservative_res, comprehensive_res])
    db_session.commit()
    db_session.refresh(conservative_res)
    db_session.refresh(comprehensive_res)

    # Update PubMedResult with screening IDs
    pubmed_res.conservative_result_id = conservative_res.id
    pubmed_res.comprehensive_result_id = comprehensive_res.id
    db_session.add(pubmed_res)
    db_session.commit()
    db_session.refresh(pubmed_res)

    # Yield relevant IDs or objects needed by tests
    return {
        "review_id": review.id,
        "pubmed_result_id": pubmed_res.id,
        "conservative_result_id": conservative_res.id,
        "comprehensive_result_id": comprehensive_res.id,
        "pubmed_res_obj": pubmed_res,
        "conservative_res_obj": conservative_res,
        "comprehensive_res_obj": comprehensive_res,
    }


@pytest.mark.integration
def test_placeholder(db_session: Session, seed_data: dict[str, Any]):
    """Placeholder test to ensure fixtures run."""
    assert db_session is not None
    assert seed_data["review_id"] is not None
    print("Seed data fixture provided:", seed_data)


# --- Add Resolver Test Functions Below --- #


@pytest.mark.integration
def test_create_resolution_success(db_session: Session, seed_data: dict[str, Any]):
    """Test successfully creating and retrieving a ScreeningResolution."""
    # Initialize without id
    new_resolution = ScreeningResolution(
        review_id=seed_data["review_id"],
        pubmed_result_id=seed_data["pubmed_result_id"],
        conservative_result_id=seed_data["conservative_result_id"],
        comprehensive_result_id=seed_data["comprehensive_result_id"],
        resolver_decision=ScreeningDecisionType.INCLUDE,
        resolver_reasoning="Resolver decided INCLUDE based on criteria X.",
        resolver_confidence_score=0.88,
        resolver_model_name="test-resolver-model",
        response_metadata={"resolver_test": True},
        start_time=datetime.now(UTC),
        end_time=datetime.now(UTC),
        trace_id=uuid.uuid4(),
    )

    db_session.add(new_resolution)
    db_session.commit()
    db_session.refresh(new_resolution)  # Refresh to get the generated ID

    # Retrieve and verify
    resolution_id = new_resolution.id  # Get ID after refresh
    retrieved_resolution = db_session.get(ScreeningResolution, resolution_id)
    assert retrieved_resolution is not None
    assert retrieved_resolution.id == resolution_id
    assert retrieved_resolution.review_id == seed_data["review_id"]
    assert retrieved_resolution.pubmed_result_id == seed_data["pubmed_result_id"]
    assert retrieved_resolution.resolver_decision == ScreeningDecisionType.INCLUDE
    assert (
        retrieved_resolution.resolver_reasoning
        == "Resolver decided INCLUDE based on criteria X."
    )
    assert retrieved_resolution.resolver_confidence_score == 0.88
    assert retrieved_resolution.response_metadata is not None
    assert retrieved_resolution.response_metadata["resolver_test"] is True


@pytest.mark.integration
def test_resolve_conflict_scenario_include(
    db_session: Session, seed_data: dict[str, Any]
):
    """Test simulating a resolution where the final decision is INCLUDE and updating PubMedResult."""
    # Initialize without id
    new_resolution = ScreeningResolution(
        review_id=seed_data["review_id"],
        pubmed_result_id=seed_data["pubmed_result_id"],
        conservative_result_id=seed_data["conservative_result_id"],
        comprehensive_result_id=seed_data["comprehensive_result_id"],
        resolver_decision=ScreeningDecisionType.INCLUDE,
        resolver_reasoning="Reasoning for final INCLUDE.",
        resolver_confidence_score=0.92,
        resolver_model_name="test-resolver-model",
        response_metadata={},
    )
    db_session.add(new_resolution)
    db_session.commit()  # Commit resolution first
    db_session.refresh(new_resolution)  # Refresh to get ID
    resolution_id = new_resolution.id

    # 2. Update the PubMedResult
    pubmed_result = db_session.get(PubMedResult, seed_data["pubmed_result_id"])
    assert pubmed_result is not None
    pubmed_result.resolution_id = resolution_id
    # REMOVED: No final_decision field on PubMedResult
    # pubmed_result.final_decision = resolver_decision
    db_session.add(pubmed_result)
    db_session.commit()
    db_session.refresh(pubmed_result)

    # 3. Verify PubMedResult update
    assert pubmed_result.resolution_id == resolution_id

    # 4. Verify Resolution record exists and has the correct decision
    retrieved_resolution = db_session.get(ScreeningResolution, resolution_id)
    assert retrieved_resolution is not None
    assert retrieved_resolution.resolver_decision == ScreeningDecisionType.INCLUDE


@pytest.mark.integration
def test_resolve_conflict_scenario_exclude(
    db_session: Session, seed_data: dict[str, Any]
):
    """Test simulating a resolution where the final decision is EXCLUDE."""
    # Initialize without id
    new_resolution = ScreeningResolution(
        review_id=seed_data["review_id"],
        pubmed_result_id=seed_data["pubmed_result_id"],
        conservative_result_id=seed_data["conservative_result_id"],
        comprehensive_result_id=seed_data["comprehensive_result_id"],
        resolver_decision=ScreeningDecisionType.EXCLUDE,
        resolver_reasoning="Reasoning for final EXCLUDE.",
        resolver_confidence_score=0.95,
        resolver_model_name="test-resolver-model",
        response_metadata={},
    )
    db_session.add(new_resolution)
    db_session.commit()
    db_session.refresh(new_resolution)  # Refresh to get ID
    resolution_id = new_resolution.id

    # 2. Update the PubMedResult
    pubmed_result = db_session.get(PubMedResult, seed_data["pubmed_result_id"])
    assert pubmed_result is not None
    pubmed_result.resolution_id = resolution_id
    db_session.add(pubmed_result)
    db_session.commit()
    db_session.refresh(pubmed_result)

    # 3. Verify PubMedResult update
    assert pubmed_result.resolution_id == resolution_id

    # 4. Verify Resolution record exists and has the correct decision
    retrieved_resolution = db_session.get(ScreeningResolution, resolution_id)
    assert retrieved_resolution is not None
    assert retrieved_resolution.resolver_decision == ScreeningDecisionType.EXCLUDE


@pytest.mark.integration
def test_resolve_conflict_scenario_uncertain(
    db_session: Session, seed_data: dict[str, Any]
):
    """Test simulating a resolution where the final decision is UNCERTAIN."""
    # Initialize without id
    new_resolution = ScreeningResolution(
        review_id=seed_data["review_id"],
        pubmed_result_id=seed_data["pubmed_result_id"],
        conservative_result_id=seed_data["conservative_result_id"],
        comprehensive_result_id=seed_data["comprehensive_result_id"],
        resolver_decision=ScreeningDecisionType.UNCERTAIN,
        resolver_reasoning="Reasoning for UNCERTAIN.",
        resolver_confidence_score=0.55,
        resolver_model_name="test-resolver-model",
        response_metadata={},
    )
    db_session.add(new_resolution)
    db_session.commit()
    db_session.refresh(new_resolution)  # Refresh to get ID
    resolution_id = new_resolution.id

    # 2. Update the PubMedResult
    pubmed_result = db_session.get(PubMedResult, seed_data["pubmed_result_id"])
    assert pubmed_result is not None
    pubmed_result.resolution_id = resolution_id
    db_session.add(pubmed_result)
    db_session.commit()
    db_session.refresh(pubmed_result)

    # 3. Verify PubMedResult update
    assert pubmed_result.resolution_id == resolution_id

    # 4. Verify Resolution record exists and has the correct decision
    retrieved_resolution = db_session.get(ScreeningResolution, resolution_id)
    assert retrieved_resolution is not None
    assert retrieved_resolution.resolver_decision == ScreeningDecisionType.UNCERTAIN


@pytest.mark.integration
def test_resolution_links_pubmed_and_abstracts(
    db_session: Session, seed_data: dict[str, Any]
):
    """Test verifying FKs load correctly from ScreeningResolution."""
    # Initialize without id
    new_resolution = ScreeningResolution(
        review_id=seed_data["review_id"],
        pubmed_result_id=seed_data["pubmed_result_id"],
        conservative_result_id=seed_data["conservative_result_id"],
        comprehensive_result_id=seed_data["comprehensive_result_id"],
        resolver_decision=ScreeningDecisionType.EXCLUDE,
        resolver_reasoning="Testing links.",
        resolver_confidence_score=0.7,
        resolver_model_name="test-linker-model",
        response_metadata={},
    )
    db_session.add(new_resolution)
    db_session.commit()
    db_session.refresh(new_resolution)  # Refresh to get ID
    resolution_id = new_resolution.id

    # Retrieve resolution and check related objects (lazy loading or explicit query)
    retrieved = db_session.get(ScreeningResolution, resolution_id)
    assert retrieved is not None

    # Check PubMedResult link (assuming relationship name is 'pubmed_result')
    # This relies on SQLAlchemy relationship loading (lazy by default)
    assert retrieved.pubmed_result is not None
    assert retrieved.pubmed_result.id == seed_data["pubmed_result_id"]

    # Check ScreenAbstractResult FOREIGN KEY IDs are correct
    assert retrieved.conservative_result_id == seed_data["conservative_result_id"]
    assert retrieved.comprehensive_result_id == seed_data["comprehensive_result_id"]


@pytest.mark.integration
def test_query_resolutions_by_review(db_session: Session, seed_data: dict[str, Any]):
    """Test querying resolutions by review_id."""
    # Initialize without id
    res1 = ScreeningResolution(
        review_id=seed_data["review_id"],
        pubmed_result_id=seed_data["pubmed_result_id"],
        conservative_result_id=seed_data["conservative_result_id"],
        comprehensive_result_id=seed_data["comprehensive_result_id"],
        resolver_decision=ScreeningDecisionType.INCLUDE,
        resolver_reasoning="First resolution for review.",
        resolver_confidence_score=0.8,
        resolver_model_name="test-model",
        response_metadata={},
    )
    # Initialize without id
    res2 = ScreeningResolution(
        review_id=seed_data["review_id"],
        pubmed_result_id=seed_data["pubmed_result_id"],
        conservative_result_id=seed_data["conservative_result_id"],
        comprehensive_result_id=seed_data["comprehensive_result_id"],
        resolver_decision=ScreeningDecisionType.EXCLUDE,  # Different decision
        resolver_reasoning="Second resolution for review.",
        resolver_confidence_score=0.85,
        resolver_model_name="test-model",
        response_metadata={},
    )

    db_session.add_all([res1, res2])
    db_session.commit()
    # Refresh needed to get IDs if we assert on them
    db_session.refresh(res1)
    db_session.refresh(res2)
    resolution_id_1 = res1.id
    resolution_id_2 = res2.id

    # Query by review_id
    stmt = select(ScreeningResolution).where(
        ScreeningResolution.review_id == seed_data["review_id"]
    )
    results = db_session.exec(stmt).all()

    assert len(results) == 2
    result_ids = {res.id for res in results}
    assert resolution_id_1 in result_ids
    assert resolution_id_2 in result_ids
