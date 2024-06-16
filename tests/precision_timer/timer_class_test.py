"""Tests the functionality of the PrecisionTimer class.

This is not a performance benchmark! This test suite only verifies that commands run without errors and that their
runtime appears to be correct. Due to the nature of this library, programmatic tests are likely to have a wide range of
execution times across all supported platform+architecture combinations. The only way to be sure the library is
appropriate for any particular system is to use the benchmarking script shipped with the library. Passing this test
suite is not sufficient to conclude the library is appropriate for any particular use case, it is only enough to
conclude it runs without errors.
"""

# Imports
import re
import threading
import time as tm

import numpy as np
import pytest  # type: ignore
from ataraxis_time import PrecisionTimer
from ataraxis_time.precision_timer_ext import CPrecisionTimer  # type: ignore
from ataraxis_time.utilities import format_message

# Global variables used for block/no-block threaded testing
global_counter: int = 0
end_flag: bool = False


def update_global_counter() -> None:
    """A simple function that continuously increments a global counter.

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
    blocking: bool = False,
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
        blocking: A boolean flag that determines whether the blocking or non-blocking version of the method is used for
            this test. Defaults to False.
    """
    # noinspection PyTypeChecker
    timer.set_precision(precision=precision)  # Switches the timer to the input precision
    if blocking:
        timer.delay_block(delay=delay, allow_sleep=allow_sleep)
    else:
        timer.delay_noblock(delay=delay, allow_sleep=allow_sleep)


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
    """Tests PrecisionTimer class initialization and precision manipulation (retrieval and setting) functionality."""
    # Initializes the class using microsecond precision
    timer = PrecisionTimer("us")

    # Verifies that the class uses the microsecond (requested) precision
    assert timer.precision == "us"

    # Switches the class to second precision and verifies the class switches precision as expected (at least according
    # to its units' tracker)
    # noinspection PyTypeChecker
    timer.set_precision("S")  # Tests that the precision argument is case-insensitive
    assert timer.precision == "s"

    # Verifies that 'supported_precisions' returns the expected output
    precisions = timer.supported_precisions
    expected_precisions = ("ns", "us", "ms", "s")
    assert np.array_equal(precisions, expected_precisions)

    # Verifies the representation method of the class
    expected_start = "PrecisionTimer(precision=s, elapsed_time = "
    expected_end = " s.)"

    # Checks if the __repr__ method returns the expected string. Specifically, verifies the entire string except for
    # the 'elapsed' parameter, as it is almost impossible to predict.
    assert expected_start in repr(timer)
    assert expected_end in repr(timer)


def test_initialization_and_precision_control_errors() -> None:
    """Tests PrecisionTimer class initialization and precision manipulation (retrieval and setting) error handling."""
    # Initializes the class using microsecond precision, this is needed to access private '__supported_precisions'
    # attribute for the tests below
    timer: PrecisionTimer = PrecisionTimer("us")

    # Extracts the allowed precision set to reuse in the tests below. References internal class variable to improve code
    # maintainability (only need to change it in one place).
    # noinspection PyProtectedMember
    valid_precision: tuple = timer._supported_precisions

    # Verifies that attempting to initialize the class with an invalid precision fails as expected
    invalid_precision = "invalid_precision"
    error_message = (
        f"Unsupported precision argument value ({invalid_precision}) encountered when initializing PrecisionTimer "
        f"class. Use one of the supported precision options: {valid_precision}."
    )
    # noinspection PyTypeChecker
    with pytest.raises(ValueError, match=re.escape(format_message(error_message))):
        # noinspection PyTypeChecker
        PrecisionTimer(invalid_precision)

    # Also verifies that attempting to set the precision of an initialized class to an unsupported value fails as
    # expected
    error_message = (
        f"Unsupported precision argument value ({invalid_precision}) encountered when setting the precision of a "
        f"PrecisionTimer class instance. Use one of the supported precision options: "
        f"{valid_precision}."
    )
    # noinspection PyTypeChecker
    with pytest.raises(ValueError, match=re.escape(format_message(error_message))):
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
    """Tests interval timing functionality of the PrecisionTimer class.

    Does not test runtime precision. Use benchmark_timer script for that purpose. This test just ensures
    that commands run without errors. Uses 'mark' fixture to generate a version of this test for all supported
    precisions and, ideally, should be executed in-parallel with other tests.
    """
    # noinspection PyTypeChecker
    timer = PrecisionTimer(precision)
    verify_interval_method(timer=timer, precision=precision, interval=1)


@pytest.mark.parametrize("precision", ["ns", "us", "ms", "s"])
@pytest.mark.parametrize("allow_sleep", [False, True])
@pytest.mark.parametrize("blocking", [False, True])
def test_delay_timing(precision: str, allow_sleep: bool, blocking: bool) -> None:
    """Tests blocking and non-blocking delay functionality of the PrecisionTimer class.

    Similar to how interval timing is tested, this function does not evaluate delay method precision! Use benchmark
    command to benchmark delay precision on your particular system.
    """
    # noinspection PyTypeChecker
    timer = PrecisionTimer(precision)
    verify_delay_method(timer=timer, precision=precision, delay=1, allow_sleep=allow_sleep, blocking=blocking)


def test_threaded_delay() -> None:
    """Verifies blocking and non-blocking delay method GIL release."""
    # Binds global variables and initializes a seconds' timer
    global global_counter, end_flag
    timer = PrecisionTimer("s")

    # Starts a separate thread that updates the global_counter
    counter_thread = threading.Thread(target=update_global_counter)
    counter_thread.daemon = True  # Set as a daemon, so it automatically closes when the main program exits
    counter_thread.start()

    # Short delay to ensure the counter-thread has started
    tm.sleep(0.1)

    # Verifies that blocking delay prevents the thread from running during the blocking period
    global_counter = 0
    timer.delay_block(delay=2)
    assert global_counter < 5

    # Verifies that non-blocking delay allows the thread to run during the blocking period
    global_counter = 0
    timer.delay_noblock(delay=2)
    assert global_counter > 25

    # Eliminates the thread to avoid nanobind leak warnings
    end_flag = True
    tm.sleep(0.1)
