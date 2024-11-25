"""Tests the functions available through the 'helper_functions' module."""

import re
from datetime import datetime, timezone

import numpy as np
import pytest  # type: ignore
from ataraxis_base_utilities import error_format
from ataraxis_time.time_helpers import convert_time, get_timestamp, extract_timestamp_from_bytes


@pytest.mark.parametrize(
    "config,input_value,expected_result,expected_type",
    [
        ({"input_type": "scalar", "input_dtype": "int", "convert_output": True}, 1000, 1.000, float),
        ({"input_type": "scalar", "input_dtype": "float", "convert_output": True}, 1000.5, 1.000, float),
        ({"input_type": "scalar", "input_dtype": "int", "convert_output": False}, 1000, 1.000, np.float64),
        (
            {"input_type": "list", "input_dtype": "int", "convert_output": True},
            [1000, 2000, 3000],
            [1.000, 2.000, 3.000],
            tuple,
        ),
        (
            {"input_type": "list", "input_dtype": "float", "convert_output": True},
            [1000.5, 2000.5, 3000.5],
            [1.000, 2.001, 3.001],
            tuple,
        ),
        (
            {"input_type": "list", "input_dtype": "int", "convert_output": False},
            [1000, 2000, 3000],
            np.array([1.000, 2.000, 3.000]),
            np.ndarray,
        ),
        ({"input_type": "numpy_array", "input_dtype": "int", "convert_output": True}, np.array([1000]), 1.000, float),
        (
            {"input_type": "numpy_array", "input_dtype": "float", "convert_output": True},
            np.array([1000.5, 2000.5, 3000.5]),
            np.array([1.000, 2.001, 3.001]),
            tuple,
        ),
        (
            {"input_type": "numpy_array", "input_dtype": "int", "convert_output": False},
            np.array([1000, 2000, 3000]),
            np.array([1.000, 2.000, 3.000]),
            np.ndarray,
        ),
        (
            {"input_type": "numpy_scalar", "input_dtype": "int", "convert_output": True},
            np.array(1000).astype(np.int32),
            1.000,
            float,
        ),
        (
            {"input_type": "numpy_scalar", "input_dtype": "float", "convert_output": True},
            np.array(1000.5).astype(np.float32),
            1.000,
            float,
        ),
        (
            {"input_type": "numpy_scalar", "input_dtype": "int", "convert_output": False},
            np.array(1000).astype(np.uint32),
            1.000,
            np.float64,
        ),
    ],
)
def test_convert_time(config, input_value, expected_result, expected_type):
    """Verifies the functioning of the convert_time() function.

    Evaluates the following input scenarios:
        0 - Scalar int input, convert_output=True -> float
        1 - Scalar float input, convert_output=True -> float
        2 - Scalar int input, convert_output=False -> numpy float
        3 - List int input, convert_output=True -> tuple[float]
        4 - List float input, convert_output=True -> tuple[float]
        5 - One-item List int input, convert_output=False -> numpy float
        6 - One-item Numpy array int input, convert_output=True -> float
        7 - Numpy array float input, convert_output=True -> tuple[float]
        8 - Numpy array int input, convert_output=False -> numpy array [numpy float]
        9 - Numpy scalar signed int input, convert_output=True -> float
        10 - Numpy scalar float input, convert_output=True -> float
        11 - Numpy scalar unsigned int input, convert_output=False -> numpy float

    Args:
        config: The configuration for the test case.
        input_value: The input value to be converted.
        expected_result: The expected result after conversion.
        expected_type: The expected type of the result.
    """
    # Runs the converter
    result = convert_time(input_value, from_units="ms", to_units="s", convert_output=config["convert_output"])

    # Verifies the output type
    assert isinstance(result, expected_type)

    # Verifies the output value splitting for scalar / iterable outputs
    if isinstance(result, (float, np.float64)):
        assert result == expected_result
    elif isinstance(result, (list, np.ndarray)):
        assert np.allclose(result, expected_result)


def test_convert_time_errors() -> None:
    """Verifies the error-handling behavior of the convert_time() method."""

    # This dict is the same as the one used by the method. Here, it is used to reconstruct the expected error messages.
    conversion_dict: dict = {
        "d": 86400,  # seconds in a day
        "h": 3600,  # seconds in an hour
        "m": 60,  # seconds in a minute
        "s": 1,  # second
        "ms": 0.001,  # millisecond
        "us": 1e-6,  # microsecond
        "ns": 1e-9,  # nanosecond
    }

    # Tests multidimensional numpy array invalid 'time' argument input
    invalid_array = np.zeros(shape=(5, 5))
    message = (
        f"Unable to convert input time-values to the requested time-format. Expected a one-dimensional Python or "
        f"numpy iterable inputs as 'time', but encountered a numpy array with unsupported shape "
        f"({invalid_array.shape}) and dimensionality ({invalid_array.ndim})."
    )
    with pytest.raises(ValueError, match=error_format(message)):
        # noinspection PyTypeChecker
        convert_time(invalid_array, from_units="s", to_units="ms")

    # Tests general invalid 'time' argument type input.
    invalid_type = object()
    message = (
        f"Invalid 'time' argument type encountered when converting input time-values to the requested time-format. "
        f"Expected a valid Python or numpy numeric scalar or iterable with float-convertible elements as input, "
        f"but encountered {invalid_type} of type {type(invalid_type).__name__}."
    )
    with pytest.raises(TypeError, match=error_format(message)):
        # noinspection PyTypeChecker
        convert_time(invalid_type, from_units="s", to_units="ms")

    # Tests invalid 'from_units' argument value (and, indirectly, type).
    invalid_input: str = "invalid"
    message = (
        f"Unsupported 'from_units' argument value ({invalid_input}) encountered when converting input time-values to "
        f"the requested time-format. Use one of the supported time-units: {', '.join(conversion_dict.keys())}."
    )
    with pytest.raises(ValueError, match=error_format(message)):
        # noinspection PyTypeChecker
        convert_time(1, from_units=invalid_input, to_units="ms")

    # Tests invalid 'to_units' argument value (and, indirectly, type).
    message = (
        f"Unsupported 'to_units' argument value ({invalid_input}) encountered when converting input time-values to "
        f"the requested time-format. Use one of the supported time-units: {', '.join(conversion_dict.keys())}."
    )
    with pytest.raises(ValueError, match=error_format(message)):
        # noinspection PyTypeChecker
        convert_time(1, from_units="s", to_units=invalid_input)

    # Tests invalid element type inside a list 'time' argument input.
    message = (
        f"Invalid element type encountered in the input 'time' argument, when attempting to convert input "
        f"time-values to the requested time-format. After converting 'time' to a list and iterating over "
        f"elements, index {1} ({None}) of type {type(None).__name__} is not float-convertible."
    )
    invalid_list: list = [1, None, 3]
    with pytest.raises(TypeError, match=error_format(message)):
        # noinspection PyTypeChecker
        convert_time(invalid_list, from_units="s", to_units="ms")

    # Test invalid element type inside a numpy array 'time' argument input (uses the same error message as a list).
    invalid_array: np.ndarray = np.array([1, None, 3])
    with pytest.raises(TypeError, match=error_format(message)):
        # noinspection PyTypeChecker
        convert_time(invalid_array, from_units="s", to_units="ms")


