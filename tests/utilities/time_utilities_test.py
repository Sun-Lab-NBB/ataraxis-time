"""Contains tests for classes and functions provided by the time_utilities.py module."""

import re
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest  # type: ignore
from ataraxis_base_utilities import error_format
from ataraxis_time import (
    TimestampFormats,
    TimestampPrecisions,
    TimeUnits,
    convert_time,
    convert_timestamp,
    from_timedelta,
    get_timestamp,
    interval_to_rate,
    parse_timestamp,
    rate_to_interval,
    to_timedelta,
)


@pytest.mark.parametrize(
    "config,input_value,expected_result,expected_type",
    [
        ({"input_type": "scalar", "input_dtype": "int", "as_float": True}, 1000, 1.000, float),
        ({"input_type": "scalar", "input_dtype": "float", "as_float": True}, 1000.5, 1.000, float),
        ({"input_type": "scalar", "input_dtype": "int", "as_float": False}, 1000, 1.000, np.float64),
        ({"input_type": "numpy_scalar", "input_dtype": "int", "as_float": True}, np.int32(1000), 1.000, float),
        ({"input_type": "numpy_scalar", "input_dtype": "float", "as_float": True}, np.float32(1000.5), 1.000, float),
        ({"input_type": "numpy_scalar", "input_dtype": "int", "as_float": False}, np.uint32(1000), 1.000, np.float64),
    ],
)
def test_convert_time(config, input_value, expected_result, expected_type) -> None:
    """Verifies the functioning of the convert_time() function across scalar int, scalar float, numpy signed int,
    numpy float, and numpy unsigned int inputs with both as_float=True and as_float=False configurations.
    """
    # Runs the converter
    result = convert_time(input_value, from_units="ms", to_units="s", as_float=config["as_float"])

    # Verifies the output type
    assert isinstance(result, expected_type)

    # Verifies the output value
    assert result == expected_result


def test_convert_time_errors() -> None:
    """Verifies the error-handling behavior of the convert_time() method."""

    # Tests invalid 'from_units' argument value (and, indirectly, type).
    invalid_input: str = "invalid"
    message = (
        f"Unable to convert time value. The 'from_units' must be one of the valid members defined in the "
        f"TimeUnits enumeration ({', '.join(tuple(TimeUnits))}), but got {invalid_input}."
    )
    with pytest.raises(ValueError, match=error_format(message)):
        # noinspection PyTypeChecker
        convert_time(1, from_units=invalid_input, to_units="ms")

    # Tests invalid 'to_units' argument value (and, indirectly, type).
    message = (
        f"Unable to convert time value. The 'to_units' must be one of the valid members defined in the "
        f"TimeUnits enumeration ({', '.join(tuple(TimeUnits))}), but got {invalid_input}."
    )
    with pytest.raises(ValueError, match=error_format(message)):
        # noinspection PyTypeChecker
        convert_time(1, from_units="s", to_units=invalid_input)


def test_get_timestamp_string_format() -> None:
    """Verifies the functioning of the get_timestamp() method with string output format."""

    # Tests default separator with string format (default)
    timestamp = get_timestamp()
    assert isinstance(timestamp, str)
    assert re.match(r"\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}-\d{6}", timestamp)

    # Tests the explicit string format with the default separator
    timestamp = get_timestamp(output_format=TimestampFormats.STRING)
    assert isinstance(timestamp, str)
    assert re.match(r"\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}-\d{6}", timestamp)

    # Tests custom separator with string format
    timestamp = get_timestamp(output_format=TimestampFormats.STRING, time_separator="_")
    assert isinstance(timestamp, str)
    assert re.match(r"\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}_\d{6}", timestamp)

    # Tests another custom separator
    timestamp = get_timestamp(output_format=TimestampFormats.STRING, time_separator=":")
    assert isinstance(timestamp, str)
    assert re.match(r"\d{4}:\d{2}:\d{2}:\d{2}:\d{2}:\d{2}:\d{6}", timestamp)


def test_get_timestamp_bytes_format() -> None:
    """Verifies the functioning of the get_timestamp() method with bytes' output format."""

    # Tests bytes' output
    timestamp_bytes = get_timestamp(output_format=TimestampFormats.BYTES)
    assert isinstance(timestamp_bytes, np.ndarray)
    assert timestamp_bytes.dtype == np.uint8
    assert timestamp_bytes.ndim == 1

    # Verifies the bytes' timestamp is the correct length (8 bytes for int64)
    assert len(timestamp_bytes) == 8

    # Tests that time_separator is ignored for bytes' format
    timestamp_bytes2 = get_timestamp(output_format=TimestampFormats.BYTES, time_separator="_")
    assert isinstance(timestamp_bytes2, np.ndarray)
    assert timestamp_bytes2.dtype == np.uint8
    assert len(timestamp_bytes2) == 8


