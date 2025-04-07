# tests/unit/app/pages/test_protocol.py
import uuid
from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import streamlit as st
from pytest import MonkeyPatch
from sqlmodel import Session

# Import functions and classes to test
from sr_assistant.app.pages.protocol import (
    build_review_model_from_pico,
    persist_review,
)
from sr_assistant.core.models import CriteriaFramework, SystematicReview


@pytest.fixture
def mock_session_state_with_pico(
    monkeypatch: MonkeyPatch,
) -> Generator[dict[str, Any], None, None]:
    """Fixture to mock st.session_state with PICO data."""
    mock_state = {
        "review_id": uuid.uuid4(),
        "background": "Test background about disease X.",
        "research_question": "Does drug Y work for disease X?",
        "pico_population": "Adults with disease X",
        "pico_intervention": "Drug Y 50mg",
        "pico_comparison": "Placebo",
        "pico_outcome": "Symptom reduction",
        "exclusion_criteria": "Pregnant women",
    }
    # Use monkeypatch for streamlit state as direct patching can be tricky
    for key, value in mock_state.items():
        monkeypatch.setattr(st.session_state, key, value, raising=False)
    # Ensure session_factory exists if persist_review needs it
    mock_session_factory = MagicMock()
    monkeypatch.setattr(
        st.session_state, "session_factory", mock_session_factory, raising=False
    )
    yield mock_state  # Yield the dict for potential use in tests
    # Teardown (optional, monkeypatch handles it but good practice)
    for key in mock_state:
        monkeypatch.delattr(st.session_state, key, raising=False)
    monkeypatch.delattr(st.session_state, "session_factory", raising=False)


# --- Tests for build_review_model_from_pico ---


def test_build_review_model_from_pico_all_fields(
    mock_session_state_with_pico: dict[str, Any],
):
    """Test building model when all PICO fields are present."""
    mock_response_widget = MagicMock()
    review = build_review_model_from_pico(mock_response_widget)

    assert isinstance(review, SystematicReview)
    assert review.id == st.session_state.review_id
    assert review.background == "Test background about disease X."
    assert review.research_question == "Does drug Y work for disease X?"
    # Check derived inclusion criteria string
    assert "Population: Adults with disease X" in review.inclusion_criteria
    assert "Intervention: Drug Y 50mg" in review.inclusion_criteria
    assert "Comparison: Placebo" in review.inclusion_criteria
    assert "Outcome: Symptom reduction" in review.inclusion_criteria
    # Check separate exclusion criteria
    assert review.exclusion_criteria == "Pregnant women"
    # Check structured PICO fields
    assert review.criteria_framework == CriteriaFramework.PICO
    assert review.criteria_framework_answers == {
        "population": "Adults with disease X",
        "intervention": "Drug Y 50mg",
        "comparison": "Placebo",
        "outcome": "Symptom reduction",
    }
    mock_response_widget.success.assert_called_once()


def test_build_review_model_from_pico_missing_fields(
    mock_session_state_with_pico: dict[str, Any],
):
    """Test building model when some PICO fields are missing."""
    # Simulate missing comparison and outcome
    st.session_state.pico_comparison = ""
    st.session_state.pico_outcome = ""
    st.session_state.exclusion_criteria = ""  # And missing exclusion

    mock_response_widget = MagicMock()
    review = build_review_model_from_pico(mock_response_widget)

    assert isinstance(review, SystematicReview)
    assert "Population: Adults with disease X" in review.inclusion_criteria
    assert "Intervention: Drug Y 50mg" in review.inclusion_criteria
    assert (
        "Comparison:" not in review.inclusion_criteria
    )  # Check missing field isn't included
    assert "Outcome:" not in review.inclusion_criteria
    assert review.exclusion_criteria == "Not specified"  # Check default
    assert review.criteria_framework == CriteriaFramework.PICO
    assert review.criteria_framework_answers == {
        "population": "Adults with disease X",
        "intervention": "Drug Y 50mg",
        "comparison": "",  # Should be empty string
        "outcome": "",  # Should be empty string
    }
    mock_response_widget.success.assert_called_once()


# --- Tests for persist_review ---


@patch(
    "sr_assistant.app.pages.protocol.select"
)  # Patch select used within persist_review
def test_persist_review_new_record(
    mock_select: MagicMock, mock_session_state_with_pico: dict[str, Any]
):
    """Test saving a new review with PICO data."""
    # Build a model to save
    review_to_save = build_review_model_from_pico(MagicMock())

    # Mock the database session context manager and methods
    mock_session = MagicMock(spec=Session)
    # Simulate record not found
    mock_session.exec.return_value.first.return_value = None

    # Configure session_factory mock to return our mock_session context
    mock_session_context = MagicMock()
    mock_session_context.__enter__.return_value = mock_session
    st.session_state.session_factory.return_value = mock_session_context

    # Call persist_review
    persisted_review = persist_review(review_to_save)

    # Assertions
    mock_select.assert_called_once_with(SystematicReview)  # Check select was called
    mock_session.exec.assert_called_once()  # Check query was executed
    mock_session.add.assert_called_once_with(
        review_to_save
    )  # Check add was called for new record
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(review_to_save)
    assert persisted_review is review_to_save  # Should return the added model


@patch("sr_assistant.app.pages.protocol.select")
def test_persist_review_update_record(
    mock_select: MagicMock, mock_session_state_with_pico: dict[str, Any]
):
    """Test updating an existing review with PICO data."""
    # Existing DB model mock
    existing_db_model = SystematicReview(
        id=st.session_state.review_id,  # Use same ID
        background="Old background",
        research_question="Old question?",
        inclusion_criteria="Old inclusion",
        exclusion_criteria="Old exclusion",
        criteria_framework=None,  # Simulate no framework initially
        criteria_framework_answers={},
    )

    # Build the updated model with new PICO data
    updated_model_data = build_review_model_from_pico(MagicMock())

    # Mock the database session context manager and methods
    mock_session = MagicMock(spec=Session)
    # Simulate finding the existing record
    mock_exec_result = MagicMock()
    mock_exec_result.first.return_value = existing_db_model
    mock_session.exec.return_value = mock_exec_result

    # Configure session_factory mock
    mock_session_context = MagicMock()
    mock_session_context.__enter__.return_value = mock_session
    st.session_state.session_factory.return_value = mock_session_context

    # Call persist_review
    persisted_review = persist_review(updated_model_data)

    # Assertions
    mock_select.assert_called_once_with(SystematicReview)
    mock_session.exec.assert_called_once()
    mock_session.add.assert_not_called()  # Should NOT call add for update
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(
        existing_db_model
    )  # Should refresh the DB model instance
    assert persisted_review is existing_db_model  # Should return the DB model instance

    # Verify fields were updated on the existing DB model mock
    assert existing_db_model.background == updated_model_data.background
    assert existing_db_model.research_question == updated_model_data.research_question
    assert existing_db_model.inclusion_criteria == updated_model_data.inclusion_criteria
    assert existing_db_model.exclusion_criteria == updated_model_data.exclusion_criteria
    assert (
        existing_db_model.criteria_framework == CriteriaFramework.PICO
    )  # Check updated
    assert (
        existing_db_model.criteria_framework_answers
        == updated_model_data.criteria_framework_answers
    )  # Check updated
    assert existing_db_model.updated_at is not None  # Check timestamp was set
