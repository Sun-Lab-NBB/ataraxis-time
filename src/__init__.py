"""A Python library that provides a high-precision thread-safe timer and helper methods to work with date and time
data.

See https://github.com/Sun-Lab-NBB/ataraxis-time for more details.
API documentation: https://ataraxis-time-api-docs.netlify.app/
Author: Ivan Kondratyev (Inkaros)
"""

from .time_helpers import TimeUnits, TimestampFormats, convert_time, get_timestamp, convert_timestamp
from .precision_timer import PrecisionTimer, TimerPrecisions

__all__ = [
    "PrecisionTimer",
    "TimeUnits",
    "TimerPrecisions",
    "TimestampFormats",
    "convert_time",
    "convert_timestamp",
    "get_timestamp",
]