def test_get_timestamp_integer_format() -> None:
    """Verifies the functioning of the get_timestamp() method with integer output format."""

    # Tests integer output
    timestamp_int = get_timestamp(output_format=TimestampFormats.INTEGER)
    assert isinstance(timestamp_int, int)

    # Verifies it's a reasonable microsecond timestamp (after the year 2020 and before the year 2050)
    assert 1577836800000000 < timestamp_int < 2524608000000000

    # Tests that time_separator is ignored for integer format
    timestamp_int2 = get_timestamp(output_format=TimestampFormats.INTEGER, time_separator="_")
    assert isinstance(timestamp_int2, int)

    # Verifies timestamps are close (within 1 second)
    assert abs(timestamp_int2 - timestamp_int) < 1_000_000


def test_convert_timestamp_bytes_to_string() -> None:
    """Verifies the functioning of convert_timestamp() when converting from bytes to string format."""

    # Gets a timestamp in bytes
    timestamp_bytes = get_timestamp(output_format=TimestampFormats.BYTES)

    # Converts to string with the default separator
    decoded = convert_timestamp(timestamp_bytes, output_format=TimestampFormats.STRING)
    assert isinstance(decoded, str)
    assert re.match(r"\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}-\d{6}", decoded)

    # Converts to string with custom separator
    decoded = convert_timestamp(timestamp_bytes, time_separator="_", output_format=TimestampFormats.STRING)
    assert isinstance(decoded, str)
    assert re.match(r"\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}_\d{6}", decoded)

    # Parses the decoded timestamp to verify components
    components = decoded.split("_")
    assert len(components) == 7  # Year, month, day, hour, minute, second, microsecond

    # Verifies timestamp components are valid
    year = int(components[0])
    month = int(components[1])
    day = int(components[2])
    hour = int(components[3])
    minute = int(components[4])
    second = int(components[5])
    microsecond = int(components[6])

    assert 2024 <= year <= 2026  # Valid year range for current tests
    assert 1 <= month <= 12  # Valid month
    assert 1 <= day <= 31  # Valid day
    assert 0 <= hour <= 23  # Valid hour
    assert 0 <= minute <= 59  # Valid minute
    assert 0 <= second <= 59  # Valid second
    assert 0 <= microsecond <= 999999  # Valid microseconds


def test_convert_timestamp_integer_to_string() -> None:
    """Verifies the functioning of convert_timestamp() when converting from integer to string format."""

    # Gets a timestamp as an integer
    timestamp_int = get_timestamp(output_format=TimestampFormats.INTEGER)

    # Converts to string
    decoded = convert_timestamp(timestamp_int, output_format=TimestampFormats.STRING)
    assert isinstance(decoded, str)
    assert re.match(r"\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}-\d{6}", decoded)

    # Converts with custom separator
    decoded = convert_timestamp(timestamp_int, time_separator="/", output_format=TimestampFormats.STRING)
    assert isinstance(decoded, str)
    assert re.match(r"\d{4}/\d{2}/\d{2}/\d{2}/\d{2}/\d{2}/\d{6}", decoded)


def test_convert_timestamp_string_to_integer() -> None:
    """Verifies the functioning of convert_timestamp() when converting from string to integer format."""

    # Gets a timestamp as a string
    timestamp_str = get_timestamp(output_format=TimestampFormats.STRING)

    # Converts to integer
    result = convert_timestamp(timestamp_str, output_format=TimestampFormats.INTEGER)
    assert isinstance(result, int)
    assert 1577836800000000 < result < 2524608000000000  # Reasonable range

    # Tests with custom separator input
    timestamp_str = get_timestamp(output_format=TimestampFormats.STRING, time_separator="_")
    result = convert_timestamp(timestamp_str, time_separator="_", output_format=TimestampFormats.INTEGER)
    assert isinstance(result, int)


def test_convert_timestamp_string_to_bytes() -> None:
    """Verifies the functioning of convert_timestamp() when converting from string to bytes' format."""

    # Gets a timestamp as a string
    timestamp_str = get_timestamp(output_format=TimestampFormats.STRING)

    # Converts to bytes
    result = convert_timestamp(timestamp_str, output_format=TimestampFormats.BYTES)
    assert isinstance(result, np.ndarray)
    assert result.dtype == np.uint8
    assert len(result) == 8


