"""This module provides the PrecisionTimer class that provides a high-level API for accessing the bound C++ timer's
functionality.
"""

from enum import StrEnum

from ataraxis_base_utilities import console

from ..precision_timer_ext import CPrecisionTimer  # type: ignore[import-not-found]


class TimerPrecisions(StrEnum):
    """Stores the timer precision modes supported by the PrecisionTimer instances.

    Use this enumeration when initializing or reconfiguring the precision used by a PrecisionTimer instance.
    """

    NANOSECOND = "ns"
    MICROSECOND = "us"
    MILLISECOND = "ms"
    SECOND = "s"


class PrecisionTimer:
    """Provides high-precision interval-timing and delay functionality.

    This class functions as an interface wrapper for a C++ class that uses the 'chrono' library to interface with the
    highest available precision clock of the host system.

    Notes:
        The precision of all class methods depends on the precision and frequency of the system's CPU. It is highly
        advised to benchmark the class before deploying it in time-critical projects to characterize the overhead
        associated with using different timer methods.

    Attributes:
        _timer: Stores the nanobind-generated C-extension timer class.

    Args:
        precision: The desired precision of the timer. Use one of the supported values defined in the TimerPrecisions
            enumeration. Currently, accepted precision values are 'ns' (nanoseconds), 'us' (microseconds),
            'ms' (milliseconds), and 's' (seconds).

    Raises:
        ValueError: If the input precision is not one of the accepted options.
    """

    def __init__(self, precision: str | TimerPrecisions = TimerPrecisions.MICROSECOND) -> None:
        # If the input precision is not supported, raises an error.
        if precision not in tuple(TimerPrecisions):
            message = (
                f"Unsupported precision argument value ({precision}) encountered when initializing PrecisionTimer "
                f"class. Use one of the supported precision options defined in the TimerPrecisions enumeration: "
                f"{tuple(TimerPrecisions)}."
            )
            console.error(message=message, error=ValueError)

        # Ensures that the precision is stored as a Precision enumeration instance.
        precision = TimerPrecisions(precision)

        # Otherwise, initializes the C++ class using the input precision.
        self._timer = CPrecisionTimer(precision=precision.value)

    def __repr__(self) -> str:
        """Returns a string representation of the instance."""
        return f"PrecisionTimer(precision={self.precision}, elapsed_time = {self.elapsed} {self.precision}.)"

    @property
    def elapsed(self) -> int:
        """Returns the time elapsed since class instantiation or the last reset() method call,
        whichever happened last.
        """
        return int(self._timer.Elapsed())

    @property
    def precision(self) -> str:
        """Returns the units currently used by the instance as a string ('ns', 'us', 'ms', or 's')."""
        return str(self._timer.GetPrecision())

    def reset(self) -> None:
        """Resets the timer."""
        self._timer.Reset()

    def delay(self, delay: int, *, allow_sleep: bool = False, block: bool = False) -> None:
        """Delays program execution for the requested period of time.

        Args:
            delay: The integer period of time to wait for. The method assumes the delay is given in the same precision
                units as used by the instance.
            allow_sleep: A boolean flag that allows releasing the CPU while suspending execution for durations above 1
                millisecond.
            block: Determines whether to hold (if True) or release (if False) the Global Interpreter Lock (GIL) during
                the delay. Releasing the GIL allows other Python threads to run in parallel with the delay.
        """
        self._timer.Delay(delay, allow_sleep, block)

    def set_precision(self, precision: str | TimerPrecisions) -> None:
        """Changes the precision used by the timer to the input option.

        Args:
            precision: The desired precision of the timer. Use one of the supported values defined in the
                TimerPrecisions enumeration. Currently, accepted precision values are 'ns' (nanoseconds), 'us'
                (microseconds), 'ms' (milliseconds), and 's' (seconds).

        Raises:
            ValueError: If the input precision is not one of the accepted options.
        """
        # If the input precision is not supported, raises an error.
        if precision not in tuple(TimerPrecisions):
            message = (
                f"Unsupported precision argument value ({precision}) encountered when initializing PrecisionTimer "
                f"class. Use one of the supported precision options defined in the TimerPrecisions enumeration: "
                f"{tuple(TimerPrecisions)}."
            )
            console.error(message=message, error=ValueError)

        # Ensures that the precision is stored as a TimerPrecisions enumeration instance.
        precision = TimerPrecisions(precision)

        # Otherwise, updates the precision used by the C++ class.
        self._timer.SetPrecision(precision=precision.value)
