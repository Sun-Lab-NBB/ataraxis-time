"""Provides the PrecisionTimer class that exposes a high-level API for the bound C++ timer's functionality."""

from enum import StrEnum

from ataraxis_base_utilities import console

from ..precision_timer_ext import CPrecisionTimer  # type: ignore[import-not-found]


class TimerPrecisions(StrEnum):
    """Defines the timer precision modes supported by PrecisionTimer instances.

    Use this enumeration when initializing or reconfiguring the precision used by a PrecisionTimer instance.
    """

    NANOSECOND = "ns"
    """Nanosecond precision."""
    MICROSECOND = "us"
    """Microsecond precision."""
    MILLISECOND = "ms"
    """Millisecond precision."""
    SECOND = "s"
    """Second precision."""


class PrecisionTimer:
    """Provides high-precision interval-timing and delay functionality.

    This class functions as an interface wrapper for a C++ class that uses the 'chrono' library to interface with the
    highest available precision clock of the host system.

    Notes:
        The precision of all class methods depends on the precision and frequency of the system's CPU. It is highly
        advised to benchmark the class before deploying it in time-critical projects to characterize the overhead
        associated with using different timer methods.

    Args:
        precision: The desired precision of the timer. Use one of the supported values defined in the TimerPrecisions
            enumeration. Currently, accepted precision values are 'ns' (nanoseconds), 'us' (microseconds),
            'ms' (milliseconds), and 's' (seconds).

    Attributes:
        _timer: The nanobind-generated C-extension timer class.

    Raises:
        ValueError: If the input precision is not one of the accepted options.
    """

    def __init__(self, precision: str | TimerPrecisions = TimerPrecisions.MICROSECOND) -> None:
        # Validates the input precision against supported options.
        if precision not in tuple(TimerPrecisions):
            message = (
                f"Unable to initialize PrecisionTimer class. The precision must be one of the supported options "
                f"defined in the TimerPrecisions enumeration ({tuple(TimerPrecisions)}), but got {precision}."
            )
            console.error(message=message, error=ValueError)

        # Converts the precision to a TimerPrecisions enumeration instance.
        precision = TimerPrecisions(precision)

        # Initializes the C++ timer class with the validated precision.
        self._timer = CPrecisionTimer(precision=precision.value)

    def __repr__(self) -> str:
        """Returns a string representation of the PrecisionTimer instance."""
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
        self._timer.Delay(duration=delay, allow_sleep=allow_sleep, block=block)

    def set_precision(self, precision: str | TimerPrecisions) -> None:
        """Changes the precision used by the timer to the input option.

        Args:
            precision: The desired precision of the timer. Use one of the supported values defined in the
                TimerPrecisions enumeration. Currently, accepted precision values are 'ns' (nanoseconds), 'us'
                (microseconds), 'ms' (milliseconds), and 's' (seconds).

        Raises:
            ValueError: If the input precision is not one of the accepted options.
        """
        # Validates the input precision against supported options.
        if precision not in tuple(TimerPrecisions):
            message = (
                f"Unable to set PrecisionTimer precision. The precision must be one of the supported options "
                f"defined in the TimerPrecisions enumeration ({tuple(TimerPrecisions)}), but got {precision}."
            )
            console.error(message=message, error=ValueError)

        # Converts the precision to a TimerPrecisions enumeration instance.
        precision = TimerPrecisions(precision)

        # Updates the precision used by the C++ timer class.
        self._timer.SetPrecision(precision=precision.value)