def test_convert_timestamp_bytes_to_integer() -> None:
    """Verifies the functioning of convert_timestamp() when converting from bytes to integer format."""

    # Gets a timestamp as bytes
    timestamp_bytes = get_timestamp(output_format=TimestampFormats.BYTES)

    # Converts to integer
    result = convert_timestamp(timestamp_bytes, output_format=TimestampFormats.INTEGER)
    assert isinstance(result, int)
    assert 1577836800000000 < result < 2524608000000000


def test_convert_timestamp_integer_to_bytes() -> None:
    """Verifies the functioning of convert_timestamp() when converting from integer to bytes' format."""

    # Gets a timestamp as an integer
    timestamp_int = get_timestamp(output_format=TimestampFormats.INTEGER)

    # Converts to bytes
    result = convert_timestamp(timestamp_int, output_format=TimestampFormats.BYTES)
    assert isinstance(result, np.ndarray)
    assert result.dtype == np.uint8
    assert len(result) == 8


def test_get_timestamp_errors() -> None:
    """Verifies the error-handling behavior of the get_timestamp() method."""

    # Tests invalid time_separator type
    invalid_time_separator: int = 123
    message = (
        f"Unable to get UTC timestamp. The 'time_separator' must be a string, but got "
        f"{invalid_time_separator} of type {type(invalid_time_separator).__name__}."
    )
    with pytest.raises(TypeError, match=error_format(message)):
        # noinspection PyTypeChecker
        get_timestamp(output_format=TimestampFormats.STRING, time_separator=invalid_time_separator)

    # Tests invalid output_format value
    invalid_format = "invalid"
    message = (
        f"Unable to get UTC timestamp. The 'output_format' must be one of the valid members defined in the "
        f"TimestampFormats enumeration ({', '.join(tuple(TimestampFormats))}), but got {invalid_format}."
    )
    with pytest.raises(ValueError, match=error_format(message)):
        # noinspection PyTypeChecker
        get_timestamp(output_format=invalid_format)


def test_convert_timestamp_errors() -> None:
    """Verifies the error-handling behavior of the convert_timestamp() method."""

    # Tests an invalid input type
    invalid_input = {"key": "value"}  # Dict instead of valid types
    message = (
        f"Unable to convert timestamp. The 'timestamp' must be a string, integer, or NumPy array, but got "
        f"{invalid_input} of type {type(invalid_input).__name__}."
    )
    with pytest.raises(TypeError, match=error_format(message)):
        # noinspection PyTypeChecker
        convert_timestamp(invalid_input)

    # Tests an invalid numpy array (wrong dtype)
    invalid_array = np.array([1, 2, 3], dtype=np.float32)
    message = (
        f"Unable to convert bytes timestamp. The 'timestamp' must be a one-dimensional uint8 numpy array, "
        f"but got {invalid_array} of type {type(invalid_array).__name__} with dtype {invalid_array.dtype} and shape "
        f"{invalid_array.shape}."
    )
    with pytest.raises(TypeError, match=error_format(message)):
        convert_timestamp(invalid_array)

    # Tests an invalid numpy array (wrong dimensions)
    invalid_array = np.array([[1, 2], [3, 4]], dtype=np.uint8)
    message = (
        f"Unable to convert bytes timestamp. The 'timestamp' must be a one-dimensional uint8 numpy array, "
        f"but got {invalid_array} of type {type(invalid_array).__name__} with dtype {invalid_array.dtype} and shape "
        f"{invalid_array.shape}."
    )
    with pytest.raises(TypeError, match=error_format(message)):
        convert_timestamp(invalid_array)

    # Tests invalid time_separator type
    invalid_separator: float = 3.14
    message = (
        f"Unable to convert timestamp. The 'time_separator' must be a string, but got "
        f"{invalid_separator} of type {type(invalid_separator).__name__}."
    )
    with pytest.raises(TypeError, match=error_format(message)):
        # noinspection PyTypeChecker
        convert_timestamp("2024-01-01-12-00-00-000000", time_separator=invalid_separator)

    # Tests invalid output_format value
    invalid_format = "invalid"
    message = (
        f"Unable to convert timestamp. The 'output_format' must be one of the valid members defined in the "
        f"TimestampFormats enumeration ({', '.join(tuple(TimestampFormats))}), but got {invalid_format}."
    )
    with pytest.raises(ValueError, match=error_format(message)):
        # noinspection PyTypeChecker
        convert_timestamp(12345, output_format=invalid_format)

    # Tests invalid precision value.
    invalid_precision = "invalid"
    message = (
        f"Unable to convert timestamp. The 'precision' must be one of the valid members defined in the "
        f"TimestampPrecisions enumeration ({', '.join(tuple(TimestampPrecisions))}), but got {invalid_precision}."
    )
    with pytest.raises(ValueError, match=error_format(message)):
        convert_timestamp(12345, precision=invalid_precision)

    # Tests a string with too many parts (>7). The internal ValueError is caught and re-raised with the generic
    # format error message.
    too_many_parts = "2024-01-01-12-00-00-000000-extra"
    message = (
        f"Unable to convert string timestamp. The timestamp must follow the format "
        f"YYYY-MM-DD-HH-MM-SS-ffffff (1 to 7 parts), but got '{too_many_parts}'."
    )
    with pytest.raises(ValueError, match=error_format(message)):
        convert_timestamp(too_many_parts)

    # Tests an invalid string format (non-numeric parts)
    invalid_string = "2024-01-01-12-00-00-abcdef"
    message = (
        f"Unable to convert string timestamp. The timestamp must follow the format "
        f"YYYY-MM-DD-HH-MM-SS-ffffff (1 to 7 parts), but got '{invalid_string}'."
    )
    with pytest.raises(ValueError, match=error_format(message)):
        convert_timestamp(invalid_string)


