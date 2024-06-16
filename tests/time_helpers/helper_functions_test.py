"""Tests the functions available through the 'helper_functions' module."""

import re

import numpy as np
import pytest  # type: ignore
from ataraxis_time.time_helpers import convert_time, get_timestamp
from ataraxis_time.utilities import format_message


def test_convert_time() -> None:
    """Verifies the functioning of the convert_timer() method."""

    # Tests scalar inputs (integers and floats)
    assert convert_time(1, from_units="s", to_units="ms") == 1000.0
    assert convert_time(1.5, from_units="m", to_units="s") == 90.0

    # Tests list inputs (integers, floats and float-convertible strings)
    assert convert_time([1, "2", 3], from_units="s", to_units="ms") == [1000.0, 2000.0, 3000.0]
    assert convert_time([1.5, 2.5, "3.5"], from_units="m", to_units="s") == [90.0, 150.0, 210.0]
    # Scalar-convertible array, should be processed like an array
    assert convert_time([1], from_units="s", to_units="ms") == [1000.0]

    # Tests numpy array inputs (integer and float)
    assert np.allclose(
        convert_time(np.array([1, 2, 3]), from_units="s", to_units="ms"), np.array([1000.0, 2000.0, 3000.0])
    )
    assert np.allclose(
        convert_time(np.array([1.5, 2.5, 3.5]), from_units="m", to_units="s"), np.array([90.0, 150.0, 210.0])
    )


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

    # Tests invalid 'time' argument type input.
    invalid_type: str = "1"
    custom_error_message = (
        f"Invalid 'time' argument type encountered when converting input time-values to the requested time-format. "
        f"Expected {type(int)}, {type(float)}, {type(list)} or {type(np.ndarray)} but encountered {invalid_type} of "
        f"type {type(invalid_type)}."
    )
    with pytest.raises(TypeError, match=re.escape(format_message(custom_error_message))):
        # noinspection PyTypeChecker
        convert_time(invalid_type, from_units="s", to_units="ms")

    # Tests invalid 'from_units' argument value (and, indirectly, type).
    invalid_input: str = "invalid"
    custom_error_message = (
        f"Unsupported 'from_units' argument value ({invalid_input}) encountered when converting input time-values to "
        f"the requested time-format. Use one of the supported time-units: {', '.join(conversion_dict.keys())}."
    )
    with pytest.raises(ValueError, match=re.escape(format_message(custom_error_message))):
        # noinspection PyTypeChecker
        convert_time(1, from_units=invalid_input, to_units="ms")

    # Tests invalid 'to_units' argument value (and, indirectly, type).
    custom_error_message = (
        f"Unsupported 'to_units' argument value ({invalid_input}) encountered when converting input time-values to "
        f"the requested time-format. Use one of the supported time-units: {', '.join(conversion_dict.keys())}."
    )
    with pytest.raises(ValueError, match=re.escape(format_message(custom_error_message))):
        # noinspection PyTypeChecker
        convert_time(1, from_units="s", to_units=invalid_input)

    # Tests invalid element type inside a list 'time' argument input.
    custom_error_message = (
        f"Invalid element type encountered in the input 'time' list or numpy array, when attempting to "
        f"convert input time-values to the requested time-format. Element index {1} ({None}) of type "
        f"{type(None)} is not float-convertible."
    )
    invalid_list: list = [1, None, 3]
    with pytest.raises(TypeError, match=re.escape(format_message(custom_error_message))):
        convert_time(invalid_list, from_units="s", to_units="ms")

    # Test invalid element type inside a numpy array 'time' argument input (uses the same error message as a list).
    invalid_array: np.ndarray = np.array([1, None, 3])
    with pytest.raises(TypeError, match=re.escape(format_message(custom_error_message))):
        convert_time(invalid_array, from_units="s", to_units="ms")


def test_get_timestamp() -> None:
    """Verifies the functioning of the get_timestamp() method."""

    # Tests default separator
    timestamp = get_timestamp()
    assert re.match(r"\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}", timestamp)

    # Tests separator override
    timestamp = get_timestamp(time_separator="_")
    assert re.match(r"\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}", timestamp)


def test_get_timestamp_errors() -> None:
    """Verifies the error-handling behavior of the get_timestamp() method."""
    # Tests invalid time_separator type
    invalid_time_separator: int = 123
    custom_error_message = (
        f"Invalid 'time_separator' argument type encountered when attempting to obtain the current timestamp. "
        f"Expected {type(str)}, but encountered {invalid_time_separator} of type {type(invalid_time_separator)}."
    )
    with pytest.raises(TypeError, match=re.escape(format_message(custom_error_message))):
        # noinspection PyTypeChecker
        get_timestamp(time_separator=invalid_time_separator)
