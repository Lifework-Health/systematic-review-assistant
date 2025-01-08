"""This type stub file was generated by pyright.
"""

from collections.abc import Callable
from typing import Any

from langgraph.utils.runnable import RunnableSeq

def get_runnable_for_func(func: Callable[..., Any]) -> RunnableSeq: ...

CACHE: dict[Callable[..., Any], RunnableSeq] = ...