def test_timestamp_roundtrip_all_formats() -> None:
    """Verifies that converting between all timestamp formats preserves the information."""

    # Get an initial timestamp in all formats
    original_str = get_timestamp(output_format=TimestampFormats.STRING)
    original_int = get_timestamp(output_format=TimestampFormats.INTEGER)
    original_bytes = get_timestamp(output_format=TimestampFormats.BYTES)

    # String -> Integer -> String
    str_to_int = convert_timestamp(original_str, output_format=TimestampFormats.INTEGER)
    int_to_str = convert_timestamp(str_to_int, output_format=TimestampFormats.STRING)
    assert int_to_str == original_str

    # String -> Bytes -> String
    str_to_bytes = convert_timestamp(original_str, output_format=TimestampFormats.BYTES)
    bytes_to_str = convert_timestamp(str_to_bytes, output_format=TimestampFormats.STRING)
    assert bytes_to_str == original_str

    # Integer -> Bytes -> Integer
    int_to_bytes = convert_timestamp(original_int, output_format=TimestampFormats.BYTES)
    bytes_to_int = convert_timestamp(int_to_bytes, output_format=TimestampFormats.INTEGER)
    assert bytes_to_int == original_int

    # Integer -> String -> Integer
    int_to_str = convert_timestamp(original_int, output_format=TimestampFormats.STRING)
    str_to_int = convert_timestamp(int_to_str, output_format=TimestampFormats.INTEGER)
    assert str_to_int == original_int

    # Bytes -> String -> Bytes
    bytes_to_str = convert_timestamp(original_bytes, output_format=TimestampFormats.STRING)
    str_to_bytes = convert_timestamp(bytes_to_str, output_format=TimestampFormats.BYTES)
    assert np.array_equal(str_to_bytes, original_bytes)

    # Bytes -> Integer -> Bytes
    bytes_to_int = convert_timestamp(original_bytes, output_format=TimestampFormats.INTEGER)
    int_to_bytes = convert_timestamp(bytes_to_int, output_format=TimestampFormats.BYTES)
    assert np.array_equal(int_to_bytes, original_bytes)


def test_timestamp_custom_separator_roundtrip() -> None:
    """Verifies that custom separators work correctly in roundtrip conversions."""

    # Test with underscore separator
    original = get_timestamp(output_format=TimestampFormats.STRING, time_separator="_")
    to_int = convert_timestamp(original, time_separator="_", output_format=TimestampFormats.INTEGER)
    back_to_str = convert_timestamp(to_int, time_separator="_", output_format=TimestampFormats.STRING)
    assert back_to_str == original

    # Test with colon separator
    original = get_timestamp(output_format=TimestampFormats.STRING, time_separator=":")
    to_bytes = convert_timestamp(original, time_separator=":", output_format=TimestampFormats.BYTES)
    back_to_str = convert_timestamp(to_bytes, time_separator=":", output_format=TimestampFormats.STRING)
    assert back_to_str == original

    # Test conversion between different separators
    original = get_timestamp(output_format=TimestampFormats.STRING, time_separator="-")
    to_int = convert_timestamp(original, time_separator="-", output_format=TimestampFormats.INTEGER)
    with_new_sep = convert_timestamp(to_int, time_separator="_", output_format=TimestampFormats.STRING)
    assert original.replace("-", "_") == with_new_sep


