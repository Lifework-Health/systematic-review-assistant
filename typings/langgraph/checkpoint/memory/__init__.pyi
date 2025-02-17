"""
This type stub file was generated by pyright.
"""

import logging
import os
import pickle
import random
import shutil
from collections import defaultdict
from collections.abc import AsyncIterator, Iterator, Sequence
from contextlib import AbstractAsyncContextManager, AbstractContextManager, ExitStack
from types import TracebackType
from typing import Any, Optional
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    ChannelVersions,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    SerializerProtocol,
    WRITES_IDX_MAP,
    get_checkpoint_id,
)
from langgraph.checkpoint.serde.types import ChannelProtocol, TASKS

logger = ...

class MemorySaver(
    BaseCheckpointSaver[str], AbstractContextManager, AbstractAsyncContextManager
):
    """An in-memory checkpoint saver.

    This checkpoint saver stores checkpoints in memory using a defaultdict.

    Note:
        Only use `MemorySaver` for debugging or testing purposes.
        For production use cases we recommend installing [langgraph-checkpoint-postgres](https://pypi.org/project/langgraph-checkpoint-postgres/) and using `PostgresSaver` / `AsyncPostgresSaver`.

    Args:
        serde (Optional[SerializerProtocol]): The serializer to use for serializing and deserializing checkpoints. Defaults to None.

    Examples:

            import asyncio

            from langgraph.checkpoint.memory import MemorySaver
            from langgraph.graph import StateGraph

            builder = StateGraph(int)
            builder.add_node("add_one", lambda x: x + 1)
            builder.set_entry_point("add_one")
            builder.set_finish_point("add_one")

            memory = MemorySaver()
            graph = builder.compile(checkpointer=memory)
            coro = graph.ainvoke(1, {"configurable": {"thread_id": "thread-1"}})
            asyncio.run(coro)  # Output: 2
    """

    storage: defaultdict[
        str,
        dict[
            str, dict[str, tuple[tuple[str, bytes], tuple[str, bytes], Optional[str]]]
        ],
    ]
    writes: defaultdict[
        tuple[str, str, str],
        dict[tuple[str, int], tuple[str, str, tuple[str, bytes], str]],
    ]
    def __init__(
        self,
        *,
        serde: Optional[SerializerProtocol] = ...,
        factory: type[defaultdict] = ...,
    ) -> None: ...
    def __enter__(self) -> MemorySaver: ...
    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]: ...
    async def __aenter__(self) -> MemorySaver: ...
    async def __aexit__(
        self,
        __exc_type: Optional[type[BaseException]],
        __exc_value: Optional[BaseException],
        __traceback: Optional[TracebackType],
    ) -> Optional[bool]: ...
    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Get a checkpoint tuple from the in-memory storage.

        This method retrieves a checkpoint tuple from the in-memory storage based on the
        provided config. If the config contains a "checkpoint_id" key, the checkpoint with
        the matching thread ID and timestamp is retrieved. Otherwise, the latest checkpoint
        for the given thread ID is retrieved.

        Args:
            config (RunnableConfig): The config to use for retrieving the checkpoint.

        Returns:
            Optional[CheckpointTuple]: The retrieved checkpoint tuple, or None if no matching checkpoint was found.
        """
        ...

    def list(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[dict[str, Any]] = ...,
        before: Optional[RunnableConfig] = ...,
        limit: Optional[int] = ...,
    ) -> Iterator[CheckpointTuple]:
        """List checkpoints from the in-memory storage.

        This method retrieves a list of checkpoint tuples from the in-memory storage based
        on the provided criteria.

        Args:
            config (Optional[RunnableConfig]): Base configuration for filtering checkpoints.
            filter (Optional[Dict[str, Any]]): Additional filtering criteria for metadata.
            before (Optional[RunnableConfig]): List checkpoints created before this configuration.
            limit (Optional[int]): Maximum number of checkpoints to return.

        Yields:
            Iterator[CheckpointTuple]: An iterator of matching checkpoint tuples.
        """
        ...

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Save a checkpoint to the in-memory storage.

        This method saves a checkpoint to the in-memory storage. The checkpoint is associated
        with the provided config.

        Args:
            config (RunnableConfig): The config to associate with the checkpoint.
            checkpoint (Checkpoint): The checkpoint to save.
            metadata (CheckpointMetadata): Additional metadata to save with the checkpoint.
            new_versions (dict): New versions as of this write

        Returns:
            RunnableConfig: The updated config containing the saved checkpoint's timestamp.
        """
        ...

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = ...,
    ) -> None:
        """Save a list of writes to the in-memory storage.

        This method saves a list of writes to the in-memory storage. The writes are associated
        with the provided config.

        Args:
            config (RunnableConfig): The config to associate with the writes.
            writes (list[tuple[str, Any]]): The writes to save.
            task_id (str): Identifier for the task creating the writes.
            task_path (str): Path of the task creating the writes.

        Returns:
            RunnableConfig: The updated config containing the saved writes' timestamp.
        """
        ...

    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Asynchronous version of get_tuple.

        This method is an asynchronous wrapper around get_tuple that runs the synchronous
        method in a separate thread using asyncio.

        Args:
            config (RunnableConfig): The config to use for retrieving the checkpoint.

        Returns:
            Optional[CheckpointTuple]: The retrieved checkpoint tuple, or None if no matching checkpoint was found.
        """
        ...

    async def alist(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[dict[str, Any]] = ...,
        before: Optional[RunnableConfig] = ...,
        limit: Optional[int] = ...,
    ) -> AsyncIterator[CheckpointTuple]:
        """Asynchronous version of list.

        This method is an asynchronous wrapper around list that runs the synchronous
        method in a separate thread using asyncio.

        Args:
            config (RunnableConfig): The config to use for listing the checkpoints.

        Yields:
            AsyncIterator[CheckpointTuple]: An asynchronous iterator of checkpoint tuples.
        """
        ...

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Asynchronous version of put.

        Args:
            config (RunnableConfig): The config to associate with the checkpoint.
            checkpoint (Checkpoint): The checkpoint to save.
            metadata (CheckpointMetadata): Additional metadata to save with the checkpoint.
            new_versions (dict): New versions as of this write

        Returns:
            RunnableConfig: The updated config containing the saved checkpoint's timestamp.
        """
        ...

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = ...,
    ) -> None:
        """Asynchronous version of put_writes.

        This method is an asynchronous wrapper around put_writes that runs the synchronous
        method in a separate thread using asyncio.

        Args:
            config (RunnableConfig): The config to associate with the writes.
            writes (List[Tuple[str, Any]]): The writes to save, each as a (channel, value) pair.
            task_id (str): Identifier for the task creating the writes.
            task_path (str): Path of the task creating the writes.

        Returns:
            None
        """
        ...

    def get_next_version(
        self, current: Optional[str], channel: ChannelProtocol
    ) -> str: ...

class PersistentDict(defaultdict):
    """Persistent dictionary with an API compatible with shelve and anydbm.

    The dict is kept in memory, so the dictionary operations run as fast as
    a regular dictionary.

    Write to disk is delayed until close or sync (similar to gdbm's fast mode).

    Input file format is automatically discovered.
    Output file format is selectable between pickle, json, and csv.
    All three serialization formats are backed by fast C implementations.

    Adapted from https://code.activestate.com/recipes/576642-persistent-dict-with-multiple-standard-file-format/

    """
    def __init__(self, *args: Any, filename: str, **kwds: Any) -> None: ...
    def sync(self) -> None:
        "Write dict to disk"
        ...

    def close(self) -> None: ...
    def __enter__(self) -> PersistentDict: ...
    def __exit__(self, *exc_info: Any) -> None: ...
    def dump(self, fileobj: Any) -> None: ...
    def load(self) -> None: ...
