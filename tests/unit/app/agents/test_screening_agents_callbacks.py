"""Unit tests for screening agents callback functions."""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, call, patch

from sr_assistant.app.agents.screening_agents import (
    chain_on_error_listener_cb,
    screen_abstracts_chain_on_end_cb,
)
from sr_assistant.core.schemas import ScreeningResponse


class TestChainOnErrorListenerCb:
    """Tests for chain_on_error_listener_cb function."""

    @patch("sr_assistant.app.agents.screening_agents.logger")
    def test_error_logging(self, mock_logger: MagicMock) -> None:
        """Test that errors and associated run objects are logged correctly."""
        # Create a mock Run object with child runs
        mock_run = MagicMock(name="MockRun")
        run_id = str(uuid.uuid4())
        mock_run.id = run_id
        mock_run.name = "test_run"

        mock_child_run1 = MagicMock(name="MockChildRun1")
        mock_child_run1.id = str(uuid.uuid4())
        mock_child_run1.name = "child_run1"

        mock_child_run2 = MagicMock(name="MockChildRun2")
        mock_child_run2.id = str(uuid.uuid4())
        mock_child_run2.name = "child_run2"

        mock_run.child_runs = [mock_child_run1, mock_child_run2]

        # Define the error
        test_error = ValueError("Simulated error for testing")

        # Call the function with the error and the run object in kwargs
        # Note: The original callback signature might have been different previously
        # Ensure this call matches the signature in screening_agents.py
        chain_on_error_listener_cb(test_error, run=mock_run)

        # Get the list of calls made to the mock_logger and its returned mocks
        calls = mock_logger.mock_calls

        # Expected sequence of calls:
        expected_calls = [
            # 1. Initial bind for parent run
            call.bind(run_id=run_id, run_name=mock_run.name),
            # 2. Exception log on the bound logger
            call.bind().exception(
                f"Error during chain execution: run_id={run_id}, error={test_error!r}, kwargs={{'run': {mock_run!r}}}",
                error=test_error,
                kwargs={
                    "run": mock_run
                },  # Note: The actual kwargs dict might vary slightly based on test execution context
            ),
            # 3. Error log for parent run object
            call.bind().error("Associated run object: {run_obj!r}", run_obj=mock_run),
            # 4. Bind for first child run
            call.bind(
                run_id=mock_child_run1.id,
                run_name=mock_child_run1.name,
                parent_run_id=run_id,
                parent_run_name=mock_run.name,
            ),
            # 5. Error log for first child run
            call.bind().error("Associated child run: {cr!r}", cr=mock_child_run1),
            # 6. Bind for second child run
            call.bind(
                run_id=mock_child_run2.id,
                run_name=mock_child_run2.name,
                parent_run_id=run_id,
                parent_run_name=mock_run.name,
            ),
            # 7. Error log for second child run
            call.bind().error("Associated child run: {cr!r}", cr=mock_child_run2),
        ]

        # Use assert_has_calls to check if these calls occurred in sequence.
        # Allow extra calls if log level might produce more debug logs.
        mock_logger.assert_has_calls(expected_calls, any_order=False)

        # Optional stricter check: Ensure EXACTLY these calls happened and no others
        # assert calls == expected_calls


