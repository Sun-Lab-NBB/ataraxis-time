"""This module contains helper functions used to work with date and time data.

These functions are included as convenience methods that are expected to be frequently used both together with and
independently of the PrecisionTimer class. Unlike PrecisionTimer class, they are not expected to be actively used
in real-time runtimes and are implemented using pure-python API where possible.
"""

from datetime import datetime
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from ..utilities import format_message


def convert_time(
    time: (
        int
        | float
        | NDArray[
            np.int8
            | np.int16
            | np.int32
            | np.int64
            | np.uint8
            | np.uint16
            | np.uint32
            | np.uint64
            | np.float16
            | np.float32
            | np.float64
        ]
        | list[int | float]
    ),
    from_units: Literal["ns", "us", "ms", "s", "m", "h", "d"],
    to_units: Literal["ns", "us", "ms", "s", "m", "h", "d"],
) -> float | NDArray[np.float64] | list[float]:
    """Converts the input time_values from the original units to the desired units.

    Supports conversion in the range from days to nanoseconds and uses numpy under-the-hood to optimize runtimes.

    Notes:
        The conversion uses 3 decimal places rounding, which may introduce inaccuracies in some cases.

    Args:
        time: An integer or float time-value. Alternatively, can be a numpy ndarray or python list of integer, float or
            any other float-convertible value type (e.g.: '1' string) values.
        from_units: The units used by the input data. Valid options are: 'ns' (nanoseconds), 'us' (microseconds),
            'ms' (milliseconds), 's' (seconds), 'm' (minutes), 'h' (hours), 'd' (days).
        to_units: The units to convert the input data to. Uses the same options as from_units.

    Returns:
        The converted time in the requested units using float format if the input vas a scalar, list format if the input
        was a python list and numpy array format if the input was a numpy array.

    Raises:
        TypeError: If 'time' argument is not of a valid type. Also, if any time list / numpy array elements are not
            float-convertible.
        ValueError: If 'from_units' or 'to_units' argument is not set to a valid time-option.
    """
    conversion_dict: dict[str, int | float] = {
        "d": 86400,  # seconds in a day
        "h": 3600,  # seconds in an hour
        "m": 60,  # seconds in a minute
        "s": 1,  # second
        "ms": 0.001,  # millisecond
        "us": 1e-6,  # microsecond
        "ns": 1e-9,  # nanosecond
    }

    # Verifies that the input time uses a valid type. There are additional checks for the list and numpy array inputs
    # below.
    if not isinstance(time, (int, float, list, np.ndarray)):
        custom_error_message = (
            f"Invalid 'time' argument type encountered when converting input time-values to the requested time-format. "
            f"Expected {type(int)}, {type(float)}, {type(list)} or {type(np.ndarray)} but encountered {time} of type "
            f"{type(time)}."
        )
        raise TypeError(format_message(custom_error_message))

    # Verifies that unit-options are valid.
    if from_units not in conversion_dict.keys():
        custom_error_message = (
            f"Unsupported 'from_units' argument value ({from_units}) encountered when converting input time-values to "
            f"the requested time-format. Use one of the supported time-units: {', '.join(conversion_dict.keys())}."
        )
        raise ValueError(format_message(custom_error_message))
    if to_units not in conversion_dict.keys():
        custom_error_message = (
            f"Unsupported 'to_units' argument value ({to_units}) encountered when converting input time-values to "
            f"the requested time-format. Use one of the supported time-units: {', '.join(conversion_dict.keys())}."
        )
        raise ValueError(format_message(custom_error_message))

    # If input time is a python list or a numpy array, attempts to convert it to a float-64 numpy array.
    is_list: bool = False
    if isinstance(time, (list, np.ndarray)):
        # First, loops over each element and verifies that it is float-convertible by attempting to convert it to a
        # float type. If conversion fails, raises a TypeError.
        for num, element in enumerate(time):
            try:
                float(element)
            except Exception:
                custom_error_message = (
                    f"Invalid element type encountered in the input 'time' list or numpy array, when attempting to "
                    f"convert input time-values to the requested time-format. Element index {num} ({element}) of type "
                    f"{type(element)} is not float-convertible."
                )
                raise TypeError(format_message(custom_error_message))

        # If all values pass validation, converts the input list or array into a float numpy array
        if isinstance(time, list):
            # For a list, generates a new numpy array object
            time = np.array(time, dtype=np.float64)
            is_list = True  # Also sets the tracker used to convert the processed data back to list before returning
        else:
            # For the array, uses built-in as-type caster
            time = time.astype(np.float64)

    # Converts the time to the desired time format and rounds the resultant values to 3 decimal points. If the input was
    # a scalar (integer or float), it will use numpy float64 output type. Otherwise, it would be a numpy array using
    # float_64 type.
    converted_time: NDArray[np.float64] | np.float64 = np.round(
        (time * conversion_dict[from_units]) / conversion_dict[to_units],
        decimals=3,
    )
    if not isinstance(converted_time, np.ndarray):
        # Converts numpy scalars to pythonic floats before returning them
        return float(converted_time)
    elif is_list:
        # noinspection PyTypeChecker
        float_list: list[float] = converted_time.tolist()
        # If the input time was a list, converts it back to list format
        return float_list
    else:
        # If the input was a numpy array, keeps it as a numpy array
        return converted_time


def get_timestamp(time_separator: str = "-") -> str:
    """Gets the current date and time (to seconds) and formats it into year-month-day-hour-minute-second string.

    This utility method can be used to quickly time-stamp events and should be decently fast as it links to a
    C-extension under the hood.

    Args:
        time_separator: The separator to use to separate the components of the time-string. Defaults to hyphens "-".

    Notes:
        Hyphen-separation is supported by the majority of modern OSes and, therefore, the default separator should be
        safe for most use cases. That said, the method does not evaluate the separator for compatibility with the
        OS-reserved symbols and treats it as a generic string to be inserted between time components. Therefore, it is
        advised to make sure that the separator is a valid string given your OS and Platform combination.

    Returns:
        The 'year-month-day-hour-minute-second' string that uses the input timer-separator to separate time-components.

    Raises:
        TypeError: If the time_separator argument is not a string.

    """
    # Verifies that time-separator is of a valid type
    if not isinstance(time_separator, str):
        custom_error_message = (
            f"Invalid 'time_separator' argument type encountered when attempting to obtain the current timestamp. "
            f"Expected {type(str)}, but encountered {time_separator} of type {type(time_separator)}."
        )
        raise TypeError(format_message(custom_error_message))

    # Obtains and formats date and time to be appended to various file and directory variables
    now: datetime = datetime.now()
    timestamp: str = now.strftime(
        f"%Y{time_separator}%m{time_separator}%d{time_separator}%H{time_separator}%M{time_separator}%S"
    )

    return timestamp
