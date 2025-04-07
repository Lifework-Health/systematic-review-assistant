"""Unit tests for utility functions in src/sr_assistant/app/utils.py."""

import datetime
import typing as t
import uuid
from datetime import timezone
from zoneinfo import ZoneInfo

import pytest
import uuid6

from sr_assistant.app.utils import (
    id_to_timestamp,
    id_to_unix_ms,
    id_to_unix_s,
    is_pmcid,
    is_pmid,
    is_utc_datetime,
    is_uuid,
    utcnow,
    validate_uuid,
    validate_uuid7,
)


class TestIdentifierValidation:
    """Tests for identifier validation functions."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("12345678", True),  # Valid PMID
            ("1", True),  # Minimum valid PMID
            ("123456789", False),  # Too long
            ("abc123", False),  # Contains non-digits
            ("", False),  # Empty string
            (None, False),  # None value
        ],
    )
    def test_is_pmid(self, value: t.Any, expected: bool) -> None:
        """Test is_pmid function with various inputs."""
        if value is None:  # Handle the None test case
            with pytest.raises(TypeError):
                is_pmid(value)  # type: ignore
        else:
            assert is_pmid(value) == expected

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("PMC12345678", True),  # Valid PMCID
            ("PMC1", True),  # Minimum valid PMCID
            ("PMC123456789", False),  # Too long
            ("pmc12345", False),  # Lowercase prefix
            ("12345678", False),  # Missing PMC prefix
            ("PMCabc123", False),  # Contains non-digits after prefix
            ("", False),  # Empty string
            (None, False),  # None value
        ],
    )
    def test_is_pmcid(self, value: t.Any, expected: bool) -> None:
        """Test is_pmcid function with various inputs."""
        if value is None:  # Handle the None test case
            with pytest.raises(TypeError):
                is_pmcid(value)  # type: ignore
        else:
            assert is_pmcid(value) == expected


class TestDatetimeUtils:
    """Tests for datetime utility functions."""

    def test_is_utc_datetime_with_timezone_utc(self) -> None:
        """Test is_utc_datetime with timezone.utc."""
        dt = datetime.datetime.now(tz=timezone.utc)
        assert is_utc_datetime(dt) is True

    def test_is_utc_datetime_with_zoneinfo_utc(self) -> None:
        """Test is_utc_datetime with ZoneInfo("UTC")."""
        dt = datetime.datetime.now(tz=ZoneInfo("UTC"))
        assert is_utc_datetime(dt) is True

    def test_is_utc_datetime_with_other_timezone(self) -> None:
        """Test is_utc_datetime with a non-UTC timezone."""
        dt = datetime.datetime.now(tz=ZoneInfo("Europe/London"))
        assert is_utc_datetime(dt) is False

    def test_is_utc_datetime_with_no_timezone(self) -> None:
        """Test is_utc_datetime with a naive datetime (no timezone)."""
        dt = datetime.datetime.now()
        assert is_utc_datetime(dt) is False

    def test_utcnow(self) -> None:
        """Test utcnow returns a datetime with UTC timezone."""
        now = utcnow()
        assert isinstance(now, datetime.datetime)
        assert is_utc_datetime(now) is True

        # Ensure the time is close to the current time
        now_timestamp = now.timestamp()
        current_timestamp = datetime.datetime.now(tz=timezone.utc).timestamp()
        assert abs(now_timestamp - current_timestamp) < 1.0  # Within 1 second


class TestUuidUtils:
    """Tests for UUID utility functions."""

    def test_is_uuid_with_uuid_object(self) -> None:
        """Test is_uuid with a uuid.UUID object."""
        u = uuid.uuid4()
        result = is_uuid(u)
        assert result is u

    def test_is_uuid_with_uuid6_object(self) -> None:
        """Test is_uuid with a uuid6.UUID object."""
        u = uuid6.uuid7()
        result = is_uuid(u)
        assert result is u

    def test_is_uuid_with_valid_uuid_string(self) -> None:
        """Test is_uuid with a valid UUID string."""
        u_str = "123e4567-e89b-12d3-a456-426614174000"  # Valid UUID string
        result = is_uuid(u_str)
        assert isinstance(result, uuid.UUID)
        assert str(result) == u_str

    def test_is_uuid_with_valid_uuid6_string(self) -> None:
        """Test is_uuid with a valid UUIDv7 string."""
        u_str = "018f668c-1d7b-7cea-b078-2bf357352967"  # Valid UUIDv7 string
        result = is_uuid(u_str)
        assert isinstance(result, (uuid.UUID, uuid6.UUID))
        assert str(result) == u_str

    def test_is_uuid_with_invalid_uuid_string(self) -> None:
        """Test is_uuid with an invalid UUID string."""
        result = is_uuid("not-a-uuid")
        assert result is None

    def test_is_uuid_with_non_string_or_uuid(self) -> None:
        """Test is_uuid with a value that is neither a string nor a UUID object."""
        result = is_uuid(12345)
        assert result is None


class TestUuidValidation:
    """Tests for UUID validation functions."""

    def test_validate_uuid_with_valid_uuid(self) -> None:
        """Test validate_uuid with a valid UUID of the correct version."""
        # Create UUIDs of different versions
        u1 = uuid.uuid1()  # v1
        u4 = uuid.uuid4()  # v4
        u7 = uuid6.uuid7()  # v7

        # Validate each UUID with its correct version
        assert validate_uuid(u1, 1) is u1
        assert validate_uuid(u4, 4) is u4
        assert validate_uuid(u7, 7) is u7

    def test_validate_uuid_with_valid_string(self) -> None:
        """Test validate_uuid with a valid UUID string."""
        # Valid UUIDv4 string
        u4_str = "123e4567-e89b-12d3-a456-426614174000"
        result = validate_uuid(u4_str, 4)
        assert isinstance(result, uuid.UUID)
        assert str(result) == u4_str

    def test_validate_uuid_with_wrong_version(self) -> None:
        """Test validate_uuid with a UUID of the wrong version."""
        # UUIDv4
        u4 = uuid.uuid4()

        # Try to validate as v1
        with pytest.raises(ValueError, match=r"Expected a UUID1, got UUID4"):
            validate_uuid(u4, 1)

    def test_validate_uuid_with_invalid_type(self) -> None:
        """Test validate_uuid with a non-UUID value."""
        with pytest.raises(TypeError, match=r"Expected a uuid.UUID or uuid6.UUID"):
            validate_uuid(12345, 4)  # type: ignore

    def test_validate_uuid7_with_valid_uuid7(self) -> None:
        """Test validate_uuid7 with a valid UUIDv7."""
        u7_str = "018f668c-1d7b-7cea-b078-2bf357352967"  # Valid UUIDv7 string
        # Should not raise an exception
        validate_uuid7(u7_str)

    def test_validate_uuid7_with_wrong_version(self) -> None:
        """Test validate_uuid7 with a UUID of the wrong version."""
        u4_str = "123e4567-e89b-12d3-a456-426614174000"  # This is actually a UUIDv1 according to uuid6 library
        with pytest.raises(ValueError, match=r"Invalid UUID version, want 7, got 1"):
            validate_uuid7(u4_str)

    def test_validate_uuid7_with_invalid_format(self) -> None:
        """Test validate_uuid7 with an invalid UUID format."""
        with pytest.raises(ValueError, match=r"Invalid UUID format"):
            validate_uuid7("not-a-uuid")

    def test_validate_uuid7_with_empty_string(self) -> None:
        """Test validate_uuid7 with an empty string."""
        with pytest.raises(ValueError, match=r"UUID string is required"):
            validate_uuid7("")


class TestUuidConversion:
    """Tests for UUID conversion functions."""

    # Use a known UUIDv7 for consistent testing
    # The time component represents: 2024-05-11T07:26:49.723Z
    UUID7_STR = "018f668c-1d7b-7cea-b078-2bf357352967"
    EXPECTED_TIMESTAMP = "2024-05-11T07:26:49.723000"
    EXPECTED_UNIX_MS = 1715412409723
    EXPECTED_UNIX_S = 1715412409.723

    def test_id_to_timestamp_with_default_suffix(self) -> None:
        """Test id_to_timestamp with the default suffix (+00:00)."""
        result = id_to_timestamp(self.UUID7_STR)
        assert result == f"{self.EXPECTED_TIMESTAMP}+00:00"

    def test_id_to_timestamp_with_z_suffix(self) -> None:
        """Test id_to_timestamp with 'Z' suffix."""
        result = id_to_timestamp(self.UUID7_STR, suffix="Z")
        assert result == f"{self.EXPECTED_TIMESTAMP}Z"

    def test_id_to_unix_ms(self) -> None:
        """Test id_to_unix_ms returns the correct Unix timestamp in milliseconds."""
        result = id_to_unix_ms(self.UUID7_STR)
        assert result == self.EXPECTED_UNIX_MS

    def test_id_to_unix_s(self) -> None:
        """Test id_to_unix_s returns the correct Unix timestamp in seconds."""
        result = id_to_unix_s(self.UUID7_STR)
        assert result == self.EXPECTED_UNIX_S
