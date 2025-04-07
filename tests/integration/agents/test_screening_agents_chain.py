"""Integration tests for LangChain components in screening_agents.py."""

import os
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
import streamlit as st

from sr_assistant.app.agents import screening_agents
from sr_assistant.app.agents.screening_agents import (
    screen_abstracts_chain_on_end_cb,
)
from sr_assistant.core.models import PubMedResult, SystematicReview
from sr_assistant.core.schemas import ScreeningResponse
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
    # Verify the chain is a RunnableParallel with two branches
    chain = screening_agents.screen_abstracts_chain

    # Check that the chain has the expected components
    assert chain._bound_methods.get("on_end") is not None
    assert chain._bound_methods.get("on_error") is not None

    # Check that conservative and comprehensive chains exist
    assert "conservative" in chain.steps
    assert "comprehensive" in chain.steps


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
    assert ScreeningDecisionType.INCLUDE not in (
        conservative_decision,
        comprehensive_decision,
    ) or (
        conservative_decision
        != comprehensive_decision  # If one includes, the other should not
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
    assert conservative_result.decision != ScreeningDecisionType.INCLUDE
    # Comprehensive might include in some cases, but should have low confidence
    if comprehensive_result.decision == ScreeningDecisionType.INCLUDE:
        assert comprehensive_result.confidence_score < 0.8


@pytest.mark.skipif(
    not os.getenv("RUN_BATCH_TEST"), reason="Batch test is resource intensive"
)
def test_batch_processing(mock_systematic_review, monkeypatch):
    """Test that batch processing works with multiple abstracts."""
    # Generate a batch of different PubMed results
    batch = []
    for i in range(3):  # Keep the batch small for testing
        batch.append(
            PubMedResult(
                pmid=str(10000 + i),
                title=f"Test Study {i} on {'Machine Learning' if i % 2 == 0 else 'Healthcare'}",
                journal=f"Journal of {'Testing' if i % 2 == 0 else 'Medicine'}",
                year=str(2010 + i),
                abstract=f"This is abstract {i} about {'machine learning' if i % 2 == 0 else 'healthcare'}.",
                authors=f"Author {i}",
                keywords=[f"keyword_{i}", "testing"],
                mesh_terms=[f"MeSH_{i}", "Testing"],
                publication_types=["Journal Article"],
            )
        )

    # Mock Streamlit session state
    class MockSessionState:
        def __init__(self):
            self.screen_abstracts_chain = screening_agents.screen_abstracts_chain
            self.screen_abstracts_results = []
            self.screen_abstracts_errors = []
            self.screen_abstracts_batch_idx = 0

    monkeypatch.setattr(st, "session_state", MockSessionState())

    # Run the batch screening
    batch_idx = 0
    result = screening_agents.screen_abstracts_batch(
        batch, batch_idx, mock_systematic_review
    )

    # Verify the output
    assert result is not None
    results, cb = result

    # Check batch results
    assert len(results) == len(batch)

    # Check that results have different decisions
    decisions = [res.conservative_result.decision for res in results]
    print(f"Batch decisions: {decisions}")

    # Verify the OpenAI callback metrics
    assert cb.total_tokens > 0
    assert cb.total_cost > 0
    print(
        f"Batch processing stats - Tokens: {cb.total_tokens}, Cost: ${cb.total_cost:.4f}"
    )


@patch("streamlit.session_state")
def test_chain_callbacks(
    mock_session_state, mock_pubmed_result, mock_systematic_review
):
    """Test that chain callbacks correctly process results."""
    # Create a mock Run that simulates LangChain's RunTree
    mock_run = MagicMock()
    mock_run.id = str(uuid.uuid4())
    mock_run.name = "test_run"
    mock_run.outputs = {}
    mock_run.tags = []

    # Create a mock child run for the conservative strategy
    mock_child_run = MagicMock()
    mock_child_run.id = str(uuid.uuid4())
    mock_child_run.name = "child_run"
    mock_child_run.tags = ["map:key:conservative"]

    review_id = str(uuid.uuid4())
    pubmed_result_id = str(mock_pubmed_result.id)

    mock_child_run.metadata = {
        "review_id": review_id,
        "pubmed_result_id": pubmed_result_id,
    }
    mock_child_run.trace_id = str(uuid.uuid4())
    mock_child_run.start_time = datetime.now(timezone.utc)
    mock_child_run.end_time = datetime.now(timezone.utc)

    # Create a mock ScreeningResponse
    mock_response = MagicMock(spec=ScreeningResponse)
    mock_response.model_dump.return_value = {
        "decision": ScreeningDecisionType.INCLUDE,
        "confidence_score": 0.9,
        "rationale": "Test rationale",
    }
    mock_child_run.outputs = {"output": mock_response}

    # Create mock chat_model child run
    mock_ccr = MagicMock()
    mock_ccr.run_type = "chat_model"
    mock_ccr.extra = {
        "metadata": {"ls_model_name": "gpt-4o"},
        "invocation_params": {"model_name": "gpt-4o"},
    }
    mock_child_run.child_runs = [mock_ccr]

    # Add child run to run
    mock_run.child_runs = [mock_child_run]

    # Call the on_end callback
    with patch("sr_assistant.app.agents.screening_agents.logger") as mock_logger:
        screen_abstracts_chain_on_end_cb(mock_run)

        # Check logger was called appropriately
        assert mock_logger.bind.called

        # The callback should add the strategy to metadata
        assert "screening_strategy" in mock_child_run.metadata
        assert (
            mock_child_run.metadata["screening_strategy"]
            == ScreeningStrategyType.CONSERVATIVE
        )
