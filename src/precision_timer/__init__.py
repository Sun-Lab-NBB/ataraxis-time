"""This package contains the PrecisionTimer class with various support functions (such as benchmark() function used to
evaluate class performance).

PrecisionTimer class acts as the main API access point that allows using the C-bindings for the core fast timer class
written in C++. It is highly advised to carry out all timer-related operations through this high-level API.
"""

from .timer_class import PrecisionTimer
from .timer_benchmark import benchmark

__all__ = ["PrecisionTimer", "benchmark"]
