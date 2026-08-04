"""Provides the PrecisionTimer class, the Timeout guard, the TimerPrecisions enumeration, and the timer benchmark."""

from .timer import PrecisionTimer, TimerPrecisions
from .timeout import Timeout

__all__ = ["PrecisionTimer", "Timeout", "TimerPrecisions"]
