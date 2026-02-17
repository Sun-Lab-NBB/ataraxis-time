"""Provides the PrecisionTimer class that exposes a high-level API for the bound C++ timer's functionality."""

from enum import StrEnum
from collections.abc import Generator

from ataraxis_base_utilities import console

from ..precision_timer_ext import CPrecisionTimer  # type: ignore[import-not-found]
from ..utilities.time_utilities import convert_time


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
        _laps: A list of recorded lap times.

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

        # Initializes the lap tracking list.
        self._laps: list[int] = []

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
        """Resets the timer and clears all recorded laps."""
        self._timer.Reset()
        self._laps.clear()

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

    def format_elapsed(self, *, max_fields: int = 2) -> str:
        """Returns the current elapsed time as a human-readable string.

        Converts the elapsed time to seconds internally, then breaks it into descending unit components
        (d, h, m, s, ms, us, ns). Auto-selects the largest non-zero unit as the starting point and includes
        up to max_fields unit segments.

        Args:
            max_fields: The maximum number of unit segments to include in the output. Defaults to 2, e.g.
                "2 h 30 m" instead of "2 h 30 m 15 s 200 ms".

        Returns:
            A human-readable string representation of the elapsed time, e.g. "2 h 30 m", "1.5 ms", "500 ns".
        """
        # Gets the current elapsed time and converts it to seconds for uniform processing.
        elapsed = self.elapsed
        precision = self.precision
        elapsed_seconds = float(convert_time(elapsed, from_units=precision, to_units="s", as_float=True))

        # Defines units in descending order with their second-based thresholds.
        units: list[tuple[str, float]] = [
            ("d", 86400.0),
            ("h", 3600.0),
            ("m", 60.0),
            ("s", 1.0),
            ("ms", 0.001),
            ("us", 1e-6),
            ("ns", 1e-9),
        ]

        # Handles zero elapsed time.
        if elapsed_seconds == 0:
            return f"0 {precision}"

        # Decomposes the elapsed seconds into unit components.
        remaining = elapsed_seconds
        parts: list[str] = []
        for unit_name, unit_seconds in units:
            if len(parts) >= max_fields:  # pragma: no cover
                break
            if remaining >= unit_seconds:
                count = remaining / unit_seconds
                if len(parts) == max_fields - 1 or unit_name == units[-1][0]:
                    # Last field: use decimal representation for remainder.
                    # Rounds to avoid floating point noise.
                    rounded = round(count, 3)
                    # Uses integer representation if the value is a whole number.
                    if rounded == int(rounded):  # pragma: no cover
                        parts.append(f"{int(rounded)} {unit_name}")
                    else:
                        parts.append(f"{rounded} {unit_name}")
                    break
                whole = int(count)
                if whole > 0:
                    parts.append(f"{whole} {unit_name}")
                    remaining -= whole * unit_seconds

        return " ".join(parts)

    def lap(self) -> int:
        """Records the current elapsed time as a lap, resets the timer, and returns the lap duration.

        Returns:
            The elapsed time captured as the lap duration, in the timer's current precision units.
        """
        duration = self.elapsed
        self._laps.append(duration)
        self._timer.Reset()
        return duration

    @property
    def laps(self) -> tuple[int, ...]:
        """Returns all recorded lap times as a tuple."""
        return tuple(self._laps)

    def poll(self, interval: int, *, allow_sleep: bool = True, block: bool = False) -> Generator[int, None, None]:
        """Infinite generator that yields an iteration count after each delay cycle.

        Each iteration calls self.delay() with the specified interval and parameters. The caller should break
        out of the loop when done.

        Args:
            interval: The delay interval in the timer's current precision units.
            allow_sleep: A boolean flag that allows releasing the CPU while suspending execution for durations above
                1 millisecond.
            block: Determines whether to hold or release the GIL during the delay.

        Yields:
            The iteration count (starting from 1) after each delay cycle.
        """
        count = 0
        while True:
            self.delay(interval, allow_sleep=allow_sleep, block=block)
            count += 1
            yield count
