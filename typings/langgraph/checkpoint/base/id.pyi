"""
This type stub file was generated by pyright.
"""

import uuid
from typing import Optional, Tuple

"""Adapted from
https://github.com/oittaa/uuid6-python/blob/main/src/uuid6/__init__.py#L95
Bundled in to avoid install issues with uuid6 package
"""
_last_v6_timestamp = ...

class UUID(uuid.UUID):
    r"""UUID draft version objects"""

    __slots__ = ...
    def __init__(
        self,
        hex: Optional[str] = ...,
        bytes: Optional[bytes] = ...,
        bytes_le: Optional[bytes] = ...,
        fields: Optional[Tuple[int, int, int, int, int, int]] = ...,
        int: Optional[int] = ...,
        version: Optional[int] = ...,
        *,
        is_safe: uuid.SafeUUID = ...,
    ) -> None:
        r"""Create a UUID."""
        ...

    @property
    def subsec(self) -> int: ...
    @property
    def time(self) -> int: ...

def uuid6(node: Optional[int] = ..., clock_seq: Optional[int] = ...) -> UUID:
    r"""UUID version 6 is a field-compatible version of UUIDv1, reordered for
    improved DB locality. It is expected that UUIDv6 will primarily be
    used in contexts where there are existing v1 UUIDs. Systems that do
    not involve legacy UUIDv1 SHOULD consider using UUIDv7 instead.

    If 'node' is not given, a random 48-bit number is chosen.

    If 'clock_seq' is given, it is used as the sequence number;
    otherwise a random 14-bit sequence number is chosen."""
    ...
