"""Contains tests for the PrecisionTimer class and TimerPrecisions enumeration provided by the timer.py module.

This is not a performance benchmark. This test suite only verifies that commands run without errors and that their
runtime appears to be correct. Due to the nature of this library, programmatic tests are likely to have a wide range of
execution times across all supported platform+architecture combinations. The only way to be sure the library is
appropriate for any particular system is to use the benchmarking script shipped with the library. Passing this test
suite is not enough to conclude the library is appropriate for any particular use case, it is only enough to conclude it
runs without errors.
"""

import re
import time as tm
import threading

import pytest  # type: ignore
from ataraxis_time import PrecisionTimer, TimerPrecisions
from ataraxis_base_utilities import error_format
from ataraxis_time.precision_timer_ext import CPrecisionTimer  # type: ignore

# Global variables used for block/no-block threaded testing
global_counter: int = 0
end_flag: bool = False


def update_global_counter() -> None:
    """Continuously increments a global counter until the end_flag is set.

    Used to test blocking vs. non-blocking delay functionality.
    """
    global global_counter
    while not end_flag:
        global_counter += 1
        tm.sleep(0.02)  # Release GIL


def verify_delay_method(
    timer: PrecisionTimer,
    precision: str,
    delay: int,
    *,
    allow_sleep: bool = False,
    block: bool = False,
) -> None:
    """Streamlines testing delay method runtimes by offering a generalized test template.

    This method reduces the boilerplate code usage by providing a template that can be used to quickly test the
    delay method under different conditions. The runtime of this method does not affect the precision of the
    input class at any outer scope.

    Notes:
        This method does not evaluate the precision of the timer, only its ability to execute the runtime.

    Args:
        timer: The PrecisionTimer class instance used by the main test function.
        precision: The precision string-option to use for the test. Has to be one of the precisions supported by the
            PrecisionTimer class: 'ns', 'us', 'ms', 's'
        delay: The integer period of time to delay for, 'precision' argument defines the units of the delay.
        allow_sleep: A boolean flag that determines whether the delay method is allowed to use sleep instead of a
            busy-wait loop. Defaults to False.
        block: A boolean flag that determines whether to hold or release the GIL during the delay. Defaults to False.
    """
    # noinspection PyTypeChecker
    timer.set_precision(precision=precision)  # Switches the timer to the input precision
    timer.delay(delay=delay, allow_sleep=allow_sleep, block=block)


def verify_interval_method(timer: PrecisionTimer, precision: str, interval: int) -> None:
    """Streamlines testing interval timing method runtimes by offering a generalized test template.

    This method reduces the boilerplate code usage by providing a template that can be used to quickly test the
    interval timing method under different conditions. The runtime of this method does not affect the precision of the
    input class at any outer scope.

    Notes:
        This method does not evaluate the precision of the timer, only its ability to execute the runtime.

    Args:
         timer: The PrecisionTimer class instance used by the main test function.
         precision: The precision string-option to use for the test. Has to be one of the precisions supported by the
            PrecisionTimer class: 'ns', 'us', 'ms', 's'
        interval: The integer period of time that should be interval-timed, 'precision' argument defines the units of
            the interval.
    """
    # noinspection PyTypeChecker
    timer.set_precision(precision=precision)
    timer.reset()
    while timer.elapsed < interval:
        pass


def test_initialization_and_precision_control() -> None:
    """Verifies PrecisionTimer class initialization and precision manipulation (retrieval and setting) functionality."""
    # Initializes the class using microsecond precision (default)
    timer = PrecisionTimer()
    assert timer.precision == "us"

    # Initializes the class explicitly using microsecond precision with string
    timer = PrecisionTimer("us")
    assert timer.precision == "us"

    # Initializes the class using TimerPrecisions enum
    timer = PrecisionTimer(TimerPrecisions.MICROSECOND)
    assert timer.precision == "us"

    # Switches the class to second precision using string and verifies the class switches precision as expected
    timer.set_precision("s")
    assert timer.precision == "s"

    # Switches the class to millisecond precision using enum and verifies the switch
    timer.set_precision(TimerPrecisions.MILLISECOND)
    assert timer.precision == "ms"

    # Tests case insensitivity by using uppercase (this will work through StrEnum's __new__)
    timer.set_precision("ns")
    assert timer.precision == "ns"

    # Verifies the representation method of the class
    timer.set_precision("s")
    expected_start = "PrecisionTimer(precision=s, elapsed_time = "
    expected_end = " s.)"

    # Checks if the __repr__ method returns the expected string. Specifically, verifies the entire string except for
    # the 'elapsed' parameter, as it is almost impossible to predict.
    repr_string = repr(timer)
    assert expected_start in repr_string
    assert expected_end in repr_string


