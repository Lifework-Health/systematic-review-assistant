"""Unit tests for screening agents module."""

import uuid
from unittest.mock import MagicMock

from sr_assistant.app.agents.screening_agents import (
    ScreenAbstractResultTuple,
    ScreenAbstractsChainInput,
    ScreeningError,
    make_screen_abstracts_chain_input,
)
from sr_assistant.core import models
from sr_assistant.core.schemas import ScreeningResponse, ScreeningResult


class TestScreenAbstractsChainInput:
    """Tests for ScreenAbstractsChainInput pydantic model."""

    def test_default_values(self) -> None:
        """Test default value for background."""
        input_data = ScreenAbstractsChainInput(
            research_question="Test question",
            inclusion_criteria="Test inclusion",
            exclusion_criteria="Test exclusion",
            title="Test title",
            journal="Test journal",
            year="2023",
            abstract="Test abstract",
        )

        assert input_data.background == "<no background provided>"
        assert input_data.research_question == "Test question"
        assert input_data.inclusion_criteria == "Test inclusion"
        assert input_data.exclusion_criteria == "Test exclusion"
        assert input_data.title == "Test title"
        assert input_data.journal == "Test journal"
        assert input_data.year == "2023"
        assert input_data.abstract == "Test abstract"

    def test_model_dump(self) -> None:
        """Test model_dump() returns expected dict."""
        input_data = ScreenAbstractsChainInput(
            background="Test background",
            research_question="Test question",
            inclusion_criteria="Test inclusion",
            exclusion_criteria="Test exclusion",
            title="Test title",
            journal="Test journal",
            year="2023",
            abstract="Test abstract",
        )

        dumped = input_data.model_dump()

        assert dumped["background"] == "Test background"
        assert dumped["research_question"] == "Test question"
        assert dumped["inclusion_criteria"] == "Test inclusion"
        assert dumped["exclusion_criteria"] == "Test exclusion"
        assert dumped["title"] == "Test title"
        assert dumped["journal"] == "Test journal"
        assert dumped["year"] == "2023"
        assert dumped["abstract"] == "Test abstract"


class TestScreeningError:
    """Tests for ScreeningError pydantic model."""

    def test_init_with_minimal_args(self) -> None:
        """Test initialization with minimal arguments."""
        search_result = MagicMock(spec=models.PubMedResult)
        error = MagicMock()

        screening_error = ScreeningError(
            search_result=search_result,
            error=error,
        )

        assert screening_error.search_result is search_result
        assert screening_error.error is error
        assert screening_error.message is None

    def test_init_with_message(self) -> None:
        """Test initialization with explicit message."""
        search_result = MagicMock(spec=models.PubMedResult)
        error = MagicMock()
        message = "Test error message"

        screening_error = ScreeningError(
            search_result=search_result,
            error=error,
            message=message,
        )

        assert screening_error.search_result is search_result
        assert screening_error.error is error
        assert screening_error.message == message

    def test_validator_with_screening_result(self) -> None:
        """Test _validate_error_and_message with ScreeningResult as error."""
        search_result = MagicMock(spec=models.PubMedResult)
        error = MagicMock(spec=ScreeningResult)

        screening_error = ScreeningError(
            search_result=search_result,
            error=error,
        )

        assert screening_error.message == "ScreeningResult should always have a message"

    def test_validator_with_screening_response(self) -> None:
        """Test _validate_error_and_message with ScreeningResponse as error."""
        search_result = MagicMock(spec=models.PubMedResult)
        error = MagicMock(spec=ScreeningResponse)

        screening_error = ScreeningError(
            search_result=search_result,
            error=error,
        )

        assert (
            screening_error.message
            == "Chain on_end failed, this is nested chain's screening output"
        )


class TestScreenAbstractResultTuple:
    """Tests for ScreenAbstractResultTuple named tuple."""

    def test_creation(self) -> None:
        """Test creating a ScreenAbstractResultTuple."""
        search_result = MagicMock(spec=models.PubMedResult)
        conservative_result = MagicMock(spec=ScreeningResult)
        comprehensive_result = MagicMock(spec=ScreeningError)

        result_tuple = ScreenAbstractResultTuple(
            search_result=search_result,
            conservative_result=conservative_result,
            comprehensive_result=comprehensive_result,
        )

        assert result_tuple.search_result is search_result
        assert result_tuple.conservative_result is conservative_result
        assert result_tuple.comprehensive_result is comprehensive_result


