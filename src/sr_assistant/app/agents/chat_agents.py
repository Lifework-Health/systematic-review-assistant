"""Streamlit chat UI agent(s)."""

from __future__ import annotations

import typing as t
import uuid
from collections.abc import AsyncGenerator, Callable, Sequence
from datetime import datetime, timezone

import streamlit as st
import uuid6
from langchain_core.language_models import LanguageModelLike
from langchain_core.messages import (
    AIMessageChunk,
    BaseMessage,
    BaseMessageChunk,
    MessageLikeRepresentation,
    SystemMessage,
)
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.tools import BaseTool, tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.prebuilt.chat_agent_executor import (  # pyright: ignore [reportMissingTypeStubs]
    AgentState,
    create_react_agent,
)
from loguru import logger
from psycopg_pool import AsyncConnectionPool, ConnectionPool

if t.TYPE_CHECKING:
    from langgraph.graph.graph import CompiledGraph

# These are improved LangGraph types as originals cause type errors
# Ref: https://github.com/langchain-ai/langgraph/blob/9fe61a42d2bf63c4ba4a94de71e6e8016729a951/libs/langgraph/langgraph/prebuilt/chat_agent_executor.py#L46C1-L53C36

# This is the graph state, i.e. what tracks node return values
# See the above link for the required keys, additional ones can be added
StateSchema_co = t.TypeVar("StateSchema_co", bound=AgentState, covariant=True)
type StateSchemaType[StateSchema_co] = type[StateSchema_co]

# LangGraph agent prompts are flexible
type GraphAgentPrompt[StateSchema_co] = (
    SystemMessage
    | str
    | Callable[[StateSchema_co], Sequence[BaseMessage]]
    | Runnable[StateSchema_co, Sequence[BaseMessage]]
)
"""Can take a few different forms:

- str: This is converted to a SystemMessage and added to the beginning of the list of messages in state["messages"].
- SystemMessage: this is added to the beginning of the list of messages in state["messages"].
- Callable: This function should take in full graph state and the output is then passed to the language model.
- Runnable: This runnable should take in full graph state and the output is then passed to the language model.
    E.g., a ChatPromptTemplate.

Example:
    >>> from typing import TypedDict
    >>>
    >>> from langgraph.managed import IsLastStep
    >>> from langgraph.prebuilt.chat_agent_executor import AgentState
    >>> prompt = ChatPromptTemplate.from_messages(
    ...     [
    ...         ("system", "Today is {today}"),
    ...         ("placeholder", "{messages}"),
    ...     ]
    ... )
    >>>
    >>> class CustomState(AgentState):
    ...     today: str
    >>>
    >>> graph = create_react_agent(model, tools, state_schema=CustomState, prompt=prompt)
    >>> inputs = {"messages": [("user", "What's today's date? And what's the weather in SF?")], "today": "July 16, 2004"}
    >>> for s in graph.stream(inputs, stream_mode="values"):
    ...     message = s["messages"][-1]
    ...     if isinstance(message, tuple):
    ...         print(message)
    ...     else:
    ...         message.pretty_print()
"""  # noqa: W505


class AgentGraphInput(t.TypedDict):
    """Input dict to a LangGraph agent.

    If the graph is using a checkpointer passing only one new message is fine. If not,
    you should pass a list of messages as a chat history.

    Attributes:
        messages (list[MessageLikeRepresentation]): list of LangChain message
            representations.

    Note:
        MessageLikeRepresentation = Union[
            BaseMessage, List[str], Tuple[str, str], str, Dict[str, Any]
        ]

    See Also:
        `langchain_core.messages.utils source <https://api.python.langchain.com/en/latest/_modules/langchain_core/messages/utils.html>`_
    """

    messages: list[MessageLikeRepresentation]


# LangGraph ReAct agent we use takes a system message
# directly as a prompt. It does support templates but
# they're more work for little gain in our use case.
#
# Its chat history and full record of every message
# is persisted in Postgres and can be used to construct
# audit trails or to better understand how AI is used
# in the project.
#
# The graph state handles chat history automatically.
# This message will simply be the first in state["messages"].
chat_assistant_system_prompt_1 = SystemMessage(
    content="""\
You're' a helpful systematic review expert assisting in developing \
a cutting-edge AI-driven systematic review platform and operating it.

## Responsibilities

You're required to review and grade every step of the process \
ensuring the highest standards. For example, you'll be asked to \
assist in developing the review protoco including developing \
PICO, etc. using FINER.

Likewise you'll assist with the search strategy helping to \
leverage query expansion and block building. The system \
leverages an ensemble LLM approach to screening, so you \
won't be directly involved in screening but may be asked to \
evaluate prompts and grade LLM responses.

You're equipped with a permanent memory that lasts for the \
duration of a given systematic review: your memory is \
keyed by the review ID. As such expect to be assigned \
a wide variety of tasks which may change over time and often."""
)


