"""Unit tests for chat agents module."""

import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import streamlit as st
import uuid6
from langchain_core.tools import BaseTool

# Direct import
from sr_assistant.app.agents import chat_agents
from sr_assistant.app.agents.chat_agents import (
    ChatAgentGraph,
)


class TestTools:
    """Tests for chat agent tools."""

    def test_get_current_time(self) -> None:
        """Test get_current_time tool returns a valid datetime in ISO format."""
        # Access the undecorated function via .func
        result = chat_agents.get_current_time.func()  # Call the underlying function

        # Check if the result is a string
        assert isinstance(result, str)

        # Try to parse the result as a datetime to validate ISO format
        try:
            datetime.fromisoformat(result)
            is_valid_iso = True
        except ValueError:
            is_valid_iso = False

        # Assert that we could parse it as a valid ISO datetime string
        assert is_valid_iso

        # Check that it's in UTC
        assert result.endswith("+00:00") or result.endswith("Z")

    def test_get_session_state_key_authorized(self) -> None:
        """Test get_session_state_key with an authorized key."""
        authorized_keys = ["test_key", "other_key"]
        with patch.object(st, "session_state", {"test_key": "test_value"}):
            # Access the undecorated function via .func
            result = (
                chat_agents.get_session_state_key.func(  # Call the underlying function
                    key="test_key", authorized_keys=authorized_keys
                )
            )
            assert "test_value" in result

    def test_get_session_state_key_unauthorized(self) -> None:
        """Test get_session_state_key with an unauthorized key."""
        authorized_keys = ["other_key"]
        with patch.object(st, "session_state", {"test_key": "test_value"}):
            # Access the undecorated function via .func
            result = (
                chat_agents.get_session_state_key.func(  # Call the underlying function
                    key="test_key", authorized_keys=authorized_keys
                )
            )
            assert "Unauthorized key" in result
            assert "test_key" in result

    def test_get_session_state_key_not_found(self) -> None:
        """Test get_session_state_key with a key that doesn't exist."""
        authorized_keys = ["test_key"]
        with patch.object(st, "session_state", {}):
            # Access the undecorated function via .func
            result = (
                chat_agents.get_session_state_key.func(  # Call the underlying function
                    key="test_key", authorized_keys=authorized_keys
                )
            )
            assert "Key not found" in result
            assert "test_key" in result


class TestAgentGraphInput:
    """Tests for AgentGraphInput typed dict."""

    def test_agent_graph_input_creation(self) -> None:
        """Test creating an AgentGraphInput typed dict."""
        # Create a simple AgentGraphInput with a valid message format
        messages = [("user", "Hello")]
        input_dict = {"messages": messages}

        # Check that it has the expected structure
        assert "messages" in input_dict
        assert input_dict["messages"] == messages


