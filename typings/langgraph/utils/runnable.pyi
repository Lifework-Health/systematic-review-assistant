"""
This type stub file was generated by pyright.
"""

import enum
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Iterator,
    Optional,
    Sequence,
    Union,
)
from langchain_core.runnables.base import Runnable, RunnableConfig, RunnableLike
from langchain_core.runnables.utils import Input
from typing_extensions import TypeGuard

class StrEnum(str, enum.Enum):
    """A string enum."""

    ...

ASYNCIO_ACCEPTS_CONTEXT = ...
KWARGS_CONFIG_KEYS: tuple[tuple[str, tuple[Any, ...], str, Any], ...] = ...
VALID_KINDS = ...

class RunnableCallable(Runnable):
    """A much simpler version of RunnableLambda that requires sync and async functions."""
    def __init__(
        self,
        func: Optional[Callable[..., Union[Any, Runnable]]],
        afunc: Optional[Callable[..., Awaitable[Union[Any, Runnable]]]] = ...,
        *,
        name: Optional[str] = ...,
        tags: Optional[Sequence[str]] = ...,
        trace: bool = ...,
        recurse: bool = ...,
        **kwargs: Any,
    ) -> None: ...
    def __repr__(self) -> str: ...
    def invoke(
        self, input: Any, config: Optional[RunnableConfig] = ..., **kwargs: Any
    ) -> Any: ...
    async def ainvoke(
        self, input: Any, config: Optional[RunnableConfig] = ..., **kwargs: Any
    ) -> Any: ...

def is_async_callable(func: Any) -> TypeGuard[Callable[..., Awaitable]]:
    """Check if a function is async."""
    ...

def is_async_generator(func: Any) -> TypeGuard[Callable[..., AsyncIterator]]:
    """Check if a function is an async generator."""
    ...

def coerce_to_runnable(
    thing: RunnableLike, *, name: Optional[str], trace: bool
) -> Runnable:
    """Coerce a runnable-like object into a Runnable.

    Args:
        thing: A runnable-like object.

    Returns:
        A Runnable.
    """
    ...

class RunnableSeq(Runnable):
    """A simpler version of RunnableSequence."""
    def __init__(self, *steps: RunnableLike, name: Optional[str] = ...) -> None:
        """Create a new RunnableSequence.

        Args:
            steps: The steps to include in the sequence.
            name: The name of the Runnable. Defaults to None.
            first: The first Runnable in the sequence. Defaults to None.
            middle: The middle Runnables in the sequence. Defaults to None.
            last: The last Runnable in the sequence. Defaults to None.

        Raises:
            ValueError: If the sequence has less than 2 steps.
        """
        ...

    def __or__(self, other: Any) -> Runnable: ...
    def __ror__(self, other: Any) -> Runnable: ...
    def invoke(
        self, input: Input, config: Optional[RunnableConfig] = ..., **kwargs: Any
    ) -> Any: ...
    async def ainvoke(
        self,
        input: Input,
        config: Optional[RunnableConfig] = ...,
        **kwargs: Optional[Any],
    ) -> Any: ...
    def stream(
        self,
        input: Input,
        config: Optional[RunnableConfig] = ...,
        **kwargs: Optional[Any],
    ) -> Iterator[Any]: ...
    async def astream(
        self,
        input: Input,
        config: Optional[RunnableConfig] = ...,
        **kwargs: Optional[Any],
    ) -> AsyncIterator[Any]: ...
