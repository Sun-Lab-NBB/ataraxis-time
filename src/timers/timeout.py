"""Provides the Timeout class that offers a timeout guard built on PrecisionTimer."""

from ataraxis_base_utilities import console

from .timer import PrecisionTimer, TimerPrecisions


class Timeout:
    """Provides a timeout guard built on PrecisionTimer.

    This class wraps a PrecisionTimer instance and provides a convenient API for checking whether a specified
    duration has elapsed. It supports activity-based reset (kick) and full reset with optional duration changes.

    Args:
        duration: The timeout duration in the timer's precision units. Must be greater than 0.
        precision: The precision to use for timeout tracking. Use one of the supported values defined in the
            TimerPrecisions enumeration.

    Attributes:
        _timer: The internal PrecisionTimer instance.
        _duration: The timeout duration.

    Raises:
        ValueError: If the duration is not greater than 0, or if the precision is not a valid option.
    """

    def __init__(self, duration: int, precision: str | TimerPrecisions = TimerPrecisions.MICROSECOND) -> None:
        if duration <= 0:
            message = (
                f"Unable to initialize the Timeout class. The 'duration' must be greater than 0, but got {duration}."
            )
            console.error(message=message, error=ValueError)

        self._duration = duration
        self._timer = PrecisionTimer(precision=precision)
        self._timer.reset()

    @property
    def expired(self) -> bool:
        """Returns True if the timeout duration has elapsed."""
        return self._timer.elapsed >= self._duration

    @property
    def remaining(self) -> int:
        """Returns the remaining time before expiry (0 if expired)."""
        remaining = self._duration - self._timer.elapsed
        return max(0, remaining)

    @property
    def elapsed(self) -> int:
        """Returns elapsed time since creation or last reset."""
        return self._timer.elapsed

    def kick(self) -> None:
        """Resets the timeout timer (for activity-based timeouts).

        This resets the internal timer without changing the duration, effectively restarting the timeout countdown.
        """
        self._timer.reset()

    def reset(self, duration: int | None = None) -> None:
        """Resets the timeout, optionally with a new duration.

        Args:
            duration: An optional new duration for the timeout. If None, the current duration is preserved.
                Must be greater than 0 if provided.

        Raises:
            ValueError: If the provided duration is not greater than 0.
        """
        if duration is not None:
            if duration <= 0:
                message = f"Unable to reset Timeout. The 'duration' must be greater than 0, but got {duration}."
                console.error(message=message, error=ValueError)
            self._duration = duration
        self._timer.reset()