def test_timestamp_datetime_validity() -> None:
    """Verifies that all timestamp formats represent valid datetime objects."""

    # Get timestamp in integer format
    timestamp_int = get_timestamp(output_format=TimestampFormats.INTEGER)

    # Convert to string and parse
    timestamp_str = convert_timestamp(timestamp_int, output_format=TimestampFormats.STRING)
    components = timestamp_str.split("-")

    # Create datetime object and verify it's valid
    dt = datetime(
        year=int(components[0]),
        month=int(components[1]),
        day=int(components[2]),
        hour=int(components[3]),
        minute=int(components[4]),
        second=int(components[5]),
        microsecond=int(components[6]),
        tzinfo=timezone.utc,
    )
    assert isinstance(dt, datetime)

    # Verify the datetime converts back to the same microseconds
    reconstructed_microseconds = int(dt.timestamp() * 1_000_000)
    assert abs(reconstructed_microseconds - timestamp_int) < 1  # Allow for rounding


def test_timestamp_precisions_enum() -> None:
    """Verifies the TimestampPrecisions enumeration functionality."""
    # Verifies all expected enum values exist.
    assert TimestampPrecisions.YEAR == "year"
    assert TimestampPrecisions.MONTH == "month"
    assert TimestampPrecisions.DAY == "day"
    assert TimestampPrecisions.HOUR == "hour"
    assert TimestampPrecisions.MINUTE == "minute"
    assert TimestampPrecisions.SECOND == "second"
    assert TimestampPrecisions.MICROSECOND == "microsecond"

    # Verifies the enumeration has exactly the expected members.
    expected = {"YEAR", "MONTH", "DAY", "HOUR", "MINUTE", "SECOND", "MICROSECOND"}
    actual = {member.name for member in TimestampPrecisions}
    assert actual == expected


def test_get_timestamp_precision() -> None:
    """Verifies the precision parameter of get_timestamp() for all formats and precision levels."""
    # Tests string format with various precision levels.
    # MICROSECOND (default) should produce 7-part string.
    ts_full = get_timestamp(output_format=TimestampFormats.STRING)
    assert isinstance(ts_full, str)
    assert len(ts_full.split("-")) == 7

    # SECOND: 6 parts (YYYY-MM-DD-HH-MM-SS)
    ts_second = get_timestamp(output_format=TimestampFormats.STRING, precision=TimestampPrecisions.SECOND)
    assert isinstance(ts_second, str)
    assert len(ts_second.split("-")) == 6

    # MINUTE: 5 parts
    ts_minute = get_timestamp(output_format=TimestampFormats.STRING, precision=TimestampPrecisions.MINUTE)
    assert isinstance(ts_minute, str)
    assert len(ts_minute.split("-")) == 5

    # HOUR: 4 parts
    ts_hour = get_timestamp(output_format=TimestampFormats.STRING, precision=TimestampPrecisions.HOUR)
    assert isinstance(ts_hour, str)
    assert len(ts_hour.split("-")) == 4

    # DAY: 3 parts
    ts_day = get_timestamp(output_format=TimestampFormats.STRING, precision=TimestampPrecisions.DAY)
    assert isinstance(ts_day, str)
    assert len(ts_day.split("-")) == 3

    # MONTH: 2 parts
    ts_month = get_timestamp(output_format=TimestampFormats.STRING, precision=TimestampPrecisions.MONTH)
    assert isinstance(ts_month, str)
    assert len(ts_month.split("-")) == 2

    # YEAR: 1 part
    ts_year = get_timestamp(output_format=TimestampFormats.STRING, precision=TimestampPrecisions.YEAR)
    assert isinstance(ts_year, str)
    assert len(ts_year.split("-")) == 1

    # Tests integer format with precision truncation.
    int_full = get_timestamp(output_format=TimestampFormats.INTEGER, precision=TimestampPrecisions.MICROSECOND)
    int_day = get_timestamp(output_format=TimestampFormats.INTEGER, precision=TimestampPrecisions.DAY)
    assert isinstance(int_full, int)
    assert isinstance(int_day, int)
    # Day-precision should zero out hours, minutes, seconds, microseconds.
    assert int_day <= int_full
    # The day-truncated value should be at a day boundary (divisible by microseconds in a day minus timezone offset).
    assert int_day % 1_000_000 == 0  # At least microseconds should be zeroed.

    # Tests bytes format with precision truncation.
    bytes_full = get_timestamp(output_format=TimestampFormats.BYTES, precision=TimestampPrecisions.MICROSECOND)
    bytes_day = get_timestamp(output_format=TimestampFormats.BYTES, precision=TimestampPrecisions.DAY)
    assert isinstance(bytes_full, np.ndarray)
    assert isinstance(bytes_day, np.ndarray)

    # Tests invalid precision.
    message = (
        f"Unable to get UTC timestamp. The 'precision' must be one of the valid members defined in the "
        f"TimestampPrecisions enumeration ({', '.join(tuple(TimestampPrecisions))}), but got invalid."
    )
    with pytest.raises(ValueError, match=error_format(message)):
        get_timestamp(precision="invalid")