def test_get_timestamp() -> None:
    """Verifies the functioning of the get_timestamp() method."""

    # Tests default separator with microseconds
    timestamp = get_timestamp()
    assert re.match(r"\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}-\d{6}", timestamp)

    # Tests custom separator with microseconds
    timestamp = get_timestamp(time_separator="_")
    assert re.match(r"\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}_\d{6}", timestamp)

    # Tests bytes output
    timestamp_bytes = get_timestamp(as_bytes=True)
    assert isinstance(timestamp_bytes, np.ndarray)
    assert timestamp_bytes.dtype == np.uint8

    # Verifies the bytes timestamp is the correct length (8 bytes for int64)
    assert len(timestamp_bytes) == 8


def test_extract_timestamp_from_bytes() -> None:
    """Verifies the functioning of the extract_timestamp_from_bytes() method."""

    # Gets a timestamp in bytes
    timestamp_bytes = get_timestamp(as_bytes=True)

    # Tests the default separator
    decoded = extract_timestamp_from_bytes(timestamp_bytes)
    assert re.match(r"\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}-\d{6}", decoded)

    # Tests a custom separator
    decoded = extract_timestamp_from_bytes(timestamp_bytes, time_separator="_")
    assert re.match(r"\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}_\d{6}", decoded)

    # Parses the decoded timestamp
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

    assert 2024 <= year <= 2025  # Valid year range
    assert 1 <= month <= 12  # Valid month
    assert 1 <= day <= 31  # Valid day
    assert 0 <= hour <= 23  # Valid hour
    assert 0 <= minute <= 59  # Valid minute
    assert 0 <= second <= 59  # Valid second
    assert 0 <= microsecond <= 999999  # Valid microseconds


def test_get_timestamp_errors() -> None:
    """Verifies the error-handling behavior of the get_timestamp() method."""

    # Tests invalid time_separator type
    invalid_time_separator: int = 123
    message = (
        f"Invalid 'time_separator' argument type encountered when attempting to obtain the current timestamp. "
        f"Expected {type(str).__name__}, but encountered {invalid_time_separator} of type "
        f"{type(invalid_time_separator).__name__}."
    )
    with pytest.raises(TypeError, match=error_format(message)):
        # noinspection PyTypeChecker
        get_timestamp(time_separator=invalid_time_separator)


def test_extract_timestamp_from_bytes_errors() -> None:
    """Verifies the error-handling behavior of the extract_timestamp_from_bytes() method."""

    # Tests invalid input type
    invalid_input = [1, 2, 3]  # List instead of numpy array
    message = (
        f"Invalid 'timestamp_bytes' argument type encountered when decoding timestamp from input bytes array. "
        f"Expected a one-dimensional uint8 numpy array, but got {invalid_input} of type "
        f"{type(invalid_input).__name__}."
    )
    with pytest.raises(TypeError, match=error_format(message)):
        # noinspection PyTypeChecker
        extract_timestamp_from_bytes(invalid_input)

    # Tests invalid numpy array (wrong size)
    invalid_array = np.array([1, 2, 3], dtype=np.uint8)  # Wrong size
    with pytest.raises(ValueError):
        extract_timestamp_from_bytes(invalid_array)


def test_timestamp_roundtrip() -> None:
    """Verifies that encoding and decoding a timestamp preserves the information."""

    # Gets current timestamp in bytes
    timestamp_bytes = get_timestamp(as_bytes=True)

    # Decodes it back to string
    decoded = extract_timestamp_from_bytes(timestamp_bytes)

    # Gets a fresh timestamp for comparison structure
    fresh = get_timestamp()

    # Verifies the structure matches (same number of components, same separators)
    assert len(decoded.split("-")) == len(fresh.split("-"))

    # Verifies the decoded timestamp represents a valid datetime
    components = decoded.split("-")
    dt = datetime(
        year=int(components[0]),
        month=int(components[1]),
        day=int(components[2]),
        hour=int(components[3]),
        minute=int(components[4]),
        second=int(components[5]),
        microsecond=int(components[6]),
    )
    assert isinstance(dt, datetime)
