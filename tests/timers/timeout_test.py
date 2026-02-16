"""Contains tests for the Timeout class provided by the timeout.py module."""

import time as tm

import pytest  # type: ignore
from ataraxis_base_utilities import error_format
from ataraxis_time import Timeout, TimerPrecisions


def test_timeout_initialization() -> None:
    """Verifies Timeout class initialization with various precisions."""
    # Default precision (microseconds) - 5 second timeout.
    timeout = Timeout(duration=5_000_000)
    assert timeout.elapsed >= 0
    assert not timeout.expired

    # Explicit microsecond precision.
    timeout = Timeout(duration=5_000_000, precision=TimerPrecisions.MICROSECOND)
    assert not timeout.expired

    # Millisecond precision - 5 second timeout.
    timeout = Timeout(duration=5_000, precision=TimerPrecisions.MILLISECOND)
    assert not timeout.expired

    # Second precision - 5 second timeout.
    timeout = Timeout(duration=5, precision=TimerPrecisions.SECOND)
    assert not timeout.expired

    # Nanosecond precision - 5 second timeout.
    timeout = Timeout(duration=5_000_000_000, precision=TimerPrecisions.NANOSECOND)
    assert not timeout.expired

    # String precision.
    timeout = Timeout(duration=5_000, precision="ms")
    assert not timeout.expired


def test_timeout_expired() -> None:
    """Verifies the expired property correctly detects timeout expiry."""
    # Creates a very short timeout (1 nanosecond) that should expire almost immediately.
    timeout = Timeout(duration=1, precision=TimerPrecisions.NANOSECOND)

    # Waits briefly to ensure the timeout expires.
    tm.sleep(0.001)  # 1 ms - more than enough for 1 ns to elapse.
    assert timeout.expired


def test_timeout_remaining() -> None:
    """Verifies the remaining property returns correct values."""
    # Creates a timeout with a known duration (5 seconds).
    timeout = Timeout(duration=5_000_000, precision=TimerPrecisions.MICROSECOND)

    # Initially, remaining should be close to the full duration.
    remaining = timeout.remaining
    assert remaining > 0
    assert remaining <= 5_000_000

    # After expiry, remaining should be 0.
    timeout_short = Timeout(duration=1, precision=TimerPrecisions.NANOSECOND)
    tm.sleep(0.001)
    assert timeout_short.remaining == 0


def test_timeout_elapsed() -> None:
    """Verifies the elapsed property returns elapsed time."""
    timeout = Timeout(duration=5_000_000, precision=TimerPrecisions.MICROSECOND)

    # Elapsed time should be non-negative and increasing.
    elapsed1 = timeout.elapsed
    assert elapsed1 >= 0

    tm.sleep(0.01)
    elapsed2 = timeout.elapsed
    assert elapsed2 > elapsed1


def test_timeout_kick() -> None:
    """Verifies the kick() method resets the timeout timer for activity-based timeouts."""
    timeout = Timeout(duration=5_000_000, precision=TimerPrecisions.MICROSECOND)

    # Let some time pass.
    tm.sleep(0.01)
    elapsed_before = timeout.elapsed
    assert elapsed_before > 0

    # Kick the timeout (reset the timer).
    timeout.kick()

    # Elapsed should be reset to near-zero.
    elapsed_after = timeout.elapsed
    assert elapsed_after < elapsed_before


def test_timeout_reset() -> None:
    """Verifies the reset() method with and without a new duration."""
    timeout = Timeout(duration=5_000_000, precision=TimerPrecisions.MICROSECOND)

    # Let some time pass.
    tm.sleep(0.01)

    # Reset without changing duration.
    timeout.reset()
    assert timeout.elapsed < 1000  # Should be very small after reset.
    assert timeout.remaining > 0

    # Reset with a new duration.
    timeout.reset(duration=5_000_000)
    assert timeout.remaining > 1_000_000
    assert not timeout.expired


def test_timeout_errors() -> None:
    """Verifies error handling for invalid Timeout initialization and reset."""
    # Tests zero duration.
    message = f"Unable to initialize the Timeout class. The 'duration' must be greater than 0, but got 0."
    with pytest.raises(ValueError, match=error_format(message)):
        Timeout(duration=0)

    # Tests negative duration.
    message = f"Unable to initialize the Timeout class. The 'duration' must be greater than 0, but got -100."
    with pytest.raises(ValueError, match=error_format(message)):
        Timeout(duration=-100)

    # Tests invalid precision (uses PrecisionTimer's validation).
    invalid_precision = "invalid"
    message = (
        f"Unable to initialize PrecisionTimer class. The precision must be one of the supported options "
        f"defined in the TimerPrecisions enumeration ({tuple(TimerPrecisions)}), but got {invalid_precision}."
    )
    with pytest.raises(ValueError, match=error_format(message)):
        Timeout(duration=1000, precision=invalid_precision)

    # Tests reset with invalid duration.
    timeout = Timeout(duration=5_000, precision=TimerPrecisions.MILLISECOND)
    message = f"Unable to reset Timeout. The 'duration' must be greater than 0, but got 0."
    with pytest.raises(ValueError, match=error_format(message)):
        timeout.reset(duration=0)

    message = f"Unable to reset Timeout. The 'duration' must be greater than 0, but got -50."
    with pytest.raises(ValueError, match=error_format(message)):
        timeout.reset(duration=-50)
