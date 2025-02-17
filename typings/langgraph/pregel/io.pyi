"""
This type stub file was generated by pyright.
"""

from typing import Any, Iterator, Literal, Mapping, Optional, Sequence, TypeVar, Union
from langchain_core.runnables.utils import AddableDict
from langgraph.channels.base import BaseChannel
from langgraph.checkpoint.base import PendingWrite
from langgraph.types import Command, PregelExecutableTask

def is_task_id(task_id: str) -> bool:
    """Check if a string is a valid task id."""
    ...

def read_channel(
    channels: Mapping[str, BaseChannel],
    chan: str,
    *,
    catch: bool = ...,
    return_exception: bool = ...,
) -> Any: ...
def read_channels(
    channels: Mapping[str, BaseChannel],
    select: Union[Sequence[str], str],
    *,
    skip_empty: bool = ...,
) -> Union[dict[str, Any], Any]: ...
def map_command(
    cmd: Command, pending_writes: list[PendingWrite]
) -> Iterator[tuple[str, str, Any]]:
    """Map input chunk to a sequence of pending writes in the form (channel, value)."""
    ...

def map_input(
    input_channels: Union[str, Sequence[str]],
    chunk: Optional[Union[dict[str, Any], Any]],
) -> Iterator[tuple[str, Any]]:
    """Map input chunk to a sequence of pending writes in the form (channel, value)."""
    ...

class AddableValuesDict(AddableDict):
    def __add__(self, other: dict[str, Any]) -> AddableValuesDict: ...
    def __radd__(self, other: dict[str, Any]) -> AddableValuesDict: ...

def map_output_values(
    output_channels: Union[str, Sequence[str]],
    pending_writes: Union[Literal[True], Sequence[tuple[str, Any]]],
    channels: Mapping[str, BaseChannel],
) -> Iterator[Union[dict[str, Any], Any]]:
    """Map pending writes (a sequence of tuples (channel, value)) to output chunk."""
    ...

class AddableUpdatesDict(AddableDict):
    def __add__(self, other: dict[str, Any]) -> AddableUpdatesDict: ...
    def __radd__(self, other: dict[str, Any]) -> AddableUpdatesDict: ...

def map_output_updates(
    output_channels: Union[str, Sequence[str]],
    tasks: list[tuple[PregelExecutableTask, Sequence[tuple[str, Any]]]],
    cached: bool = ...,
) -> Iterator[dict[str, Union[Any, dict[str, Any]]]]:
    """Map pending writes (a sequence of tuples (channel, value)) to output chunk."""
    ...

T = TypeVar("T")

def single(iter: Iterator[T]) -> Optional[T]: ...
