"""Tests the functions available through the 'time_helpers' module."""

import re
from datetime import datetime, timezone

import numpy as np
import pytest  # type: ignore
from ataraxis_base_utilities import error_format
from ataraxis_time import convert_time, get_timestamp, convert_timestamp, TimestampFormats, TimeUnits


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
def test_convert_time(config, input_value, expected_result, expected_type):
    """Verifies the functioning of the convert_time() function.

    Evaluates the following input scenarios:
        0 - Scalar int input, as_float=True -> float
        1 - Scalar float input, as_float=True -> float
        2 - Scalar int input, as_float=False -> numpy float64
        3 - Numpy scalar signed int input, as_float=True -> float
        4 - Numpy scalar float input, as_float=True -> float
        5 - Numpy scalar unsigned int input, as_float=False -> numpy float64

    Args:
        config: The configuration for the test case.
        input_value: The input value to be converted.
        expected_result: The expected result after conversion.
        expected_type: The expected type of the result.
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
        f"Unsupported 'from_units' argument value ({invalid_input}) encountered when converting input time-values to "
        f"the requested time-format. Use one of the valid members defined in the TimeUnits enumeration: "
        f"{', '.join(tuple(TimeUnits))}."
    )
    with pytest.raises(ValueError, match=error_format(message)):
        # noinspection PyTypeChecker
        convert_time(1, from_units=invalid_input, to_units="ms")

    # Tests invalid 'to_units' argument value (and, indirectly, type).
    message = (
        f"Unsupported 'to_units' argument value ({invalid_input}) encountered when converting input time-values to "
        f"the requested time-format. Use one of the valid members defined in the TimeUnits enumeration: "
        f"{', '.join(tuple(TimeUnits))}."
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
        f"Invalid 'time_separator' argument type encountered when getting the current UTC timestamp. "
        f"Expected {type(str).__name__}, but encountered {invalid_time_separator} of type "
        f"{type(invalid_time_separator).__name__}."
    )
    with pytest.raises(TypeError, match=error_format(message)):
        # noinspection PyTypeChecker
        get_timestamp(output_format=TimestampFormats.STRING, time_separator=invalid_time_separator)

    # Tests invalid output_format value
    invalid_format = "invalid"
    message = (
        f"Unsupported 'format' argument value ({invalid_format}) encountered when getting the current UTC "
        f"timestamp. Use one of the valid members defined in the TimestampFormats enumeration: "
        f"{', '.join(tuple(TimestampFormats))}."
    )
    with pytest.raises(ValueError, match=error_format(message)):
        # noinspection PyTypeChecker
        get_timestamp(output_format=invalid_format)


def test_convert_timestamp_errors() -> None:
    """Verifies the error-handling behavior of the convert_timestamp() method."""

    # Tests an invalid input type
    invalid_input = {"key": "value"}  # Dict instead of valid types
    message = (
        f"Invalid 'timestamp' argument type encountered when converting timestamp. "
        f"Expected string, integer, or NumPy array, but got {invalid_input} of type "
        f"{type(invalid_input).__name__}."
    )
    with pytest.raises(TypeError, match=error_format(message)):
        # noinspection PyTypeChecker
        convert_timestamp(invalid_input)

    # Tests an invalid numpy array (wrong dtype)
    invalid_array = np.array([1, 2, 3], dtype=np.float32)
    message = (
        f"Invalid 'timestamp' argument type encountered when converting a bytes' timestamp. "
        f"Expected a one-dimensional uint8 numpy array, but got {invalid_array} of type "
        f"{type(invalid_array).__name__} with dtype {invalid_array.dtype} and shape {invalid_array.shape}."
    )
    with pytest.raises(TypeError, match=error_format(message)):
        convert_timestamp(invalid_array)

    # Tests an invalid numpy array (wrong dimensions)
    invalid_array = np.array([[1, 2], [3, 4]], dtype=np.uint8)
    message = (
        f"Invalid 'timestamp' argument type encountered when converting a bytes' timestamp. "
        f"Expected a one-dimensional uint8 numpy array, but got {invalid_array} of type "
        f"{type(invalid_array).__name__} with dtype {invalid_array.dtype} and shape {invalid_array.shape}."
    )
    with pytest.raises(TypeError, match=error_format(message)):
        convert_timestamp(invalid_array)

    # Tests invalid time_separator type
    invalid_separator: float = 3.14
    message = (
        f"Invalid 'time_separator' argument type encountered when converting timestamp. "
        f"Expected {type(str).__name__}, but encountered {invalid_separator} of type "
        f"{type(invalid_separator).__name__}."
    )
    with pytest.raises(TypeError, match=error_format(message)):
        # noinspection PyTypeChecker
        convert_timestamp("2024-01-01-12-00-00-000000", time_separator=invalid_separator)

    # Tests invalid output_format value
    invalid_format = "invalid"
    message = (
        f"Unsupported 'output_format' argument value ({invalid_format}) encountered when converting "
        f"timestamp. Use one of the valid members defined in the TimestampFormats enumeration: "
        f"{', '.join(tuple(TimestampFormats))}."
    )
    with pytest.raises(ValueError, match=error_format(message)):
        # noinspection PyTypeChecker
        convert_timestamp(12345, output_format=invalid_format)

    # Tests an invalid string format (wrong number of parts)
    invalid_string = "2024-01-01"
    message = (
        f"Invalid timestamp string format encountered when converting timestamp. "
        f"Expected format YYYY-MM-DD-HH-MM-SS-ffffff, but got '{invalid_string}'."
    )
    with pytest.raises(ValueError, match=error_format(message)):
        convert_timestamp(invalid_string)

    # Tests an invalid string format (non-numeric parts)
    invalid_string = "2024-01-01-12-00-00-abcdef"
    message = (
        f"Invalid timestamp string format encountered when converting timestamp. "
        f"Expected format YYYY-MM-DD-HH-MM-SS-ffffff, but got '{invalid_string}'."
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
