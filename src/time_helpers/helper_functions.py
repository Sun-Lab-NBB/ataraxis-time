"""This module contains helper functions used to work with date and time data.

These functions are included as convenience methods that are expected to be frequently used both together with and
independently of the PrecisionTimer class. Unlike PrecisionTimer class, they are not expected to be actively used
in real-time runtimes and are implemented using pure-python API where possible.
"""

from typing import Any, Union, Literal
from datetime import datetime

import numpy as np
from numpy.typing import NDArray
from ataraxis_base_utilities import console, ensure_list


def convert_time(
    time: Union[
        int,
        float,
        list[int | float],
        tuple[int | float],
        np.signedinteger[Any],
        np.unsignedinteger[Any],
        np.floating[Any],
        NDArray[np.signedinteger[Any] | np.unsignedinteger[Any] | np.floating[Any]],
    ],
    from_units: Literal["ns", "us", "ms", "s", "m", "h", "d"],
    to_units: Literal["ns", "us", "ms", "s", "m", "h", "d"],
    *,
    convert_output: bool = True,
) -> float | tuple[float] | NDArray[np.float64] | np.float64:
    """Converts the input time value(s) from the original units to the requested units.

    Supports conversion in the range from days to nanoseconds and uses numpy under-the-hood to optimize runtime speed.
    Since the function always converts input data to numpy arrays, it can be configured to return data using either
    numpy or python formats. If the data can be returned as a scalar, it will be returned as a scalar, even if the
    input was iterable (e.g.: a one-element list).

    Notes:
        While this function accepts numpy arrays, it expects them to be one-dimensional. To pass a multidimensional
        numpy array through this function, first flatten the array into one dimension.

        The conversion uses 3 decimal places rounding, which may introduce inaccuracies in some cases.

    Args:
        time: A scalar Python or numpy numeric time-value to convert. Alternatively, can be Python or numpy iterable
            that contains float-convertible numeric values. Input numpy arrays have to be one-dimensional.
        from_units: The units used by the input data. Valid options are: 'ns' (nanoseconds), 'us' (microseconds),
            'ms' (milliseconds), 's' (seconds), 'm' (minutes), 'h' (hours), 'd' (days).
        to_units: The units to convert the input data to. Uses the same options as from_units.
        convert_output: Determines whether to convert output to a Python scalar / iterable type or to return it as a
            numpy type.

    Returns:
        The converted time in the requested units using either python 'float' or numpy 'float64' format. The returned
        data will be a scalar, if possible. If not, it will be a tuple (when the function is configured to return
        Python types) or a numpy array (when the function is configured to return numpy types).

    Raises:
        TypeError: If 'time' argument is not of a valid type. If time contains elements that are not float-convertible.
        ValueError: If 'from_units' or 'to_units' argument is not set to a valid time-option. If time is a
            multidimensional numpy array.
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

    # Prevents the function from working with multidimensional numpy arrays.
    if isinstance(time, np.ndarray) and time.ndim > 1:
        message = (
            f"Unable to convert input time-values to the requested time-format. Expected a one-dimensional Python or "
            f"numpy iterable inputs as 'time', but encountered a numpy array with unsupported shape ({time.shape}) and "
            f"dimensionality ({time.ndim})."
        )
        console.error(message=message, error=ValueError)

    # Verifies that the input time uses a valid type. To do so, attempts to cast the input into a python list. This
    # will generally 'pass' more arguments than desired, so there are extra checks below to further filter the input
    # types.
    try:
        time_list = ensure_list(time)

    except TypeError:
        message = (
            f"Invalid 'time' argument type encountered when converting input time-values to the requested time-format. "
            f"Expected a valid Python or numpy numeric scalar or iterable with float-convertible elements as input, "
            f"but encountered {time} of type {type(time).__name__}."
        )
        console.error(message=message, error=TypeError)
        # Fallback to appease mypy, should not be reachable
        raise TypeError(message)  # pragma: no cover

    # Verifies that unit-options are valid.
    if from_units not in conversion_dict.keys():
        message = (
            f"Unsupported 'from_units' argument value ({from_units}) encountered when converting input time-values to "
            f"the requested time-format. Use one of the supported time-units: {', '.join(conversion_dict.keys())}."
        )
        console.error(message=message, error=ValueError)

    if to_units not in conversion_dict.keys():
        message = (
            f"Unsupported 'to_units' argument value ({to_units}) encountered when converting input time-values to "
            f"the requested time-format. Use one of the supported time-units: {', '.join(conversion_dict.keys())}."
        )
        console.error(message=message, error=ValueError)

    # Next, loops over each element of the list generated above and verifies that it is float-convertible by
    # attempting to convert it to a float type. If conversion fails, raises a TypeError.
    for num, element in enumerate(time_list):
        try:
            float(element)
        except BaseException:
            message = (
                f"Invalid element type encountered in the input 'time' argument, when attempting to convert input "
                f"time-values to the requested time-format. After converting 'time' to a list and iterating over "
                f"elements, index {num} ({element}) of type {type(element).__name__} is not float-convertible."
            )
            console.error(message=message, error=TypeError)

    # If all values pass validation, converts the input list or array into a float numpy array
    time = np.array(time_list, dtype=np.float64)

    # Converts the time to the desired time format and rounds the resultant values to 3 decimal points.
    converted_time: NDArray[np.float64] = np.round(
        (time * conversion_dict[from_units]) / conversion_dict[to_units],
        decimals=3,
    )

    if convert_output:
        if converted_time.size != 1:
            # Converts an array with multiple elements to tuple
            return tuple(converted_time.tolist())
        else:
            # This pops the only element out as the nearest Python type (float)
            return converted_time.item()
    else:
        if converted_time.size != 1:
            # This returns numpy array with a float64 type
            return converted_time
        else:
            # This returns a float64 scalar type.
            return np.float64(converted_time[0])


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
        message = (
            f"Invalid 'time_separator' argument type encountered when attempting to obtain the current timestamp. "
            f"Expected {type(str).__name__}, but encountered {time_separator} of type {type(time_separator).__name__}."
        )
        console.error(message=message, error=TypeError)

    # Obtains and formats date and time to be appended to various file and directory variables
    now: datetime = datetime.now()
    timestamp: str = now.strftime(
        f"%Y{time_separator}%m{time_separator}%d{time_separator}%H{time_separator}%M{time_separator}%S"
    )

    return timestamp