# create_react_agent requires tools but is the simplest way
# to get started with a good graph quickly, so we create a
# simple tools.
@tool
def get_current_time() -> str:
    """Returns current time and date in UTC."""
    return datetime.now(tz=timezone.utc).isoformat()


# TODO: hide authorized_keys from model
@tool
def get_session_state_key(key: str, authorized_keys: list[str] | None = None) -> t.Any:
    """Returns the value associated with the given key if it exists in the session state.

    Otherwise, returns an error message.
    """
    if key not in (authorized_keys or []):
        return f"Unauthorized key (tell the human!): {key}"
    if key not in st.session_state:
        return f"Key not found in session state (tell the human!): {key}"
    return f"st.session_state[{key}]: {st.session_state[key]}"


class ChatAgentGraph:
    """LangGraph agent wrapper."""

    def __init__(
        self,
        model: LanguageModelLike | None = None,
        prompt: GraphAgentPrompt[StateSchema_co] = chat_assistant_system_prompt_1,
        *,
        config: RunnableConfig | None = None,
        tools: list[BaseTool] | None = None,
        db_uri: str | None = None,
        default_thread_id: str | uuid.UUID | uuid6.UUID | None = None,
    ) -> None:
        # Set db_uri from session_state only if not provided
        if db_uri is None:
            try:
                db_uri = st.session_state.config.DATABASE_URL
            except AttributeError:
                # Handle cases where config or DATABASE_URL might be missing
                # Or raise a more specific error if it's always expected
                logger.error(
                    "DATABASE_URL not found in st.session_state.config during ChatAgentGraph init."
                )
                # Depending on requirements, you might raise an error or set a fallback default
                raise ValueError(
                    "DATABASE_URL must be configured in session_state.config or passed explicitly."
                )

        self.prompt = prompt
        # Assign default tool if tools is None
        self.tools = tools if tools is not None else [get_current_time]
        self.db_uri = db_uri
        self.model = model or ChatOpenAI(
            model="gpt-4o", temperature=0, tags=["sr_assistant:prototype"]
        )
        self.config = config
        self.thread_id = self._set_default_thread_id(default_thread_id)
        self._checkpointer_conn_kwargs = {
            "autocommit": True,
            "prepare_threshold": 0,
        }
        # Ensure db_uri is not None before creating the pool
        if self.db_uri is None:
            raise ValueError("Database URI could not be determined.")
        self.pool = ConnectionPool(
            conninfo=self.db_uri,
            max_size=20,
            kwargs=self._checkpointer_conn_kwargs,
        )
        self.latest_checkpoint = None

    @property
    def checkpointer(self) -> PostgresSaver:
        with self.pool.connection() as conn:
            return PostgresSaver(conn)

    def _set_default_thread_id(
        self, default_thread_id: str | uuid.UUID | uuid6.UUID | None
    ) -> str:
        if isinstance(default_thread_id, (uuid.UUID | uuid6.UUID)):
            default_thread_id = str(default_thread_id)
        if not default_thread_id:
            if "review_id" in st.session_state:
                default_thread_id = str(st.session_state.review_id)
            else:
                default_thread_id = str(uuid.uuid4())
        else:
            default_thread_id = str(default_thread_id)
        st.session_state.thread_id = str(default_thread_id)
        return st.session_state.thread_id  # pyright: ignore [reportReturnType]


