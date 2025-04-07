"""Suggestion agent for systematic review criteria.

Needs a rewrite.
"""

from __future__ import annotations

from langchain_openai import ChatOpenAI
from loguru import logger

from sr_assistant.core.models import SystematicReview
from sr_assistant.core.schemas import PicosSuggestions, SuggestionResult


class SuggestionAgent:
    """Agent for providing suggestions on systematic review criteria."""

    def __init__(self, model: str = "gpt-4o", temperature: float = 0.0) -> None:
        """Initialize the agent with model configuration."""
        self.llm = ChatOpenAI(
            model=model, temperature=temperature
        ).with_structured_output(PicosSuggestions)

    @logger.catch(Exception)
    def get_suggestions(self, review: SystematicReview) -> SuggestionResult:
        """Generates PICO suggestions and critique based on background and question."""
        logger.info("Generating PICO suggestions...")

        prompt = f"""Given the following systematic review context:

        Background: {review.background}
        Research Question: {review.research_question}

        Analyze the background and research question, then generate structured suggestions for the PICO components (Population, Intervention, Comparison, Outcome).
        Also provide a brief general critique or suggestions for clarifying the protocol based ONLY on the background and research question provided.

        If a component cannot be reliably inferred, leave its suggestion empty or state why.
        """

        try:
            structured_response: PicosSuggestions = self.llm.invoke(prompt)
            logger.info(f"Received structured PICO suggestions: {structured_response}")
            return SuggestionResult(
                pico=structured_response,
                raw_response=structured_response.general_critique,
            )
        except Exception as e:
            logger.exception("LLM call failed during PICO suggestion generation.")
            return SuggestionResult(
                pico=None, raw_response=f"Error generating suggestions: {e}"
            )