def test_timer_precisions_enum() -> None:
    """Verifies the TimerPrecisions enumeration functionality."""
    # Verifies all expected enum values exist
    assert TimerPrecisions.NANOSECOND == "ns"
    assert TimerPrecisions.MICROSECOND == "us"
    assert TimerPrecisions.MILLISECOND == "ms"
    assert TimerPrecisions.SECOND == "s"

    # Verifies the enumeration has exactly the expected members
    expected_precisions = {"NANOSECOND", "MICROSECOND", "MILLISECOND", "SECOND"}
    actual_precisions = {member.name for member in TimerPrecisions}
    assert actual_precisions == expected_precisions

    # Verifies string values match expected format
    expected_values = {"ns", "us", "ms", "s"}
    actual_values = {member.value for member in TimerPrecisions}
    assert actual_values == expected_values

    # Verifies case-insensitive string conversion works through StrEnum
    assert TimerPrecisions("ns") == TimerPrecisions.NANOSECOND
    assert TimerPrecisions("ns") == TimerPrecisions.NANOSECOND
    assert TimerPrecisions("us") == TimerPrecisions.MICROSECOND


def test_initialization_and_precision_control_errors() -> None:
    """Verifies PrecisionTimer class initialization and precision manipulation (retrieval and setting) error handling."""
    # Verifies that attempting to initialize the class with an invalid precision fails as expected
    invalid_precision = "invalid_precision"
    message = (
        f"Unable to initialize PrecisionTimer class. The precision must be one of the supported options "
        f"defined in the TimerPrecisions enumeration ({tuple(TimerPrecisions)}), but got {invalid_precision}."
    )
    # noinspection PyTypeChecker
    with pytest.raises(ValueError, match=error_format(message)):
        # noinspection PyTypeChecker
        PrecisionTimer(invalid_precision)

    # Initializes a valid timer for testing set_precision errors
    timer = PrecisionTimer("us")

    # Verifies that attempting to set the precision of an initialized class to an unsupported value fails as expected
    message = (
        f"Unable to set PrecisionTimer precision. The precision must be one of the supported options "
        f"defined in the TimerPrecisions enumeration ({tuple(TimerPrecisions)}), but got {invalid_precision}."
    )
    # noinspection PyTypeChecker
    with pytest.raises(ValueError, match=error_format(message)):
        # noinspection PyTypeChecker
        timer.set_precision(invalid_precision)


def test_elapsed_property() -> None:
    """Verifies the basic functioning of the PrecisionTimer's 'elapsed' property."""
    # Initializes a nanosecond timer
    timer = PrecisionTimer("ns")

    # Verifies that the elapsed counter increases as time passes
    time_value = timer.elapsed
    assert time_value != timer.elapsed

    # Verifies that resetting the timer correctly re-bases the elapsed time calculation.
    time_value = timer.elapsed
    timer.reset()
    assert time_value > timer.elapsed


@pytest.mark.parametrize("precision", ["ns", "us", "ms", "s"])
def test_interval_timing(precision: str) -> None:
    """Verifies the interval timing functionality of the PrecisionTimer class for the given precision.

    Does not test runtime precision. Use the benchmark_timer script for that purpose. This test just ensures
    that commands run without errors. Uses 'mark' fixture to generate a version of this test for all supported
    precisions and, ideally, should be executed in-parallel with other tests.
    """
    # noinspection PyTypeChecker
    timer = PrecisionTimer(precision)
    verify_interval_method(timer=timer, precision=precision, interval=1)


