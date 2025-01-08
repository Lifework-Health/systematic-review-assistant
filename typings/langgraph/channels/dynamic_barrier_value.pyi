"""This type stub file was generated by pyright.
"""

from collections.abc import Sequence
from typing import Any, Generic, NamedTuple, Self, Union

from langgraph.channels.base import BaseChannel, Value

class WaitForNames(NamedTuple):
    names: set[Any]

class DynamicBarrierValue(
    Generic[Value], BaseChannel[Value, Union[Value, WaitForNames], set[Value]]
):
    """A channel that switches between two states

    - in the "priming" state it can't be read from.
        - if it receives a WaitForNames update, it switches to the "waiting" state.
    - in the "waiting" state it collects named values until all are received.
        - once all named values are received, it can be read once, and it switches
          back to the "priming" state.
    """

    __slots__ = ...
    names: set[Value] | None
    seen: set[Value]
    def __init__(self, typ: type[Value]) -> None: ...
    def __eq__(self, value: object) -> bool: ...
    @property
    def ValueType(self) -> type[Value]:
        """The type of the value stored in the channel."""

    @property
    def UpdateType(self) -> type[Value]:
        """The type of the update received by the channel."""

    def checkpoint(self) -> tuple[set[Value] | None, set[Value]]: ...
    def from_checkpoint(
        self, checkpoint: tuple[set[Value] | None, set[Value]] | None
    ) -> Self: ...
    def update(self, values: Sequence[Value | WaitForNames]) -> bool: ...
    def get(self) -> Value: ...
    def consume(self) -> bool: ...