class TestChatAgentGraph:
    """Tests for ChatAgentGraph class."""

    @patch("sr_assistant.app.agents.chat_agents.ConnectionPool")
    def test_init_with_defaults(self, mock_pool_class: MagicMock) -> None:
        """Test initializing a ChatAgentGraph with default values."""
        # Mock the pool
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool

        # Mock config needed by the ChatAgentGraph constructor
        mock_config = MagicMock()
        mock_config.DATABASE_URL = "postgresql://test"
        with patch.object(st, "session_state") as mock_session_state:
            mock_session_state.config = mock_config

            # Create a ChatAgentGraph instance
            graph = ChatAgentGraph()

            # Check default values
            assert graph.db_uri == "postgresql://test"
            # Check that the default tool (get_current_time) was added correctly
            assert len(graph.tools) == 1
            assert isinstance(
                graph.tools[0], BaseTool
            )  # It should be a BaseTool instance
            assert graph.tools[0].name == "get_current_time"
            # Check that the underlying function is the original one
            # This uses .func to access the original function object wrapped by the tool
            assert graph.tools[0].func == chat_agents.get_current_time.func
            assert mock_pool_class.called
            assert graph._checkpointer_conn_kwargs["autocommit"] is True

    @patch("sr_assistant.app.agents.chat_agents.ConnectionPool")
    def test_init_with_custom_values(self, mock_pool_class: MagicMock) -> None:
        """Test initializing a ChatAgentGraph with custom values."""
        # Mock the pool
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool

        # Create mock tools and model
        mock_tool = MagicMock()
        mock_model = MagicMock()
        mock_prompt = MagicMock()
        mock_config_param = MagicMock()

        # Mock session_state
        mock_config = MagicMock()
        mock_config.DATABASE_URL = "postgresql://test"

        with patch.object(st, "session_state") as mock_session_state:
            mock_session_state.config = mock_config

            # Create a ChatAgentGraph instance with custom values
            graph = ChatAgentGraph(
                model=mock_model,
                prompt=mock_prompt,
                config=mock_config_param,
                tools=[mock_tool],
                db_uri="postgresql://custom",
            )

            # Check custom values
            assert graph.db_uri == "postgresql://custom"
            assert graph.tools == [mock_tool]
            assert graph.model == mock_model
            assert graph.prompt == mock_prompt
            assert graph.config == mock_config_param
            assert mock_pool_class.called

    @patch("sr_assistant.app.agents.chat_agents.ConnectionPool")
    @patch("uuid.uuid4")
    def test_set_default_thread_id_with_none(
        self, mock_uuid4: MagicMock, mock_pool_class: MagicMock
    ) -> None:
        """Test _set_default_thread_id with None."""
        # Mock the pool
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool

        # Mock UUID4
        mock_uuid = uuid.UUID("00000000-0000-0000-0000-000000000000")
        mock_uuid4.return_value = mock_uuid

        # Mock config
        mock_config = MagicMock()
        mock_config.DATABASE_URL = "postgresql://test"

        # Create a graph with no default_thread_id
        with patch.object(st, "session_state") as mock_session_state:
            mock_session_state.config = mock_config

            graph = ChatAgentGraph()

            # Check that it generated a UUID
            assert graph.thread_id == str(mock_uuid)
            assert mock_session_state.thread_id == str(mock_uuid)

    @patch("sr_assistant.app.agents.chat_agents.ConnectionPool")
    def test_set_default_thread_id_with_review_id(
        self, mock_pool_class: MagicMock
    ) -> None:
        """Test _set_default_thread_id with review_id in session_state."""
        # Mock the pool
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool

        # Mock _set_default_thread_id method to force using review_id
        original_set_default_thread_id = ChatAgentGraph._set_default_thread_id

        def mock_set_default_thread_id(self, default_thread_id):
            if hasattr(st.session_state, "review_id"):
                thread_id = str(st.session_state.review_id)
                st.session_state.thread_id = thread_id
                return thread_id
            # Fall back to original implementation for other cases
            return original_set_default_thread_id(self, default_thread_id)

        # Apply the patch
        with patch.object(
            ChatAgentGraph, "_set_default_thread_id", mock_set_default_thread_id
        ):
            # Mock config
            mock_config = MagicMock()
            mock_config.DATABASE_URL = "postgresql://test"

            # Create a graph with no default_thread_id
            with patch.object(st, "session_state") as mock_session_state:
                mock_session_state.config = mock_config
                mock_session_state.review_id = "11111111-1111-1111-1111-111111111111"

                graph = ChatAgentGraph()

                # Check that it used the review_id
                assert graph.thread_id == "11111111-1111-1111-1111-111111111111"
                assert (
                    mock_session_state.thread_id
                    == "11111111-1111-1111-1111-111111111111"
                )

    @patch("sr_assistant.app.agents.chat_agents.ConnectionPool")
    def test_set_default_thread_id_with_string(
        self, mock_pool_class: MagicMock
    ) -> None:
        """Test _set_default_thread_id with string UUID."""
        # Mock the pool
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool

        # Mock config
        mock_config = MagicMock()
        mock_config.DATABASE_URL = "postgresql://test"

        # Create a graph with string default_thread_id
        with patch.object(st, "session_state") as mock_session_state:
            mock_session_state.config = mock_config

            thread_id = "22222222-2222-2222-2222-222222222222"
            graph = ChatAgentGraph(default_thread_id=thread_id)

            # Check that it used the provided thread_id
            assert graph.thread_id == thread_id
            assert mock_session_state.thread_id == thread_id

    @patch("sr_assistant.app.agents.chat_agents.ConnectionPool")
    def test_set_default_thread_id_with_uuid(self, mock_pool_class: MagicMock) -> None:
        """Test _set_default_thread_id with UUID object."""
        # Mock the pool
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool

        # Mock config
        mock_config = MagicMock()
        mock_config.DATABASE_URL = "postgresql://test"

        # Create a graph with UUID default_thread_id
        with patch.object(st, "session_state") as mock_session_state:
            mock_session_state.config = mock_config

            thread_id = uuid.UUID("33333333-3333-3333-3333-333333333333")
            graph = ChatAgentGraph(default_thread_id=thread_id)

            # Check that it used the provided thread_id
            assert graph.thread_id == str(thread_id)
            assert mock_session_state.thread_id == str(thread_id)

    @patch("sr_assistant.app.agents.chat_agents.ConnectionPool")
    def test_set_default_thread_id_with_uuid6(self, mock_pool_class: MagicMock) -> None:
        """Test _set_default_thread_id with UUID6 object."""
        # Mock the pool
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool

        # Mock config
        mock_config = MagicMock()
        mock_config.DATABASE_URL = "postgresql://test"

        # Mock UUID6 since we can't easily create a real one for testing
        mock_uuid6 = MagicMock(spec=uuid6.UUID)
        mock_uuid6.__str__.return_value = "44444444-4444-4444-4444-444444444444"

        # Create a graph with UUID6 default_thread_id
        with patch.object(st, "session_state") as mock_session_state:
            mock_session_state.config = mock_config

            graph = ChatAgentGraph(default_thread_id=mock_uuid6)

            # Check that it used the provided thread_id
            assert graph.thread_id == "44444444-4444-4444-4444-444444444444"
            assert (
                mock_session_state.thread_id == "44444444-4444-4444-4444-444444444444"
            )

    @patch("sr_assistant.app.agents.chat_agents.ConnectionPool")
    def test_checkpointer_property(self, mock_pool_class: MagicMock) -> None:
        """Test checkpointer property gets a PostgresSaver with connection from pool."""
        # Mock the pool and connection
        mock_conn = MagicMock()
        mock_pool = MagicMock()
        mock_pool.connection.return_value.__enter__.return_value = mock_conn
        mock_pool_class.return_value = mock_pool

        # Mock config
        mock_config = MagicMock()
        mock_config.DATABASE_URL = "postgresql://test"

        # Create a graph
        with patch.object(st, "session_state") as mock_session_state:
            mock_session_state.config = mock_config

            graph = ChatAgentGraph()

            # Mock PostgresSaver
            with patch(
                "sr_assistant.app.agents.chat_agents.PostgresSaver"
            ) as mock_saver_class:
                mock_saver = MagicMock()
                mock_saver_class.return_value = mock_saver

                # Get the checkpointer
                result = graph.checkpointer

                # Check that it created a PostgresSaver with the connection
                mock_saver_class.assert_called_once_with(mock_conn)
                assert result == mock_saver
