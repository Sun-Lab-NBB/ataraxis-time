"""Provides the PrecisionTimer class that exposes a high-level API for the bound C++ timer's functionality."""

from enum import StrEnum
from collections.abc import Generator

from ataraxis_base_utilities import console

from ..precision_timer_ext import CPrecisionTimer  # type: ignore[import-not-found]

_NANOSECONDS_PER_UNIT: dict[str, int] = {"ns": 1, "us": 1_000, "ms": 1_000_000, "s": 1_000_000_000}
"""Maps each TimerPrecisions value to the number of nanoseconds that unit contains."""

_FORMAT_UNITS: tuple[tuple[str, int], ...] = (
    ("d", 86_400_000_000_000),
    ("h", 3_600_000_000_000),
    ("m", 60_000_000_000),
    ("s", 1_000_000_000),
    ("ms", 1_000_000),
    ("us", 1_000),
    ("ns", 1),
)
"""Orders the units used to format elapsed time, from largest to smallest, with their nanosecond magnitudes."""


class TimerPrecisions(StrEnum):
    """Defines the timer precision modes supported by PrecisionTimer instances."""

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

        Instances are safe to share between threads. The timer reference point is updated with atomic operations, so
        concurrent lap() calls return adjacent intervals that together partition the elapsed time.

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
        if precision not in tuple(TimerPrecisions):
            message = (
                f"Unable to initialize PrecisionTimer class. The precision must be one of the supported options "
                f"defined in the TimerPrecisions enumeration ({tuple(TimerPrecisions)}), but got {precision}."
            )
            console.error(message=message, error=ValueError)

        precision = TimerPrecisions(precision)
        self._timer = CPrecisionTimer(precision=precision.value)
        self._laps: list[int] = []

    def __repr__(self) -> str:
        """Returns a string representation of the PrecisionTimer instance."""
        return f"PrecisionTimer(precision={self.precision}, elapsed={self.elapsed})"

    @property
    def elapsed(self) -> int:
        """Returns the time elapsed since class instantiation or the most recent reset() or lap() method call,
        whichever happened last.
        """
        return int(self._timer.Elapsed())

    @property
    def precision(self) -> str:
        """Returns the units currently used by the instance as a string ('ns', 'us', 'ms', or 's')."""
        return str(self._timer.get_precision())

    def reset(self) -> None:
        """Resets the timer and clears all recorded laps."""
        self._timer.Reset()
        self._laps.clear()

    def delay(self, delay: int, *, allow_sleep: bool = False, block: bool = False) -> None:
        """Delays program execution for the requested period of time.

        Args:
            delay: The integer period of time to wait for. The method assumes the delay is given in the same precision
                units as used by the instance.
            allow_sleep: Determines whether the timer may use sleep instead of busy-wait to suspend execution.
                Sleep is only used when the timer precision is 'ms' or 's'.
            block: Determines whether to hold (if True) or release (if False) the Global Interpreter Lock (GIL) during
                the delay. Releasing the GIL allows other Python threads to run in parallel with the delay, at the cost
                of tail latency. When another Python thread is CPU-bound, reacquiring the GIL can extend a delay by up
                to one thread-switch interval. Use block=True when latency determinism matters more than parallelism.
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
        if precision not in tuple(TimerPrecisions):
            message = (
                f"Unable to set PrecisionTimer precision. The precision must be one of the supported options "
                f"defined in the TimerPrecisions enumeration ({tuple(TimerPrecisions)}), but got {precision}."
            )
            console.error(message=message, error=ValueError)

        precision = TimerPrecisions(precision)
        self._timer.SetPrecision(precision=precision.value)

    def format_elapsed(self, *, max_fields: int = 2) -> str:
        """Returns the current elapsed time as a human-readable string.

        Converts the elapsed time to nanoseconds internally, then breaks it into descending unit components
        (d, h, m, s, ms, us, ns). Auto-selects the largest non-zero unit as the starting point and includes
        up to max_fields unit segments.

        Args:
            max_fields: The maximum number of unit segments to include in the output. Defaults to 2, e.g.
                "2 h 30 m" instead of "2 h 30 m 15 s 200 ms".

        Returns:
            A human-readable string representation of the elapsed time, e.g. "2 h 30 m", "1.5 ms", "500 ns".

        Raises:
            ValueError: If max_fields is less than 1.
        """
        if max_fields < 1:
            message = (
                f"Unable to format the elapsed time. The 'max_fields' must be greater than 0, but got {max_fields}."
            )
            console.error(message=message, error=ValueError)

        # Nanoseconds are the finest unit the timer reports, so the whole decomposition runs on exact integers and no
        # floating point residue reaches the output.
        elapsed = self.elapsed
        precision = self.precision
        elapsed_nanoseconds = elapsed * _NANOSECONDS_PER_UNIT[precision]

        if elapsed_nanoseconds == 0:
            return f"0 {precision}"

        remaining = elapsed_nanoseconds
        parts: list[str] = []
        for unit_name, unit_nanoseconds in _FORMAT_UNITS:
            if remaining < unit_nanoseconds:
                continue
            if len(parts) == max_fields - 1 or unit_name == _FORMAT_UNITS[-1][0]:
                # Last field: renders the remainder as a decimal, dropping a trailing zero fraction.
                count = round(remaining / unit_nanoseconds, ndigits=3)
                whole_count = int(count)
                parts.append(f"{whole_count} {unit_name}" if count == whole_count else f"{count} {unit_name}")
                break
            whole = remaining // unit_nanoseconds
            parts.append(f"{whole} {unit_name}")
            remaining -= whole * unit_nanoseconds

        return " ".join(parts)

    def lap(self) -> int:
        """Records the current elapsed time as a lap, resets the timer, and returns the lap duration.

        Returns:
            The elapsed time captured as the lap duration, in the timer's current precision units.
        """
        duration = int(self._timer.Lap())
        self._laps.append(duration)
        return duration

    @property
    def laps(self) -> tuple[int, ...]:
        """Returns all recorded lap times as a tuple."""
        return tuple(self._laps)

    def poll(self, interval: int, *, allow_sleep: bool = True, block: bool = False) -> Generator[int, None, None]:
        """Yields an iteration count after each delay cycle.

        The caller should break out of the loop when done, because the generator never terminates on its own.

        Args:
            interval: The delay interval in the timer's current precision units.
            allow_sleep: Determines whether the timer may use sleep instead of busy-wait to suspend execution.
                Sleep is only used when the timer precision is 'ms' or 's'.
            block: Determines whether to hold or release the GIL during the delay.

        Yields:
            The iteration count (starting from 1) after each delay cycle.
        """
        count = 0
        while True:
            self.delay(delay=interval, allow_sleep=allow_sleep, block=block)
            count += 1
            yield count