class TestScreenAbstractsChainOnEndCb:
    """Tests for screen_abstracts_chain_on_end_cb function."""

    @patch("sr_assistant.app.agents.screening_agents.logger")
    def test_no_outputs_warning(self, mock_logger: MagicMock) -> None:
        """Test warning when run has no outputs."""
        # Create a mock Run object with no outputs
        mock_run = MagicMock()
        mock_run.id = str(uuid.uuid4())
        mock_run.name = "test_run"
        mock_run.outputs = None

        # Call the function
        screen_abstracts_chain_on_end_cb(mock_run)

        # Check that logger.bind and logger.warning were called correctly
        assert mock_logger.bind.called
        # The bound logger should have warning called once
        bound_logger = mock_logger.bind.return_value
        assert bound_logger.warning.called

    @patch("sr_assistant.app.agents.screening_agents.logger")
    def test_no_child_runs(self, mock_logger: MagicMock) -> None:
        """Test case where run has outputs but no child runs."""
        # Create a mock Run object with outputs but no child runs
        mock_run = MagicMock()
        mock_run.id = str(uuid.uuid4())
        mock_run.name = "test_run"
        mock_run.outputs = {"test": "value"}
        mock_run.child_runs = []

        # Call the function
        screen_abstracts_chain_on_end_cb(mock_run)

        # The function should just return without error
        bound_logger = mock_logger.bind.return_value
        assert not bound_logger.error.called

    @patch("sr_assistant.app.agents.screening_agents.logger")
    def test_child_run_with_no_outputs(self, mock_logger: MagicMock) -> None:
        """Test case where child run has no outputs."""
        # Create a mock Run object with outputs and a child run with no outputs
        mock_run = MagicMock()
        mock_run.id = str(uuid.uuid4())
        mock_run.name = "test_run"
        mock_run.outputs = {"test": "value"}

        mock_child_run = MagicMock()
        mock_child_run.id = str(uuid.uuid4())
        mock_child_run.name = "child_run"
        mock_child_run.outputs = None
        mock_child_run.tags = ["map:key:conservative"]

        mock_run.child_runs = [mock_child_run]

        # Call the function
        screen_abstracts_chain_on_end_cb(mock_run)

        # Should log a warning for the child run with no outputs
        bound_logger = mock_logger.bind.return_value
        assert bound_logger.warning.called

    @patch("sr_assistant.app.agents.screening_agents.logger")
    def test_child_run_with_no_tags(self, mock_logger: MagicMock) -> None:
        """Test case where child run has outputs but no tags."""
        # Create a mock Run object with outputs and a child run with outputs but no tags
        mock_run = MagicMock()
        mock_run.id = str(uuid.uuid4())
        mock_run.name = "test_run"
        mock_run.outputs = {"test": "value"}

        mock_child_run = MagicMock()
        mock_child_run.id = str(uuid.uuid4())
        mock_child_run.name = "child_run"
        mock_child_run.outputs = {"output": "value"}
        mock_child_run.tags = None

        mock_run.child_runs = [mock_child_run]

        # Call the function
        screen_abstracts_chain_on_end_cb(mock_run)

        # Should log an error for the child run with no tags
        bound_logger = mock_logger.bind.return_value
        assert bound_logger.error.called
        assert any(
            "No tags for run" in str(call) for call in bound_logger.error.call_args_list
        )

    @patch("sr_assistant.app.agents.screening_agents.logger")
    def test_child_run_with_unknown_output_key(self, mock_logger: MagicMock) -> None:
        """Test case where child run has an unknown output key."""
        # Create a mock Run object with outputs and a child run with an unknown output key
        mock_run = MagicMock()
        mock_run.id = str(uuid.uuid4())
        mock_run.name = "test_run"
        mock_run.outputs = {"test": "value"}

        mock_child_run = MagicMock()
        mock_child_run.id = str(uuid.uuid4())
        mock_child_run.name = "child_run"
        mock_child_run.outputs = {"output": "value"}
        mock_child_run.tags = ["map:key:unknown"]

        mock_run.child_runs = [mock_child_run]

        # Call the function
        screen_abstracts_chain_on_end_cb(mock_run)

        # Should log an error for the child run with unknown output key
        bound_logger = mock_logger.bind.return_value
        assert bound_logger.error.called
        assert any(
            "Unknown output key for run" in str(call)
            for call in bound_logger.error.call_args_list
        )

    @patch("sr_assistant.app.agents.screening_agents.logger")
    def test_child_run_with_unknown_response_type(self, mock_logger: MagicMock) -> None:
        """Test case where child run has an unknown response type."""
        # Create a mock Run object with outputs and a child run with an unknown response type
        mock_run = MagicMock()
        mock_run.id = str(uuid.uuid4())
        mock_run.name = "test_run"
        mock_run.outputs = {"test": "value"}
        mock_run.tags = []

        mock_child_run = MagicMock()
        mock_child_run.id = str(uuid.uuid4())
        mock_child_run.name = "child_run"
        mock_child_run.outputs = {"output": "not a ScreeningResponse"}
        mock_child_run.tags = ["map:key:conservative"]

        mock_run.child_runs = [mock_child_run]

        # Call the function
        screen_abstracts_chain_on_end_cb(mock_run)

        # Should log an error for the child run with unknown response type
        bound_logger = mock_logger.bind.return_value
        assert bound_logger.error.called
        assert any(
            "Unknown response type" in str(call)
            for call in bound_logger.error.call_args_list
        )

    @patch("sr_assistant.app.agents.screening_agents.logger")
    def test_child_run_missing_review_id(self, mock_logger: MagicMock) -> None:
        """Test case where child run metadata is missing review_id."""
        # Create a mock Run object with outputs and a child run with missing review_id
        mock_run = MagicMock()
        mock_run.id = str(uuid.uuid4())
        mock_run.name = "test_run"
        mock_run.outputs = {"test": "value"}
        mock_run.tags = []

        mock_child_run = MagicMock()
        mock_child_run.id = str(uuid.uuid4())
        mock_child_run.name = "child_run"
        mock_child_run.outputs = {"output": MagicMock(spec=ScreeningResponse)}
        mock_child_run.tags = ["map:key:conservative"]
        mock_child_run.metadata = {}

        mock_run.child_runs = [mock_child_run]

        # Call the function
        screen_abstracts_chain_on_end_cb(mock_run)

        # Should log an error for the child run with missing review_id
        bound_logger = mock_logger.bind.return_value
        assert bound_logger.error.called
        assert any(
            "Missing review_id in metadata" in str(call)
            for call in bound_logger.error.call_args_list
        )

    @patch("sr_assistant.app.agents.screening_agents.logger")
    def test_child_run_missing_pubmed_result_id(self, mock_logger: MagicMock) -> None:
        """Test case where child run metadata is missing pubmed_result_id."""
        # Create a mock Run object with outputs and a child run with missing pubmed_result_id
        mock_run = MagicMock()
        mock_run.id = str(uuid.uuid4())
        mock_run.name = "test_run"
        mock_run.outputs = {"test": "value"}
        mock_run.tags = []

        mock_child_run = MagicMock()
        mock_child_run.id = str(uuid.uuid4())
        mock_child_run.name = "child_run"
        mock_child_run.outputs = {"output": MagicMock(spec=ScreeningResponse)}
        mock_child_run.tags = ["map:key:conservative"]
        mock_child_run.metadata = {"review_id": str(uuid.uuid4())}

        mock_run.child_runs = [mock_child_run]

        # Call the function
        screen_abstracts_chain_on_end_cb(mock_run)

        # Should log an error for the child run with missing pubmed_result_id
        bound_logger = mock_logger.bind.return_value
        assert bound_logger.error.called
        assert any(
            "Missing pubmed_result_id in metadata" in str(call)
            for call in bound_logger.error.call_args_list
        )

    @patch("sr_assistant.app.agents.screening_agents.logger")
    def test_successful_processing(self, mock_logger: MagicMock) -> None:
        """Test that the function runs without exceptions for a valid input.

        This test doesn't fully verify the behavior of the function due to the
        complexity of mocking all the components, but it at least ensures the function
        can process a valid input without raising exceptions.
        """
        # Create a mock Run object with all required fields
        run_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())
        review_id = str(uuid.uuid4())
        pubmed_result_id = str(uuid.uuid4())

        # Create mocks with minimum required fields
        mock_run = MagicMock()
        mock_run.outputs = {}
        mock_run.tags = []
        mock_run.child_runs = []

        # Create a minimal child run
        mock_child_run = MagicMock()
        mock_child_run.tags = ["map:key:conservative"]
        mock_child_run.metadata = {
            "review_id": review_id,
            "pubmed_result_id": pubmed_result_id,
        }
        mock_child_run.trace_id = trace_id
        mock_child_run.start_time = datetime.now(timezone.utc)
        mock_child_run.end_time = datetime.now(timezone.utc)
        mock_child_run.inputs = {}

        # Create a mock response
        mock_screening_response = MagicMock(spec=ScreeningResponse)
        mock_child_run.outputs = {"output": mock_screening_response}

        # Create a minimal chat_model child
        mock_ccr = MagicMock()
        mock_ccr.run_type = "chat_model"
        mock_ccr.extra = {"metadata": {}, "invocation_params": {}}
        mock_child_run.child_runs = [mock_ccr]

        # Add child run to run
        mock_run.child_runs = [mock_child_run]

        # The function should run without exceptions
        try:
            screen_abstracts_chain_on_end_cb(mock_run)
            # If we get here, the test passes
            assert True
        except Exception as e:
            # If an exception is raised, the test fails
            assert False, (
                f"screen_abstracts_chain_on_end_cb raised {type(e).__name__}: {e}"
            )
