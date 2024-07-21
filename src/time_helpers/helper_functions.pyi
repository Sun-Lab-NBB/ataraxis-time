from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray

def convert_time(
    time: int
    | float
    | list[int | float]
    | tuple[int | float]
    | np.signedinteger[Any]
    | np.unsignedinteger[Any]
    | np.floating[Any]
    | NDArray[np.signedinteger[Any] | np.unsignedinteger[Any] | np.floating[Any]],
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
        The \'year-month-day-hour-minute-second\' string that uses the input timer-separator to separate time-components.

    Raises:
        TypeError: If the time_separator argument is not a string.

    """
