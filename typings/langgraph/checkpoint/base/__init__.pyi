"""
This type stub file was generated by pyright.
"""

from collections.abc import AsyncIterator, Iterator, Mapping, Sequence
from datetime import datetime, timezone
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Literal,
    NamedTuple,
    Optional,
    Tuple,
    TypeVar,
    TypedDict,
    Union,
)
from langchain_core.runnables import ConfigurableFieldSpec, RunnableConfig
from langgraph.checkpoint.base.id import uuid6
from langgraph.checkpoint.serde.base import SerializerProtocol, maybe_add_typed_methods
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.serde.types import (
    ChannelProtocol,
    ERROR,
    INTERRUPT,
    RESUME,
    SCHEDULED,
    SendProtocol,
)

V = TypeVar("V", int, float, str)
PendingWrite = Tuple[str, str, Any]

class CheckpointMetadata(TypedDict, total=False):
    """Metadata associated with a checkpoint."""

    source: Literal["input", "loop", "update", "fork"]
    step: int
    writes: dict[str, Any]
    parents: dict[str, str]
    ...

class TaskInfo(TypedDict):
    status: Literal["scheduled", "success", "error"]
    ...

ChannelVersions = dict[str, Union[str, int, float]]

class Checkpoint(TypedDict):
    """State snapshot at a given point in time."""

    v: int
    id: str
    ts: str
    channel_values: dict[str, Any]
    channel_versions: ChannelVersions
    versions_seen: dict[str, ChannelVersions]
    pending_sends: List[SendProtocol]
    ...

def empty_checkpoint() -> Checkpoint: ...
def copy_checkpoint(checkpoint: Checkpoint) -> Checkpoint: ...
def create_checkpoint(
    checkpoint: Checkpoint,
    channels: Optional[Mapping[str, ChannelProtocol]],
    step: int,
    *,
    id: Optional[str] = ...,
) -> Checkpoint:
    """Create a checkpoint for the given channels."""
    ...

class CheckpointTuple(NamedTuple):
    """A tuple containing a checkpoint and its associated data."""

    config: RunnableConfig
    checkpoint: Checkpoint
    metadata: CheckpointMetadata
    parent_config: Optional[RunnableConfig] = ...
    pending_writes: Optional[List[PendingWrite]] = ...

CheckpointThreadId = ...
CheckpointNS = ...
CheckpointId = ...

