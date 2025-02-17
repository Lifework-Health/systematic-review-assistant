"""
This type stub file was generated by pyright.
"""

from typing import Generic, Optional, Sequence, Type
from typing_extensions import Self
from langgraph.channels.base import BaseChannel, Value

class NamedBarrierValue(Generic[Value], BaseChannel[Value, Value, set[Value]]):
    """A channel that waits until all named values are received before making the value available."""

    __slots__ = ...
    names: set[Value]
    seen: set[Value]
    def __init__(self, typ: Type[Value], names: set[Value]) -> None: ...
    def __eq__(self, value: object) -> bool: ...
    @property
    def ValueType(self) -> Type[Value]:
        """The type of the value stored in the channel."""
        ...

    @property
    def UpdateType(self) -> Type[Value]:
        """The type of the update received by the channel."""
        ...

    def checkpoint(self) -> set[Value]: ...
    def from_checkpoint(self, checkpoint: Optional[set[Value]]) -> Self: ...
    def update(self, values: Sequence[Value]) -> bool: ...
    def get(self) -> Value: ...
    def consume(self) -> bool: ...
