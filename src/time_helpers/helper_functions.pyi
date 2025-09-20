from enum import StrEnum
from typing import Any

import numpy as np
from numpy.typing import NDArray as NDArray

_DT_STRING_PARTS: int

class TimeUnits(StrEnum):
    NANOSECOND = "ns"
    MICROSECOND = "us"
    MILLISECOND = "ms"
    SECOND = "s"
    MINUTE = "m"
    HOUR = "h"
    DAY = "d"

class TimestampFormats(StrEnum):
    STRING = "str"
    BYTES = "byte"
    INTEGER = "int"

def convert_time(
    time: float | np.integer[Any] | np.floating[Any],
    from_units: str | TimeUnits,
    to_units: str | TimeUnits,
    *,
    as_float: bool = False,
) -> float | np.float64: ...
def get_timestamp(
    output_format: str | TimestampFormats = ..., time_separator: str = "-"
) -> str | int | NDArray[np.uint8]: ...
def convert_timestamp(
    timestamp: str | int | NDArray[np.uint8], time_separator: str = "-", output_format: str | TimestampFormats = ...
) -> str | int | NDArray[np.uint8]: ...
