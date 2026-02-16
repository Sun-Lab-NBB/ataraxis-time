"""Provides the PrecisionTimer class, Timeout guard, and support functions for timer usage and benchmarking."""

from .timer import PrecisionTimer, TimerPrecisions
from .timeout import Timeout

__all__ = ["PrecisionTimer", "Timeout", "TimerPrecisions"]
