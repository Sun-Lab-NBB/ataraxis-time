"""Contains tests for the PrecisionTimer class and TimerPrecisions enumeration provided by the timer.py module.

This is not a performance benchmark. This test suite only verifies that commands run without errors and that their
runtime appears to be correct. Due to the nature of this library, programmatic tests are likely to have a wide range of
execution times across all supported platform+architecture combinations. The benchmarking script shipped with the
library is what establishes whether the library is appropriate for any particular system.
"""

import re
import time
import threading

import pytest
from ataraxis_time import PrecisionTimer, TimerPrecisions
from ataraxis_base_utilities import error_format

# Global variables used for block/no-block threaded testing.
_global_counter: int = 0
_end_flag: bool = False


def test_initialization_and_precision_control() -> None:
    """Verifies PrecisionTimer initialization and precision-control functionality."""
    timer = PrecisionTimer()
    assert timer.precision == "us"

    timer = PrecisionTimer("us")
    assert timer.precision == "us"

    timer = PrecisionTimer(TimerPrecisions.MICROSECOND)
    assert timer.precision == "us"

    # Switches the class to second precision using string and verifies the class switches precision as expected.
    timer.set_precision(precision="s")
    assert timer.precision == "s"

    # Switches the class to millisecond precision using enum and verifies the switch.
    timer.set_precision(precision=TimerPrecisions.MILLISECOND)
    assert timer.precision == "ms"

    # Switches to nanosecond precision using a string.
    timer.set_precision(precision="ns")
    assert timer.precision == "ns"

    timer.set_precision(precision="s")
    expected_start = "PrecisionTimer(precision=s, elapsed="

    # Checks if the __repr__ method returns the expected string. Specifically, verifies the entire string except for
    # the 'elapsed' parameter, as it is almost impossible to predict.
    repr_string = repr(timer)
    assert repr_string.startswith(expected_start)
    assert repr_string.endswith(")")


def test_timer_precisions_enum() -> None:
    """Verifies the TimerPrecisions enumeration functionality."""
    # Verifies all expected enum values exist.
    assert TimerPrecisions.NANOSECOND == "ns"
    assert TimerPrecisions.MICROSECOND == "us"
    assert TimerPrecisions.MILLISECOND == "ms"
    assert TimerPrecisions.SECOND == "s"

    # Verifies the enumeration has exactly the expected members.
    expected_precisions = {"NANOSECOND", "MICROSECOND", "MILLISECOND", "SECOND"}
    actual_precisions = {member.name for member in TimerPrecisions}
    assert actual_precisions == expected_precisions

    # Verifies string values match expected format.
    expected_values = {"ns", "us", "ms", "s"}
    actual_values = {member.value for member in TimerPrecisions}
    assert actual_values == expected_values

    # Verifies string-value to enum conversion through StrEnum.
    assert TimerPrecisions("ns") == TimerPrecisions.NANOSECOND
    assert TimerPrecisions("us") == TimerPrecisions.MICROSECOND


def test_initialization_and_precision_control_errors() -> None:
    """Verifies PrecisionTimer initialization and precision-control error handling."""
    # Verifies that attempting to initialize the class with an invalid precision fails as expected.
    invalid_precision = "invalid_precision"
    message = (
        f"Unable to initialize PrecisionTimer class. The precision must be one of the supported options "
        f"defined in the TimerPrecisions enumeration ({tuple(TimerPrecisions)}), but got {invalid_precision}."
    )
    with pytest.raises(ValueError, match=error_format(message)):
        PrecisionTimer(invalid_precision)

    timer = PrecisionTimer("us")

    # Verifies that attempting to set the precision of an initialized class to an unsupported value fails as expected.
    message = (
        f"Unable to set PrecisionTimer precision. The precision must be one of the supported options "
        f"defined in the TimerPrecisions enumeration ({tuple(TimerPrecisions)}), but got {invalid_precision}."
    )
    with pytest.raises(ValueError, match=error_format(message)):
        timer.set_precision(precision=invalid_precision)


def test_elapsed_property() -> None:
    """Verifies the basic functioning of the PrecisionTimer's 'elapsed' property."""
    timer = PrecisionTimer("ns")

    # Verifies that the elapsed counter increases as time passes.
    time_value = timer.elapsed
    assert time_value != timer.elapsed

    # Verifies that resetting the timer correctly re-bases the elapsed time calculation.
    time_value = timer.elapsed
    timer.reset()
    assert time_value > timer.elapsed


