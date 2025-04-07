"""Integration tests for the suggestion agent."""

from __future__ import annotations

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from sr_assistant.core.models import SystematicReview
from sr_assistant.step1.suggestion_agent import SuggestionAgent


@pytest.fixture
def agent() -> SuggestionAgent:
    """Create a suggestion agent for testing."""
    return SuggestionAgent(model="gpt-4o", temperature=0.0)


@pytest.fixture
def sample_criteria() -> SystematicReview:
    """Create sample review criteria for testing."""
    return SystematicReview(
        background="This is a sample background for a systematic review.",
        research_question="Does cognitive behavioral therapy (CBT) improve anxiety symptoms in adults with generalized anxiety disorder?",
        inclusion_criteria="Adults >18, Diagnosed GAD, CBT intervention, RCTs, English language",
        exclusion_criteria="Children <18, Non-human studies, Case reports, Studies without control groups",
    )


@pytest.mark.integration
def test_agent_suggestions(agent: SuggestionAgent, sample_criteria: SystematicReview) -> None:
    """Test that the agent provides suggestions and maintains message history."""
    # Get suggestions
    suggestions = agent.get_suggestions(sample_criteria)

    # Verify we got a non-empty response
    assert suggestions, "Agent should return non-empty suggestions"
    assert len(suggestions) > 100, "Response should be substantial"

    # Check message history
    history = agent.get_message_history()
    assert len(history) == 2, "Should have one human message and one AI message"
    assert isinstance(history[0], HumanMessage), "First message should be from human"
    assert isinstance(history[1], AIMessage), "Second message should be from AI"

    # Verify history content
    assert "Research Question" in history[0].content
    assert "CBT" in history[0].content
    assert history[1].content == suggestions


@pytest.mark.integration
def test_agent_multiple_interactions(
    agent: SuggestionAgent, sample_criteria: SystematicReview
) -> None:
    """Test that the agent maintains history across multiple interactions."""
    # First interaction
    first_response = agent.get_suggestions(sample_criteria)
    assert first_response, "First response should not be empty"

    # Second interaction with modified criteria
    modified_criteria = SystematicReview(
        research_question=sample_criteria.research_question,
        inclusion_criteria=sample_criteria.inclusion_criteria
        + ", Published after 2010",
        exclusion_criteria=sample_criteria.exclusion_criteria,
    )
    second_response = agent.get_suggestions(modified_criteria)
    assert second_response, "Second response should not be empty"

    # Check history
    history = agent.get_message_history()
    assert len(history) == 4, "Should have four messages (2 human, 2 AI)"
    assert isinstance(history[0], HumanMessage)
    assert isinstance(history[1], AIMessage)
    assert isinstance(history[2], HumanMessage)
    assert isinstance(history[3], AIMessage)

    # Verify responses are different
    assert first_response != second_response, "Responses should be different"


@pytest.mark.integration
def test_agent_clear_history(agent: SuggestionAgent, sample_criteria: SystematicReview) -> None:
    """Test that the agent can clear its message history."""
    # Get initial suggestions
    agent.get_suggestions(sample_criteria)
    assert len(agent.get_message_history()) == 2, "Should have two messages"

    # Clear history
    agent.clear_history()
    assert len(agent.get_message_history()) == 0, "History should be empty"

    # Get new suggestions
    new_suggestions = agent.get_suggestions(sample_criteria)
    assert new_suggestions, "Should get new suggestions after clearing history"
    assert len(agent.get_message_history()) == 2, "Should have two new messages"
