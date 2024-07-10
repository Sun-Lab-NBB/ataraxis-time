"""This library provides a sub-microsecond-precise thread-safe timer and helper methods to work with date and
time data.

See https://github.com/Sun-Lab-NBB/ataraxis-time for more details.
API documentation: https://ataraxis-time-api-docs.netlify.app/
Author: Ivan Kondratyev (Inkaros)
"""

from .precision_timer import PrecisionTimer, benchmark

__all__ = ["PrecisionTimer", "benchmark"]