@pytest.mark.parametrize("precision", ["ns", "us", "ms", "s"])
def test_interval_timing(precision: str) -> None:
    """Verifies the interval timing functionality of the PrecisionTimer class for the given precision."""
    timer = PrecisionTimer(precision)
    _verify_interval_method(timer=timer, precision=precision, interval=1)


@pytest.mark.parametrize("precision", ["ns", "us", "ms", "s"])
@pytest.mark.parametrize("allow_sleep", [False, True])
@pytest.mark.parametrize("block", [False, True])
def test_delay_timing(precision: str, allow_sleep: bool, block: bool) -> None:
    """Verifies the delay functionality of the PrecisionTimer class with different blocking modes."""
    timer = PrecisionTimer(precision)
    _verify_delay_method(timer=timer, precision=precision, delay=1, allow_sleep=allow_sleep, block=block)


def test_delay_with_enum_precision() -> None:
    """Verifies that delay method works correctly when timer is initialized with TimerPrecisions enum."""
    # Tests each enum value.
    for precision_enum in TimerPrecisions:
        timer = PrecisionTimer(precision_enum)
        timer.delay(delay=1, allow_sleep=False, block=False)
        assert timer.precision == precision_enum.value

        # Tests delay with different parameter combinations.
        timer.delay(delay=1, allow_sleep=True, block=False)
        timer.delay(delay=1, allow_sleep=False, block=True)
        timer.delay(delay=1, allow_sleep=True, block=True)


def test_threaded_delay() -> None:
    """Verifies blocking and non-blocking delay method GIL release behavior."""
    # Binds global variables and initializes a seconds' timer.
    global _global_counter, _end_flag
    timer = PrecisionTimer("s")

    # Starts a separate thread that updates the _global_counter.
    counter_thread = threading.Thread(target=_update_global_counter)
    # Configures the thread as a daemon, so it closes automatically when the main program exits.
    counter_thread.daemon = True
    counter_thread.start()

    # Short delay to ensure the counter-thread has started.
    time.sleep(0.1)

    # Verifies that blocking delay (block=True) prevents the thread from running during the delay period
    # because it holds the GIL.
    _global_counter = 0
    timer.delay(delay=2, block=True)
    assert _global_counter < 5

    # Verifies that non-blocking delay (block=False) releases the GIL and allows the thread to run during the delay
    # period.
    _global_counter = 0
    timer.delay(delay=2, block=False)
    assert _global_counter > 25

    # Eliminates the thread to avoid nanobind leak warnings.
    _end_flag = True
    time.sleep(0.1)


def test_precision_switching() -> None:
    """Verifies that precision can be switched dynamically during timer operation."""
    timer = PrecisionTimer(TimerPrecisions.NANOSECOND)
    assert timer.precision == "ns"

    # Switches to microseconds.
    timer.set_precision(precision=TimerPrecisions.MICROSECOND)
    assert timer.precision == "us"

    # Switches to milliseconds using a string.
    timer.set_precision(precision="ms")
    assert timer.precision == "ms"

    # Switches to seconds using a string.
    timer.set_precision(precision="s")
    assert timer.precision == "s"

    # Verifies the timer still works after multiple precision changes.
    timer.reset()
    timer.delay(delay=1, allow_sleep=False, block=False)
    assert timer.elapsed >= 1  # Should be at least 1 second


def test_timer_with_different_initialization_methods() -> None:
    """Verifies that PrecisionTimer can be initialized with different argument types."""
    nanosecond_timer = PrecisionTimer("ns")
    assert nanosecond_timer.precision == "ns"

    microsecond_timer = PrecisionTimer("us")
    assert microsecond_timer.precision == "us"

    millisecond_timer = PrecisionTimer("ms")
    assert millisecond_timer.precision == "ms"

    enum_timer = PrecisionTimer(TimerPrecisions.SECOND)
    assert enum_timer.precision == "s"

    default_timer = PrecisionTimer()
    assert default_timer.precision == "us"


