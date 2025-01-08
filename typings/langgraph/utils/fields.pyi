"""This type stub file was generated by pyright.
"""

from collections.abc import Generator
from typing import Any

_DEFAULT_KEYS: frozenset[str] = ...

def get_field_default(name: str, type_: Any, schema: type[Any]) -> Any:
    """Determine the default value for a field in a state schema.

    This is based on:
        If TypedDict:
            - Required/NotRequired
            - total=False -> everything optional
        - Type annotation (Optional/Union[None])
    """

def get_enhanced_type_hints(
    type: type[Any],
) -> Generator[tuple[str, Any, Any, str | None], None, None]:
    """Attempt to extract default values and descriptions from provided type, used for config schema."""