def test_convert_timestamp_variable_length_strings() -> None:
    """Verifies convert_timestamp() correctly handles variable-length string inputs (1-7 parts)."""
    # 7 parts (full): standard behavior.
    result = convert_timestamp("2024-06-15-12-30-45-123456", output_format=TimestampFormats.STRING)
    assert isinstance(result, str)
    assert result == "2024-06-15-12-30-45-123456"

    # 6 parts: missing microsecond (defaults to 0).
    result = convert_timestamp("2024-06-15-12-30-45", output_format=TimestampFormats.STRING)
    assert isinstance(result, str)
    assert result == "2024-06-15-12-30-45-000000"

    # 5 parts: missing second and microsecond.
    result = convert_timestamp("2024-06-15-12-30", output_format=TimestampFormats.STRING)
    assert isinstance(result, str)
    assert result == "2024-06-15-12-30-00-000000"

    # 3 parts: just date.
    result = convert_timestamp("2024-06-15", output_format=TimestampFormats.STRING)
    assert isinstance(result, str)
    assert result == "2024-06-15-00-00-00-000000"

    # 1 part: just year.
    result = convert_timestamp("2024", output_format=TimestampFormats.STRING)
    assert isinstance(result, str)
    assert result == "2024-01-01-00-00-00-000000"

    # Tests roundtrip: variable-length string to integer and back to full string.
    int_result = convert_timestamp("2024-06-15-12-30", output_format=TimestampFormats.INTEGER)
    assert isinstance(int_result, int)
    str_result = convert_timestamp(int_result, output_format=TimestampFormats.STRING)
    assert str_result == "2024-06-15-12-30-00-000000"


def test_convert_timestamp_precision() -> None:
    """Verifies the precision parameter of convert_timestamp() for output truncation."""
    full_ts = "2024-06-15-12-30-45-123456"

    # Convert string to string with day precision.
    result = convert_timestamp(full_ts, output_format=TimestampFormats.STRING, precision=TimestampPrecisions.DAY)
    assert isinstance(result, str)
    assert len(result.split("-")) == 3

    # Convert string to string with minute precision.
    result = convert_timestamp(full_ts, output_format=TimestampFormats.STRING, precision=TimestampPrecisions.MINUTE)
    assert isinstance(result, str)
    assert len(result.split("-")) == 5

    # Convert integer to string with hour precision.
    int_ts = convert_timestamp(full_ts, output_format=TimestampFormats.INTEGER)
    result = convert_timestamp(int_ts, output_format=TimestampFormats.STRING, precision=TimestampPrecisions.HOUR)
    assert isinstance(result, str)
    assert len(result.split("-")) == 4