@pytest.mark.parametrize("precision", ["ns", "us", "ms", "s"])
@pytest.mark.parametrize("allow_sleep", [False, True])
@pytest.mark.parametrize("block", [False, True])
def test_delay_timing(precision: str, allow_sleep: bool, block: bool) -> None:
    """Verifies the delay functionality of the PrecisionTimer class with different blocking modes.

    Similar to how interval timing is tested, this function does not evaluate delay method precision. Use the
    benchmark command to benchmark delay precision on your particular system.
    """
    # noinspection PyTypeChecker
    timer = PrecisionTimer(precision)
    verify_delay_method(timer=timer, precision=precision, delay=1, allow_sleep=allow_sleep, block=block)


def test_delay_with_enum_precision() -> None:
    """Verifies that delay method works correctly when timer is initialized with TimerPrecisions enum."""
    # Test with each enum value
    for precision_enum in TimerPrecisions:
        timer = PrecisionTimer(precision_enum)
        timer.delay(delay=1, allow_sleep=False, block=False)
        assert timer.precision == precision_enum.value

        # Also test delay with different parameter combinations
        timer.delay(delay=1, allow_sleep=True, block=False)
        timer.delay(delay=1, allow_sleep=False, block=True)
        timer.delay(delay=1, allow_sleep=True, block=True)


def test_threaded_delay() -> None:
    """Verifies blocking and non-blocking delay method GIL release behavior."""
    # Binds global variables and initializes a seconds' timer
    global global_counter, end_flag
    timer = PrecisionTimer("s")

    # Starts a separate thread that updates the global_counter
    counter_thread = threading.Thread(target=update_global_counter)
    counter_thread.daemon = True  # Set as a daemon, so it automatically closes when the main program exits
    counter_thread.start()

    # Short delay to ensure the counter-thread has started
    tm.sleep(0.1)

    # Verifies that blocking delay (block=True) prevents the thread from running during the delay period
    # because it holds the GIL
    global_counter = 0
    timer.delay(delay=2, block=True)
    assert global_counter < 5

    # Verifies that non-blocking delay (block=False) releases the GIL and allows the thread to run during the delay
    # period
    global_counter = 0
    timer.delay(delay=2, block=False)
    assert global_counter > 25

    # Eliminates the thread to avoid nanobind leak warnings
    end_flag = True
    tm.sleep(0.1)


def test_precision_switching() -> None:
    """Verifies that precision can be switched dynamically during timer operation."""
    timer = PrecisionTimer(TimerPrecisions.NANOSECOND)
    assert timer.precision == "ns"

    # Record initial elapsed time in nanoseconds
    initial_elapsed_ns = timer.elapsed

    # Switch to microseconds
    timer.set_precision(TimerPrecisions.MICROSECOND)
    assert timer.precision == "us"

    # Switch to milliseconds using string
    timer.set_precision("ms")
    assert timer.precision == "ms"

    # Switch to seconds using uppercase string
    timer.set_precision("s")
    assert timer.precision == "s"

    # Verify timer still works after multiple precision changes
    timer.reset()
    timer.delay(delay=1, allow_sleep=False, block=False)
    assert timer.elapsed >= 1  # Should be at least 1 second


def test_timer_with_different_initialization_methods() -> None:
    """Verifies that PrecisionTimer can be initialized with different argument types."""
    # Test initialization with string lowercase
    timer1 = PrecisionTimer("ns")
    assert timer1.precision == "ns"

    # Test initialization with string uppercase
    timer2 = PrecisionTimer("us")
    assert timer2.precision == "us"

    # Test initialization with string mixed case
    timer3 = PrecisionTimer("ms")
    assert timer3.precision == "ms"

    # Test initialization with TimerPrecisions enum
    timer4 = PrecisionTimer(TimerPrecisions.SECOND)
    assert timer4.precision == "s"

    # Test default initialization (should be microseconds)
    timer5 = PrecisionTimer()
    assert timer5.precision == "us"


def test_reset_functionality() -> None:
    """Verifies the reset method works correctly with different precisions."""
    for precision in TimerPrecisions:
        timer = PrecisionTimer(precision)

        # Let some time pass
        timer.delay(delay=10, allow_sleep=False, block=False)

        # Get elapsed time before reset
        elapsed_before = timer.elapsed
        assert elapsed_before > 0

        # Reset the timer
        timer.reset()

        # Elapsed time should be much smaller after reset
        elapsed_after = timer.elapsed
        assert elapsed_after < elapsed_before

        # Verify timer still functions after reset
        timer.delay(delay=1, allow_sleep=False, block=False)
        assert timer.elapsed >= 1