class BaseCheckpointSaver(Generic[V]):
    """Base class for creating a graph checkpointer.

    Checkpointers allow LangGraph agents to persist their state
    within and across multiple interactions.

    Attributes:
        serde (SerializerProtocol): Serializer for encoding/decoding checkpoints.

    Note:
        When creating a custom checkpoint saver, consider implementing async
        versions to avoid blocking the main thread.
    """

    serde: SerializerProtocol = ...
    def __init__(self, *, serde: Optional[SerializerProtocol] = ...) -> None: ...
    @property
    def config_specs(self) -> list[ConfigurableFieldSpec]:
        """Define the configuration options for the checkpoint saver.

        Returns:
            list[ConfigurableFieldSpec]: List of configuration field specs.
        """
        ...

    def get(self, config: RunnableConfig) -> Optional[Checkpoint]:
        """Fetch a checkpoint using the given configuration.

        Args:
            config (RunnableConfig): Configuration specifying which checkpoint to retrieve.

        Returns:
            Optional[Checkpoint]: The requested checkpoint, or None if not found.
        """
        ...

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Fetch a checkpoint tuple using the given configuration.

        Args:
            config (RunnableConfig): Configuration specifying which checkpoint to retrieve.

        Returns:
            Optional[CheckpointTuple]: The requested checkpoint tuple, or None if not found.

        Raises:
            NotImplementedError: Implement this method in your custom checkpoint saver.
        """
        ...

    def list(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[Dict[str, Any]] = ...,
        before: Optional[RunnableConfig] = ...,
        limit: Optional[int] = ...,
    ) -> Iterator[CheckpointTuple]:
        """List checkpoints that match the given criteria.

        Args:
            config (Optional[RunnableConfig]): Base configuration for filtering checkpoints.
            filter (Optional[Dict[str, Any]]): Additional filtering criteria.
            before (Optional[RunnableConfig]): List checkpoints created before this configuration.
            limit (Optional[int]): Maximum number of checkpoints to return.

        Returns:
            Iterator[CheckpointTuple]: Iterator of matching checkpoint tuples.

        Raises:
            NotImplementedError: Implement this method in your custom checkpoint saver.
        """
        ...

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Store a checkpoint with its configuration and metadata.

        Args:
            config (RunnableConfig): Configuration for the checkpoint.
            checkpoint (Checkpoint): The checkpoint to store.
            metadata (CheckpointMetadata): Additional metadata for the checkpoint.
            new_versions (ChannelVersions): New channel versions as of this write.

        Returns:
            RunnableConfig: Updated configuration after storing the checkpoint.

        Raises:
            NotImplementedError: Implement this method in your custom checkpoint saver.
        """
        ...

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[Tuple[str, Any]],
        task_id: str,
        task_path: str = ...,
    ) -> None:
        """Store intermediate writes linked to a checkpoint.

        Args:
            config (RunnableConfig): Configuration of the related checkpoint.
            writes (List[Tuple[str, Any]]): List of writes to store.
            task_id (str): Identifier for the task creating the writes.
            task_path (str): Path of the task creating the writes.

        Raises:
            NotImplementedError: Implement this method in your custom checkpoint saver.
        """
        ...

    async def aget(self, config: RunnableConfig) -> Optional[Checkpoint]:
        """Asynchronously fetch a checkpoint using the given configuration.

        Args:
            config (RunnableConfig): Configuration specifying which checkpoint to retrieve.

        Returns:
            Optional[Checkpoint]: The requested checkpoint, or None if not found.
        """
        ...

    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Asynchronously fetch a checkpoint tuple using the given configuration.

        Args:
            config (RunnableConfig): Configuration specifying which checkpoint to retrieve.

        Returns:
            Optional[CheckpointTuple]: The requested checkpoint tuple, or None if not found.

        Raises:
            NotImplementedError: Implement this method in your custom checkpoint saver.
        """
        ...

    async def alist(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[Dict[str, Any]] = ...,
        before: Optional[RunnableConfig] = ...,
        limit: Optional[int] = ...,
    ) -> AsyncIterator[CheckpointTuple]:
        """Asynchronously list checkpoints that match the given criteria.

        Args:
            config (Optional[RunnableConfig]): Base configuration for filtering checkpoints.
            filter (Optional[Dict[str, Any]]): Additional filtering criteria for metadata.
            before (Optional[RunnableConfig]): List checkpoints created before this configuration.
            limit (Optional[int]): Maximum number of checkpoints to return.

        Returns:
            AsyncIterator[CheckpointTuple]: Async iterator of matching checkpoint tuples.

        Raises:
            NotImplementedError: Implement this method in your custom checkpoint saver.
        """
        ...

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Asynchronously store a checkpoint with its configuration and metadata.

        Args:
            config (RunnableConfig): Configuration for the checkpoint.
            checkpoint (Checkpoint): The checkpoint to store.
            metadata (CheckpointMetadata): Additional metadata for the checkpoint.
            new_versions (ChannelVersions): New channel versions as of this write.

        Returns:
            RunnableConfig: Updated configuration after storing the checkpoint.

        Raises:
            NotImplementedError: Implement this method in your custom checkpoint saver.
        """
        ...

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[Tuple[str, Any]],
        task_id: str,
        task_path: str = ...,
    ) -> None:
        """Asynchronously store intermediate writes linked to a checkpoint.

        Args:
            config (RunnableConfig): Configuration of the related checkpoint.
            writes (List[Tuple[str, Any]]): List of writes to store.
            task_id (str): Identifier for the task creating the writes.
            task_path (str): Path of the task creating the writes.

        Raises:
            NotImplementedError: Implement this method in your custom checkpoint saver.
        """
        ...

    def get_next_version(self, current: Optional[V], channel: ChannelProtocol) -> V:
        """Generate the next version ID for a channel.

        Default is to use integer versions, incrementing by 1. If you override, you can use str/int/float versions,
        as long as they are monotonically increasing.

        Args:
            current (Optional[V]): The current version identifier (int, float, or str).
            channel (BaseChannel): The channel being versioned.

        Returns:
            V: The next version identifier, which must be increasing.
        """
        ...

class EmptyChannelError(Exception):
    """Raised when attempting to get the value of a channel that hasn't been updated
    for the first time yet."""

    ...

def get_checkpoint_id(config: RunnableConfig) -> Optional[str]:
    """Get checkpoint ID in a backwards-compatible manner (fallback on thread_ts)."""
    ...

WRITES_IDX_MAP = ...