def test_parse_timestamp() -> None:
    """Verifies the parse_timestamp() function with various format strings and output formats."""
    # Tests parsing a standard ISO-style date string.
    result = parse_timestamp("2024-06-15 12:30:45", "%Y-%m-%d %H:%M:%S")
    assert isinstance(result, int)
    assert result > 0

    # Verifies the parsed value matches expected microseconds.
    expected_dt = datetime(2024, 6, 15, 12, 30, 45, tzinfo=timezone.utc)
    expected_us = int(expected_dt.timestamp() * 1_000_000)
    assert result == expected_us

    # Tests string output format.
    result_str = parse_timestamp("2024-06-15 12:30:45", "%Y-%m-%d %H:%M:%S", output_format=TimestampFormats.STRING)
    assert isinstance(result_str, str)
    assert result_str == "2024-06-15-12-30-45-000000"

    # Tests bytes output format.
    result_bytes = parse_timestamp("2024-06-15 12:30:45", "%Y-%m-%d %H:%M:%S", output_format=TimestampFormats.BYTES)
    assert isinstance(result_bytes, np.ndarray)
    assert result_bytes.dtype == np.uint8
    assert len(result_bytes) == 8

    # Tests with custom time_separator for string output.
    result_sep = parse_timestamp(
        "2024-06-15 12:30:45", "%Y-%m-%d %H:%M:%S", output_format=TimestampFormats.STRING, time_separator="_"
    )
    assert isinstance(result_sep, str)
    assert "_" in result_sep

    # Tests with precision truncation.
    result_day = parse_timestamp(
        "2024-06-15 12:30:45",
        "%Y-%m-%d %H:%M:%S",
        output_format=TimestampFormats.STRING,
        precision=TimestampPrecisions.DAY,
    )
    assert isinstance(result_day, str)
    assert len(result_day.split("-")) == 3
    assert result_day == "2024-06-15"

    # Tests parsing a date-only format.
    result_date = parse_timestamp("15/06/2024", "%d/%m/%Y")
    assert isinstance(result_date, int)
    expected_dt = datetime(2024, 6, 15, tzinfo=timezone.utc)
    assert result_date == int(expected_dt.timestamp() * 1_000_000)

    # Tests parsing with microseconds.
    result_us = parse_timestamp("2024-06-15 12:30:45.123456", "%Y-%m-%d %H:%M:%S.%f")
    assert isinstance(result_us, int)
    expected_dt = datetime(2024, 6, 15, 12, 30, 45, 123456, tzinfo=timezone.utc)
    assert result_us == int(expected_dt.timestamp() * 1_000_000)


def test_parse_timestamp_errors() -> None:
    """Verifies the error-handling behavior of the parse_timestamp() function."""
    # Tests an invalid format string that doesn't match the date string.
    message = (
        f"Unable to parse timestamp. The date string '2024-06-15' could not be parsed with the format "
        f"string '%Y/%m/%d'."
    )
    with pytest.raises(ValueError, match=error_format(message)):
        parse_timestamp("2024-06-15", "%Y/%m/%d")

    # Tests an invalid precision value.
    message = (
        f"Unable to parse timestamp. The 'precision' must be one of the valid members defined in the "
        f"TimestampPrecisions enumeration ({', '.join(tuple(TimestampPrecisions))}), but got invalid."
    )
    with pytest.raises(ValueError, match=error_format(message)):
        parse_timestamp("2024-06-15", "%Y-%m-%d", precision="invalid")

    # Tests an invalid output_format.
    message = (
        f"Unable to parse timestamp. The 'output_format' must be one of the valid members defined in the "
        f"TimestampFormats enumeration ({', '.join(tuple(TimestampFormats))}), but got invalid."
    )
    with pytest.raises(ValueError, match=error_format(message)):
        # noinspection PyTypeChecker
        parse_timestamp("2024-06-15", "%Y-%m-%d", output_format="invalid")


def test_rate_to_interval() -> None:
    """Verifies the rate_to_interval() function with various rates and units."""
    # 1 Hz = 1,000,000 microseconds.
    result = rate_to_interval(1.0, to_units=TimeUnits.MICROSECOND)
    assert isinstance(result, np.float64)
    assert result == 1_000_000.0

    # 1 Hz = 1 second.
    result = rate_to_interval(1.0, to_units=TimeUnits.SECOND, as_float=True)
    assert isinstance(result, float)
    assert result == 1.0

    # 60 Hz = ~16666.667 microseconds.
    result = rate_to_interval(60.0, to_units=TimeUnits.MICROSECOND, as_float=True)
    assert isinstance(result, float)
    assert abs(result - 16666.667) < 1.0

    # 1000 Hz = 1 millisecond.
    result = rate_to_interval(1000.0, to_units=TimeUnits.MILLISECOND, as_float=True)
    assert isinstance(result, float)
    assert result == 1.0

    # Tests with numpy input.
    result = rate_to_interval(np.float64(10.0), to_units=TimeUnits.SECOND, as_float=True)
    assert isinstance(result, float)
    assert result == 0.1


