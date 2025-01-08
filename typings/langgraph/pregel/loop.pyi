"""This type stub file was generated by pyright.
"""

import concurrent.futures
from collections.abc import Callable, Mapping, Sequence
from types import TracebackType
from typing import (
    Any,
    AsyncContextManager,
    ContextManager,
    Literal,
    Self,
    TypeVar,
)

from langchain_core.callbacks import AsyncParentRunManager, ParentRunManager
from langchain_core.runnables import RunnableConfig
from langgraph.channels.base import BaseChannel
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    ChannelVersions,
    Checkpoint,
    CheckpointMetadata,
    PendingWrite,
)
from langgraph.managed.base import ManagedValueMapping, ManagedValueSpec
from langgraph.pregel.algo import Call, GetNextVersion
from langgraph.pregel.executor import Submit
from langgraph.pregel.read import PregelNode
from langgraph.store.base import BaseStore
from langgraph.types import All, LoopProtocol, PregelExecutableTask, StreamProtocol
from typing_extensions import ParamSpec

V = TypeVar("V")
P = ParamSpec("P")
INPUT_DONE = ...
INPUT_RESUMING = ...
SPECIAL_CHANNELS = ...

def DuplexStream(*streams: StreamProtocol) -> StreamProtocol: ...

class PregelLoop(LoopProtocol):
    input: Any | None
    checkpointer: BaseCheckpointSaver | None
    nodes: Mapping[str, PregelNode]
    specs: Mapping[str, BaseChannel | ManagedValueSpec]
    output_keys: str | Sequence[str]
    stream_keys: str | Sequence[str]
    skip_done_tasks: bool
    is_nested: bool
    manager: None | AsyncParentRunManager | ParentRunManager
    interrupt_after: All | Sequence[str]
    interrupt_before: All | Sequence[str]
    checkpointer_get_next_version: GetNextVersion
    checkpointer_put_writes: Callable[[RunnableConfig, Sequence[tuple[str, Any]], str], Any] | None
    _checkpointer_put_after_previous: Callable[[concurrent.futures.Future | None, RunnableConfig, Sequence[tuple[str, Any]], str, ChannelVersions], Any] | None
    submit: Submit
    channels: Mapping[str, BaseChannel]
    managed: ManagedValueMapping
    checkpoint: Checkpoint
    checkpoint_ns: tuple[str, ...]
    checkpoint_config: RunnableConfig
    checkpoint_metadata: CheckpointMetadata
    checkpoint_pending_writes: list[PendingWrite]
    checkpoint_previous_versions: dict[str, str | float | int]
    prev_checkpoint_config: RunnableConfig | None
    status: Literal[
        "pending", "done", "interrupt_before", "interrupt_after", "out_of_steps"
    ]
    tasks: dict[str, PregelExecutableTask]
    to_interrupt: list[PregelExecutableTask]
    output: None | dict[str, Any] | Any = ...
    def __init__(
        self,
        input: Any | None,
        *,
        stream: StreamProtocol | None,
        config: RunnableConfig,
        store: BaseStore | None,
        checkpointer: BaseCheckpointSaver | None,
        nodes: Mapping[str, PregelNode],
        specs: Mapping[str, BaseChannel | ManagedValueSpec],
        output_keys: str | Sequence[str],
        stream_keys: str | Sequence[str],
        interrupt_after: All | Sequence[str] = ...,
        interrupt_before: All | Sequence[str] = ...,
        manager: None | AsyncParentRunManager | ParentRunManager = ...,
        check_subgraphs: bool = ...,
        debug: bool = ...,
    ) -> None: ...
    def put_writes(self, task_id: str, writes: Sequence[tuple[str, Any]]) -> None:
        """Put writes for a task, to be read by the next tick."""

    def accept_push(
        self, task: PregelExecutableTask, write_idx: int, call: Call | None = ...
    ) -> PregelExecutableTask | None:
        """Accept a PUSH from a task, potentially returning a new task to start."""

    def tick(self, *, input_keys: str | Sequence[str]) -> bool:
        """Execute a single iteration of the Pregel loop.
        Returns True if more iterations are needed.
        """

class SyncPregelLoop(PregelLoop, ContextManager):
    def __init__(
        self,
        input: Any | None,
        *,
        stream: StreamProtocol | None,
        config: RunnableConfig,
        store: BaseStore | None,
        checkpointer: BaseCheckpointSaver | None,
        nodes: Mapping[str, PregelNode],
        specs: Mapping[str, BaseChannel | ManagedValueSpec],
        manager: None | AsyncParentRunManager | ParentRunManager = ...,
        interrupt_after: All | Sequence[str] = ...,
        interrupt_before: All | Sequence[str] = ...,
        output_keys: str | Sequence[str] = ...,
        stream_keys: str | Sequence[str] = ...,
        check_subgraphs: bool = ...,
        debug: bool = ...,
    ) -> None: ...
    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...

class AsyncPregelLoop(PregelLoop, AsyncContextManager):
    def __init__(
        self,
        input: Any | None,
        *,
        stream: StreamProtocol | None,
        config: RunnableConfig,
        store: BaseStore | None,
        checkpointer: BaseCheckpointSaver | None,
        nodes: Mapping[str, PregelNode],
        specs: Mapping[str, BaseChannel | ManagedValueSpec],
        interrupt_after: All | Sequence[str] = ...,
        interrupt_before: All | Sequence[str] = ...,
        manager: None | AsyncParentRunManager | ParentRunManager = ...,
        output_keys: str | Sequence[str] = ...,
        stream_keys: str | Sequence[str] = ...,
        check_subgraphs: bool = ...,
        debug: bool = ...,
    ) -> None: ...
    async def __aenter__(self) -> Self: ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...