def test_format_elapsed() -> None:
    """Verifies the format_elapsed() method returns human-readable duration strings."""
    timer = PrecisionTimer("s")

    # Let some time elapse and verify the output is a non-empty string with unit abbreviations.
    timer.delay(delay=1, allow_sleep=False, block=False)
    result = timer.format_elapsed()
    assert isinstance(result, str)
    assert len(result) > 0
    # Should contain at least one unit abbreviation.
    assert re.search(r"(ns|us|ms|s|m|h|d)", result)

    # Tests with nanosecond precision - should produce output with ns/us/ms units.
    timer_ns = PrecisionTimer("ns")
    timer_ns.delay(delay=1000, allow_sleep=False, block=False)
    result_ns = timer_ns.format_elapsed()
    assert isinstance(result_ns, str)
    assert len(result_ns) > 0

    # Tests with max_fields=1 - should produce at most one unit segment.
    timer_ms = PrecisionTimer("ms")
    timer_ms.delay(delay=100, allow_sleep=False, block=False)
    result_1 = timer_ms.format_elapsed(max_fields=1)
    assert isinstance(result_1, str)
    # Should have at most one space-separated part.
    assert len(result_1.split(" ")) <= 1

    # Tests zero elapsed time. With second precision, elapsed returns 0 right after reset since
    # less than 1 second has passed, so this reliably triggers the zero-elapsed branch.
    timer_zero = PrecisionTimer("s")
    timer_zero.reset()
    result_zero = timer_zero.format_elapsed()
    assert result_zero == "0s"


def test_lap() -> None:
    """Verifies the lap() method records elapsed time, resets timer, and returns the lap duration."""
    timer = PrecisionTimer("ms")

    # Records a lap after a short delay.
    timer.delay(delay=10, allow_sleep=False, block=False)
    lap_duration = timer.lap()

    # Verifies the lap duration was captured.
    assert isinstance(lap_duration, int)
    assert lap_duration >= 10

    # Verifies the timer was reset (elapsed should be much smaller than the lap duration).
    assert timer.elapsed < lap_duration

    # Records a second lap.
    timer.delay(delay=5, allow_sleep=False, block=False)
    lap2 = timer.lap()
    assert isinstance(lap2, int)
    assert lap2 >= 5


def test_laps_property() -> None:
    """Verifies the laps property returns all recorded lap times as a tuple."""
    timer = PrecisionTimer("ms")

    # Initially, laps should be empty.
    assert timer.laps == ()

    # Records multiple laps.
    timer.delay(delay=5, allow_sleep=False, block=False)
    lap1 = timer.lap()
    timer.delay(delay=5, allow_sleep=False, block=False)
    lap2 = timer.lap()
    timer.delay(delay=5, allow_sleep=False, block=False)
    lap3 = timer.lap()

    # Verifies the laps tuple.
    laps = timer.laps
    assert isinstance(laps, tuple)
    assert len(laps) == 3
    assert laps[0] == lap1
    assert laps[1] == lap2
    assert laps[2] == lap3


def test_lap_clears_on_reset() -> None:
    """Verifies that reset() clears all recorded laps."""
    timer = PrecisionTimer("ms")

    # Records some laps.
    timer.delay(delay=5, allow_sleep=False, block=False)
    timer.lap()
    timer.delay(delay=5, allow_sleep=False, block=False)
    timer.lap()
    assert len(timer.laps) == 2

    # Resets the timer - laps should be cleared.
    timer.reset()
    assert timer.laps == ()
    assert len(timer.laps) == 0


def test_poll() -> None:
    """Verifies the poll() generator yields iteration counts after each delay cycle."""
    timer = PrecisionTimer("ms")

    # Tests that poll yields incrementing counts.
    iterations = []
    for count in timer.poll(interval=1, allow_sleep=False, block=False):
        iterations.append(count)
        if count >= 3:
            break

    assert iterations == [1, 2, 3]

    # Tests with allow_sleep=True.
    iterations2 = []
    for count in timer.poll(interval=1, allow_sleep=True, block=False):
        iterations2.append(count)
        if count >= 2:
            break

    assert iterations2 == [1, 2]
