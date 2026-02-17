from enum import StrEnum
from typing import Any
import datetime

import numpy as np
from numpy.typing import NDArray as NDArray

_DT_MAX_PARTS: int

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

class TimestampPrecisions(StrEnum):
    YEAR = "year"
    MONTH = "month"
    DAY = "day"
    HOUR = "hour"
    MINUTE = "minute"
    SECOND = "second"
    MICROSECOND = "microsecond"

_PRECISION_PARTS: dict[str, int]

def convert_time(
    time: float | np.integer[Any] | np.floating[Any],
    from_units: str | TimeUnits,
    to_units: str | TimeUnits,
    *,
    as_float: bool = False,
) -> float | np.float64: ...
def get_timestamp(
    output_format: str | TimestampFormats = ..., time_separator: str = "-", precision: str | TimestampPrecisions = ...
) -> str | int | NDArray[np.uint8]: ...
def convert_timestamp(
    timestamp: str | int | NDArray[np.uint8],
    time_separator: str = "-",
    output_format: str | TimestampFormats = ...,
    precision: str | TimestampPrecisions = ...,
) -> str | int | NDArray[np.uint8]: ...
def parse_timestamp(
    date_string: str,
    format_string: str,
    *,
    output_format: str | TimestampFormats = ...,
    time_separator: str = "-",
    precision: str | TimestampPrecisions = ...,
) -> str | int | NDArray[np.uint8]: ...
def rate_to_interval(
    rate: float | np.integer[Any] | np.floating[Any], to_units: str | TimeUnits = ..., *, as_float: bool = False
) -> float | np.float64: ...
def interval_to_rate(
    interval: float | np.integer[Any] | np.floating[Any], from_units: str | TimeUnits = ..., *, as_float: bool = False
) -> float | np.float64: ...
def to_timedelta(
    time: float | np.integer[Any] | np.floating[Any], from_units: str | TimeUnits
) -> datetime.timedelta: ...
def from_timedelta(
    timedelta_value: datetime.timedelta, to_units: str | TimeUnits, *, as_float: bool = False
) -> float | np.float64: ...
def _truncate_microseconds(microseconds: int, precision: str) -> int: ...