def test_interval_to_rate() -> None:
    """Verifies the interval_to_rate() function with various intervals and units."""
    # 1,000,000 microseconds = 1 Hz.
    result = interval_to_rate(1_000_000.0, from_units=TimeUnits.MICROSECOND)
    assert isinstance(result, np.float64)
    assert result == 1.0

    # 1 second = 1 Hz.
    result = interval_to_rate(1.0, from_units=TimeUnits.SECOND, as_float=True)
    assert isinstance(result, float)
    assert result == 1.0

    # 1 millisecond = 1000 Hz.
    result = interval_to_rate(1.0, from_units=TimeUnits.MILLISECOND, as_float=True)
    assert isinstance(result, float)
    assert result == 1000.0

    # Tests roundtrip: rate -> interval -> rate. Uses tolerant comparison due to rounding in convert_time.
    original_rate = 30.0
    interval = rate_to_interval(original_rate, to_units=TimeUnits.MICROSECOND, as_float=True)
    recovered_rate = interval_to_rate(interval, from_units=TimeUnits.MICROSECOND, as_float=True)
    assert abs(recovered_rate - original_rate) < 1.0


def test_rate_interval_errors() -> None:
    """Verifies error handling for rate_to_interval() and interval_to_rate()."""
    # Tests zero rate.
    message = f"Unable to convert rate to interval. The 'rate' must be greater than 0, but got 0."
    with pytest.raises(ValueError, match=error_format(message)):
        rate_to_interval(0)

    # Tests negative rate.
    message = f"Unable to convert rate to interval. The 'rate' must be greater than 0, but got -1.0."
    with pytest.raises(ValueError, match=error_format(message)):
        rate_to_interval(-1.0)

    # Tests zero interval.
    message = f"Unable to convert interval to rate. The 'interval' must be greater than 0, but got 0."
    with pytest.raises(ValueError, match=error_format(message)):
        interval_to_rate(0)

    # Tests negative interval.
    message = f"Unable to convert interval to rate. The 'interval' must be greater than 0, but got -5.0."
    with pytest.raises(ValueError, match=error_format(message)):
        interval_to_rate(-5.0)


def test_to_timedelta() -> None:
    """Verifies the to_timedelta() function with various units."""
    # 1 second.
    td = to_timedelta(1.0, from_units=TimeUnits.SECOND)
    assert isinstance(td, timedelta)
    assert td == timedelta(seconds=1)

    # 1000 milliseconds = 1 second.
    td = to_timedelta(1000.0, from_units=TimeUnits.MILLISECOND)
    assert isinstance(td, timedelta)
    assert td == timedelta(seconds=1)

    # 1 hour.
    td = to_timedelta(1.0, from_units=TimeUnits.HOUR)
    assert isinstance(td, timedelta)
    assert td == timedelta(hours=1)

    # 1 day.
    td = to_timedelta(1.0, from_units=TimeUnits.DAY)
    assert isinstance(td, timedelta)
    assert td == timedelta(days=1)

    # 500,000 microseconds = 0.5 seconds.
    td = to_timedelta(500_000, from_units=TimeUnits.MICROSECOND)
    assert isinstance(td, timedelta)
    assert td == timedelta(seconds=0.5)


def test_from_timedelta() -> None:
    """Verifies the from_timedelta() function with various units."""
    # 1 second timedelta to seconds.
    result = from_timedelta(timedelta(seconds=1), to_units=TimeUnits.SECOND, as_float=True)
    assert isinstance(result, float)
    assert result == 1.0

    # 1 second timedelta to milliseconds.
    result = from_timedelta(timedelta(seconds=1), to_units=TimeUnits.MILLISECOND, as_float=True)
    assert isinstance(result, float)
    assert result == 1000.0

    # 1 hour timedelta to minutes.
    result = from_timedelta(timedelta(hours=1), to_units=TimeUnits.MINUTE, as_float=True)
    assert isinstance(result, float)
    assert result == 60.0

    # Returns np.float64 by default.
    result = from_timedelta(timedelta(seconds=5), to_units=TimeUnits.SECOND)
    assert isinstance(result, np.float64)
    assert result == 5.0


def test_timedelta_roundtrip() -> None:
    """Verifies that to_timedelta and from_timedelta produce consistent roundtrip conversions."""
    # Roundtrip: value -> timedelta -> value.
    for units in [TimeUnits.SECOND, TimeUnits.MILLISECOND, TimeUnits.MINUTE, TimeUnits.HOUR]:
        original = 42.0
        td = to_timedelta(original, from_units=units)
        recovered = from_timedelta(td, to_units=units, as_float=True)
        assert abs(recovered - original) < 0.01