# This needs refactoring and isn't used currently
async def ainvoke_chat_agent(
    messages: AgentGraphInput,
    prompt: GraphAgentPrompt[StateSchema_co] = chat_assistant_system_prompt_1,
    *,
    tools: list[BaseTool] | None = None,
    db_uri: str | None = None,
    thread_id: str | uuid.UUID | None = None,
) -> AsyncGenerator[BaseMessageChunk]:
    """Systematic Review chat assistant in Streamlit UI.

    The agent graph looks like this:

    ``` mermaid
    stateDiagram-v2
        [*] --> Start
        Start --> Agent
        Agent --> Tools : continue
        Tools --> Agent
        Agent --> End : end
        End --> [*]

        classDef startClass fill:#ffdfba;
        classDef endClass fill:#baffc9;
        classDef otherClass fill:#fad7de;

        class Start startClass
        class End endClass
        class Agent,Tools otherClass
    ```

    See Also:
        `create_react_agent source <https://github.com/langchain-ai/langgraph/blob/9fe61a42d2bf63c4ba4a94de71e6e8016729a951/libs/langgraph/langgraph/prebuilt/chat_agent_executor.py#L237>`_

    Todo:
        - Turn to a class, simplify uses, helpers for steamlit chat
        - invocation should require only passing one humanmessage
        - How to make this proper async considering Streamllit?
          - loop executor for graph invocation? checkpointer already
            uses executor. concur futures would be better but this
            is all async for many reasons.
        - Should be split into reusable base class/components
          since reading all docs and configuring everythihng takes
          time and we may want to use this for screening and
          past the prototype (currently simple chains for that)
        - methods for working with checkpointer, doing restores, etc.
        - Tools: access Streamlit UIs so it can write for users,
          e.g., PICO from question, etc. guess this means wrapping session state,
          unclear how to write to non-form widgets. Instantiate in st.empty and replace?
        - Tools: Entrez pubmed query gen/expansion, or maybe this shouldn't be a tool,
            too slow?
        - Tools: MeSH etc. autocomplete with Entrez and LLM
        - Tools to query PG and help with e.g. PRISMA
          and data extraction tasks
        - Tools to help analyze screeening results (see LC Pandas agent, convert to
          graph).
        - Tool to screen for duplicates, e.g., embeddings or shouldn't be a tool
        - Tools to analyze and assist with protocol and search strategy.
    """
    if isinstance(thread_id, (uuid.UUID | uuid6.UUID)):
        thread_id = str(thread_id)
    if not thread_id:
        if "review_id" in st.session_state:
            # TODO: This means chat history is shared throughout the review, do we want that?
            #       It is explained in system prompt though ... and was intentional.
            #       Pages could also create IDs or have convention in st.session_state.
            thread_id = str(st.session_state.review_id)
        else:
            thread_id = str(uuid.uuid4())
    if not db_uri:
        db_uri = st.session_state.config.DATABASE_URL
        if not db_uri:
            msg = "No DATABASE_URL in st.session_state.config"
            logger.error(msg)
            raise ValueError(msg)
    if not tools:
        tools = [get_current_time]
    model = ChatOpenAI(model="gpt-4o", temperature=0)
    connection_kwargs = {
        "autocommit": True,
        "prepare_threshold": 0,
    }
    async with AsyncConnectionPool(
        conninfo=db_uri,
        max_size=20,
        kwargs=connection_kwargs,
    ) as pool:
        checkpointer = AsyncPostgresSaver(pool)  # type: ignore
        # Uses AgentState
        graph: CompiledGraph = create_react_agent(
            prompt=prompt, model=model, tools=tools, checkpointer=checkpointer
        )
        config = RunnableConfig(
            configurable={"thread_id": thread_id},
            recursion_limit=1000,
            run_name="sra:chat:react-agent",
            tags=["sr_assistant:prototype", "step1", "step2", "step3", "streamlit"],
            max_concurrency=50,
        )
        # StreamEvent:
        #'event': 'on_chat_model_stream',
        # 'name': 'ChatOpenAI',
        # 'run_id': '3fdbf494-acce-402e-9b50-4eab46403859',
        # 'tags': ['seq:step:1'],
        # 'metadata': {'langgraph_step': 1,
        #  'langgraph_node': 'call_model',
        #  'langgraph_triggers': ['start:call_model'],
        #  'langgraph_task_idx': 0,
        #  'checkpoint_id': '1ef657a0-0f9d-61b8-bffe-0c39e4f9ad6c',
        #  'checkpoint_ns': 'call_model',
        #  'ls_provider': 'openai',
        #  'ls_model_name': 'gpt-4o-mini',
        #  'ls_model_type': 'chat',
        #  'ls_temperature': 0.7},
        # 'data': {'chunk': AIMessageChunk(content='Hello', id='run-3fdbf494-acce-402e-9b50-4eab46403859')},
        # 'parent_ids': []}
        async for event in graph.astream_events(messages, config=config, version="v2"):
            kind = event["event"]
            logger.info(f"{kind!r}: {event['name']!r}")
            logger.debug(f"StreamEvent: {event!r}")
            if kind == "on_chat_model_stream":
                yield event["data"].get(
                    "chunk", AIMessageChunk(content="")
                )  #  langchain_core.runnables.schema.StreamEvent

        # TODO: do something with this, accept a session state key as param? at least
        # have a property in the class?
        await checkpointer.aget(config)