def test_reset_functionality() -> None:
    """Verifies the reset method works correctly with different precisions."""
    for precision in TimerPrecisions:
        timer = PrecisionTimer(precision)

        # Lets some time pass.
        timer.delay(delay=10, allow_sleep=False, block=False)

        # Reads the elapsed time before the reset.
        elapsed_before = timer.elapsed
        assert elapsed_before > 0

        timer.reset()

        # Verifies the elapsed time is much smaller after the reset.
        elapsed_after = timer.elapsed
        assert elapsed_after < elapsed_before

        # Verifies the timer still functions after the reset.
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
    # Verifies at least one unit abbreviation is present.
    assert re.search(r"(ns|us|ms|s|m|h|d)", result)

    # Tests nanosecond precision, which produces output in ns, us, or ms units.
    timer_ns = PrecisionTimer("ns")
    timer_ns.delay(delay=1000, allow_sleep=False, block=False)
    result_ns = timer_ns.format_elapsed()
    assert isinstance(result_ns, str)
    assert len(result_ns) > 0

    # Tests max_fields=1, which produces at most one unit segment.
    timer_ms = PrecisionTimer("ms")
    timer_ms.delay(delay=100, allow_sleep=False, block=False)
    single_field_result = timer_ms.format_elapsed(max_fields=1)
    assert isinstance(single_field_result, str)

    # Tests zero elapsed time. With second precision, elapsed returns 0 right after reset since
    # less than 1 second has passed, so this reliably triggers the zero-elapsed branch.
    timer_zero = PrecisionTimer("s")
    timer_zero.reset()
    result_zero = timer_zero.format_elapsed()
    assert result_zero == "0 s"


