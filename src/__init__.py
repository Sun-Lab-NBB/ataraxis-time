"""Provides a high-precision thread-safe timer and helper methods to work with date and time data.

See the `documentation <https://ataraxis-time-api-docs.netlify.app/>`_ for the description of available assets. See
the `source code repository <https://github.com/Sun-Lab-NBB/ataraxis-time>`_ for more details.

Authors: Ivan Kondratyev (Inkaros)
"""

from .timers import Timeout, PrecisionTimer, TimerPrecisions
from .utilities import (
    TimeUnits,
    TimestampFormats,
    TimestampPrecisions,
    convert_time,
    to_timedelta,
    get_timestamp,
    from_timedelta,
    parse_timestamp,
    interval_to_rate,
    rate_to_interval,
    convert_timestamp,
)

__all__ = [
    "PrecisionTimer",
    "TimeUnits",
    "Timeout",
    "TimerPrecisions",
    "TimestampFormats",
    "TimestampPrecisions",
    "convert_time",
    "convert_timestamp",
    "from_timedelta",
    "get_timestamp",
    "interval_to_rate",
    "parse_timestamp",
    "rate_to_interval",
    "to_timedelta",
]