class TestMakeScreenAbstractsChainInput:
    """Tests for make_screen_abstracts_chain_input function."""

    def test_empty_batch(self) -> None:
        """Test with empty pubmed results batch."""
        pubmed_results_batch: list[models.PubMedResult] = []
        mock_review = MagicMock(spec=models.SystematicReview)
        mock_review.id = uuid.uuid4()
        mock_review.background = "Test background"
        mock_review.research_question = "Test question"
        mock_review.inclusion_criteria = "Test inclusion"
        mock_review.exclusion_criteria = "Test exclusion"

        result = make_screen_abstracts_chain_input(pubmed_results_batch, mock_review)

        assert isinstance(result, dict)
        assert "inputs" in result
        assert "config" in result
        assert len(result["inputs"]) == 0
        assert len(result["config"]) == 0

    def test_single_item_batch(self) -> None:
        """Test with a batch containing a single PubMedResult."""
        mock_pubmed_result = MagicMock(spec=models.PubMedResult)
        mock_pubmed_result.id = uuid.uuid4()
        mock_pubmed_result.title = "Test title"
        mock_pubmed_result.journal = "Test journal"
        mock_pubmed_result.year = "2023"
        mock_pubmed_result.abstract = "Test abstract"

        pubmed_results_batch = [mock_pubmed_result]

        mock_review = MagicMock(spec=models.SystematicReview)
        mock_review.id = uuid.uuid4()
        mock_review.background = "Test background"
        mock_review.research_question = "Test question"
        mock_review.inclusion_criteria = "Test inclusion"
        mock_review.exclusion_criteria = "Test exclusion"

        result = make_screen_abstracts_chain_input(pubmed_results_batch, mock_review)

        assert isinstance(result, dict)
        assert "inputs" in result
        assert "config" in result
        assert len(result["inputs"]) == 1
        assert len(result["config"]) == 1

        # Check content of inputs
        input_item = result["inputs"][0]
        assert input_item["background"] == "Test background"
        assert input_item["research_question"] == "Test question"
        assert input_item["inclusion_criteria"] == "Test inclusion"
        assert input_item["exclusion_criteria"] == "Test exclusion"
        assert input_item["title"] == "Test title"
        assert input_item["journal"] == "Test journal"
        assert input_item["year"] == "2023"
        assert input_item["abstract"] == "Test abstract"

        # Check content of config
        config_item = result["config"][0]
        assert "metadata" in config_item
        assert config_item["metadata"]["review_id"] == str(mock_review.id)
        assert config_item["metadata"]["pubmed_result_id"] == str(mock_pubmed_result.id)

        # Check tags
        assert "tags" in config_item
        assert f"sra:review_id:{mock_review.id}" in config_item["tags"]
        assert f"sra:pubmed_result_id:{mock_pubmed_result.id}" in config_item["tags"]
        assert "sra:screen_abstracts_chain:i:0" in config_item["tags"]

    def test_multi_item_batch(self) -> None:
        """Test with a batch containing multiple PubMedResults."""
        # Create mock PubMedResults
        mock_pubmed_results = []
        for i in range(3):
            mock_pubmed_result = MagicMock(spec=models.PubMedResult)
            mock_pubmed_result.id = uuid.uuid4()
            mock_pubmed_result.title = f"Test title {i}"
            mock_pubmed_result.journal = f"Test journal {i}"
            mock_pubmed_result.year = f"202{i}"
            mock_pubmed_result.abstract = f"Test abstract {i}"
            mock_pubmed_results.append(mock_pubmed_result)

        pubmed_results_batch = mock_pubmed_results

        mock_review = MagicMock(spec=models.SystematicReview)
        mock_review.id = uuid.uuid4()
        mock_review.background = "Test background"
        mock_review.research_question = "Test question"
        mock_review.inclusion_criteria = "Test inclusion"
        mock_review.exclusion_criteria = "Test exclusion"

        result = make_screen_abstracts_chain_input(pubmed_results_batch, mock_review)

        assert isinstance(result, dict)
        assert "inputs" in result
        assert "config" in result
        assert len(result["inputs"]) == 3
        assert len(result["config"]) == 3

        # Check content of each input item
        for i, input_item in enumerate(result["inputs"]):
            assert input_item["background"] == "Test background"
            assert input_item["research_question"] == "Test question"
            assert input_item["inclusion_criteria"] == "Test inclusion"
            assert input_item["exclusion_criteria"] == "Test exclusion"
            assert input_item["title"] == f"Test title {i}"
            assert input_item["journal"] == f"Test journal {i}"
            assert input_item["year"] == f"202{i}"
            assert input_item["abstract"] == f"Test abstract {i}"

        # Check content of each config item
        for i, config_item in enumerate(result["config"]):
            assert "metadata" in config_item
            assert config_item["metadata"]["review_id"] == str(mock_review.id)
            assert config_item["metadata"]["pubmed_result_id"] == str(
                mock_pubmed_results[i].id
            )

            # Check tags
            assert "tags" in config_item
            assert f"sra:review_id:{mock_review.id}" in config_item["tags"]
            assert (
                f"sra:pubmed_result_id:{mock_pubmed_results[i].id}"
                in config_item["tags"]
            )
            assert f"sra:screen_abstracts_chain:i:{i}" in config_item["tags"]