def test_format_elapsed_fractional_field(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies format_elapsed() renders the final unit segment as a decimal for non-whole unit counts."""
    timer = PrecisionTimer("ms")

    # Pins the elapsed time and precision so the final field resolves to a fractional unit count
    # (1500 ms == 1.5 s). Real elapsed times cannot reliably reproduce this, so patching is the only
    # deterministic way to exercise the decimal-rendering branch.
    monkeypatch.setattr(PrecisionTimer, "elapsed", property(lambda _self: 1500))
    monkeypatch.setattr(PrecisionTimer, "precision", property(lambda _self: "ms"))

    assert timer.format_elapsed(max_fields=1) == "1.5 s"


def test_lap() -> None:
    """Verifies the lap() method records elapsed time, resets timer, and returns the lap duration."""
    timer = PrecisionTimer("ms")

    timer.delay(delay=10, allow_sleep=False, block=False)
    lap_duration = timer.lap()

    assert isinstance(lap_duration, int)
    assert lap_duration >= 10

    # Verifies the timer was reset (elapsed should be much smaller than the lap duration).
    assert timer.elapsed < lap_duration

    timer.delay(delay=5, allow_sleep=False, block=False)
    lap2 = timer.lap()
    assert isinstance(lap2, int)
    assert lap2 >= 5


def test_laps_property() -> None:
    """Verifies the laps property returns all recorded lap times as a tuple."""
    timer = PrecisionTimer("ms")

    # Verifies the laps tuple starts empty.
    assert timer.laps == ()

    timer.delay(delay=5, allow_sleep=False, block=False)
    lap1 = timer.lap()
    timer.delay(delay=5, allow_sleep=False, block=False)
    lap2 = timer.lap()
    timer.delay(delay=5, allow_sleep=False, block=False)
    lap3 = timer.lap()

    laps = timer.laps
    assert isinstance(laps, tuple)
    assert len(laps) == 3
    assert laps[0] == lap1
    assert laps[1] == lap2
    assert laps[2] == lap3


def test_lap_clears_on_reset() -> None:
    """Verifies that reset() clears all recorded laps."""
    timer = PrecisionTimer("ms")

    timer.delay(delay=5, allow_sleep=False, block=False)
    timer.lap()
    timer.delay(delay=5, allow_sleep=False, block=False)
    timer.lap()
    assert len(timer.laps) == 2

    # Resets the timer, which clears the recorded laps.
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
    sleeping_iterations = []
    for count in timer.poll(interval=1, allow_sleep=True, block=False):
        sleeping_iterations.append(count)
        if count >= 2:
            break

    assert sleeping_iterations == [1, 2]


@pytest.mark.parametrize(
    "precision,divisor,sleep_duration",
    [("ns", 1, 0.05), ("us", 1_000, 0.05), ("ms", 1_000_000, 0.05), ("s", 1_000_000_000, 1.1)],
)
def test_elapsed_reports_expected_magnitude(precision: str, divisor: int, sleep_duration: float) -> None:
    """Verifies the elapsed property reports the correct magnitude for each precision.

    Uses a two-sided bound against an independently measured interval, so that a wrong conversion divisor fails here.
    Every other assertion in this suite is a lower bound or a relative ordering, which a scaled value satisfies.
    """
    timer = PrecisionTimer(precision)
    timer.reset()
    start = time.perf_counter_ns()
    time.sleep(sleep_duration)
    reported = timer.elapsed
    expected = (time.perf_counter_ns() - start) / divisor

    assert 0.5 * expected <= reported <= 2.0 * expected


def test_format_elapsed_pins_multi_field_output(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies the multi-field decomposition produces exact segment values.

    Pins the elapsed time so the decomposition is deterministic, since real elapsed times cannot reproduce an exact
    multi-segment string.
    """
    monkeypatch.setattr(PrecisionTimer, "elapsed", property(lambda _self: 3_660_000))
    monkeypatch.setattr(PrecisionTimer, "precision", property(lambda _self: "ms"))
    timer = PrecisionTimer("ms")

    assert timer.format_elapsed(max_fields=2) == "1 h 1 m"
    assert timer.format_elapsed(max_fields=3) == "1 h 1 m"

    # Verifies a sub-millisecond elapsed time renders in nanoseconds.
    monkeypatch.setattr(PrecisionTimer, "elapsed", property(lambda _self: 500))
    monkeypatch.setattr(PrecisionTimer, "precision", property(lambda _self: "ns"))
    assert timer.format_elapsed() == "500 ns"


def test_format_elapsed_errors() -> None:
    """Verifies format_elapsed() rejects a max_fields value below one."""
    timer = PrecisionTimer("s")
    message = "Unable to format the elapsed time. The 'max_fields' must be greater than 0, but got 0."
    with pytest.raises(ValueError, match=error_format(message)):
        timer.format_elapsed(max_fields=0)


def test_lap_partitions_elapsed_time() -> None:
    """Verifies consecutive laps account for the whole interval, leaving no gap between one lap and the next."""
    timer = PrecisionTimer("ns")

    # The recorded laps span a shorter interval than the bracket measuring them, so preemption between the bracket and
    # the first lap only ever depresses the ratio. The best attempt is therefore the one that reflects the timer rather
    # than the load the host happened to be under, and repeating guards a busy machine against a spurious failure.
    best_ratio = 0.0
    for _ in range(5):
        start = time.perf_counter_ns()
        timer.reset()
        for _ in range(200):
            timer.lap()
        total = time.perf_counter_ns() - start
        recorded = sum(timer.laps)

        assert recorded <= total
        best_ratio = max(best_ratio, recorded / total)

    # Each lap re-bases the timer in the same step that reads it, so the next lap begins where this one ended. Reading
    # the elapsed time and re-basing separately would drop the interval between the two calls from every lap.
    assert best_ratio > 0.8


def test_lap_does_not_overlap_across_threads() -> None:
    """Verifies concurrent laps receive distinct slices of the elapsed time."""
    timer = PrecisionTimer("ns")
    start = time.perf_counter_ns()
    timer.reset()

    def record_laps() -> None:
        for _ in range(200):
            timer.lap()

    threads = [threading.Thread(target=record_laps) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    total = time.perf_counter_ns() - start

    assert len(timer.laps) == 800

    # Overlapping laps would count the shared interval once per thread and push the sum past the measured total.
    assert sum(timer.laps) <= total


def _update_global_counter() -> None:
    """Continuously increments a global counter until the _end_flag is set."""
    global _global_counter
    while not _end_flag:
        _global_counter += 1
        time.sleep(0.02)  # Release GIL


def _verify_delay_method(
    timer: PrecisionTimer,
    precision: str,
    delay: int,
    *,
    allow_sleep: bool = False,
    block: bool = False,
) -> None:
    """Streamlines testing delay method runtimes by offering a generalized test template.

    Notes:
        Exercises the runtime of the delay method.

    Args:
        timer: The instance used by the calling test function.
        precision: The precision option to use for the test. Must be one of the options supported by the
            PrecisionTimer class: 'ns', 'us', 'ms', or 's'.
        delay: The period of time to delay for. The 'precision' argument defines the units.
        allow_sleep: Determines whether the delay method may use sleep instead of a busy-wait loop. Defaults to False.
        block: Determines whether to hold or release the GIL during the delay. Defaults to False.
    """
    timer.set_precision(precision=precision)
    timer.delay(delay=delay, allow_sleep=allow_sleep, block=block)


def _verify_interval_method(timer: PrecisionTimer, precision: str, interval: int) -> None:
    """Streamlines testing interval timing method runtimes by offering a generalized test template.

    Notes:
        Exercises the runtime of the interval timing method.

    Args:
        timer: The instance used by the calling test function.
        precision: The precision option to use for the test. Must be one of the options supported by the
            PrecisionTimer class: 'ns', 'us', 'ms', or 's'.
        interval: The period of time that should be interval-timed. The 'precision' argument defines the units.
    """
    timer.set_precision(precision=precision)
    timer.reset()
    while timer.elapsed < interval:
        pass
