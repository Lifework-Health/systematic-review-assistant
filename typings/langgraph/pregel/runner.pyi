"""
This type stub file was generated by pyright.
"""

import asyncio
import concurrent.futures
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Iterable,
    Iterator,
    Optional,
    Sequence,
    Union,
)
from langgraph.pregel.algo import Call
from langgraph.pregel.executor import Submit
from langgraph.types import PregelExecutableTask, RetryPolicy

class PregelRunner:
    """Responsible for executing a set of Pregel tasks concurrently, committing
    their writes, yielding control to caller when there is output to emit, and
    interrupting other tasks if appropriate."""
    def __init__(
        self,
        *,
        submit: Submit,
        put_writes: Callable[[str, Sequence[tuple[str, Any]]], None],
        schedule_task: Callable[
            [PregelExecutableTask, int, Optional[Call]], Optional[PregelExecutableTask]
        ],
        use_astream: bool = ...,
        node_finished: Optional[Callable[[str], None]] = ...,
    ) -> None: ...
    def tick(
        self,
        tasks: Iterable[PregelExecutableTask],
        *,
        reraise: bool = ...,
        timeout: Optional[float] = ...,
        retry_policy: Optional[RetryPolicy] = ...,
        get_waiter: Optional[Callable[[], concurrent.futures.Future[None]]] = ...,
    ) -> Iterator[None]: ...
    async def atick(
        self,
        tasks: Iterable[PregelExecutableTask],
        *,
        reraise: bool = ...,
        timeout: Optional[float] = ...,
        retry_policy: Optional[RetryPolicy] = ...,
        get_waiter: Optional[Callable[[], asyncio.Future[None]]] = ...,
    ) -> AsyncIterator[None]: ...
    def commit(
        self,
        task: PregelExecutableTask,
        fut: Union[None, concurrent.futures.Future[Any], asyncio.Future[Any]],
        exception: Optional[BaseException] = ...,
    ) -> None: ...
