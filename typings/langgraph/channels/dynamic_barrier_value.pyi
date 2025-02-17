"""
This type stub file was generated by pyright.
"""

from typing import Any, Generic, NamedTuple, Optional, Sequence, Type, Union
from typing_extensions import Self
from langgraph.channels.base import BaseChannel, Value

class WaitForNames(NamedTuple):
    names: set[Any]
    ...

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
    names: Optional[set[Value]]
    seen: set[Value]
    def __init__(self, typ: Type[Value]) -> None: ...
    def __eq__(self, value: object) -> bool: ...
    @property
    def ValueType(self) -> Type[Value]:
        """The type of the value stored in the channel."""
        ...

    @property
    def UpdateType(self) -> Type[Value]:
        """The type of the update received by the channel."""
        ...

    def checkpoint(self) -> tuple[Optional[set[Value]], set[Value]]: ...
    def from_checkpoint(
        self, checkpoint: Optional[tuple[Optional[set[Value]], set[Value]]]
    ) -> Self: ...
    def update(self, values: Sequence[Union[Value, WaitForNames]]) -> bool: ...
    def get(self) -> Value: ...
    def consume(self) -> bool: ...
