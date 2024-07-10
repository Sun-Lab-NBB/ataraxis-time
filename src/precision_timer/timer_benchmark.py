"""This module contains the benchmark() function used to assess the performance of the PrecisionTimer class on
the intended host-system.

To improve user-experience, installing the library automatically generates a shorthand 'benchmark_timer' command that
allows calling the benchmark() method from the CLI without using the short (ataraxis_time.benchmark) or the full
method path (ataraxis_time.precision_timer.timer_benchmark.benchmark).

Calling benchmark_timer with --help argument displays the list of command line arguments that can be used to configure
the behavior of the benchmark. The default benchmark arguments are designed to offer a high-confidence result
without excessive time expenditures, but may not be optimal for all users. The CLI options are also listed in the online
API documentation.
"""

import time as tm

from tqdm import tqdm
import click
import numpy as np

from .timer_class import PrecisionTimer
from ..time_helpers.helper_functions import convert_time


@click.command()
@click.option(
    "--interval-cycles",
    "-ic",
    type=click.IntRange(min=1, clamp=False),
    default=60,
    help="Number of times to repeat the interval benchmark for each of the tested precisions. Example: -ic 60",
)
@click.option(
    "--interval-delay",
    "-id",
    type=click.FloatRange(min=0, min_open=True, clamp=False),
    default=1,
    help="The interval duration, in seconds, to use during the interval benchmark for each of the tested precisions. "
    "Example: -id 1",
)
@click.option(
    "--delay-cycles",
    "-dc",
    nargs=4,
    type=click.IntRange(min=1, clamp=False),
    default=(1000, 1000, 1000, 60),
    help="Number of times to repeat the delay benchmark (blocking and non-blocking) for each of the tested "
    "precisions. Expects a space-separated sequence in the order of: ns, us, ms, s. "
    "Example: -dc 1000 1000 1000 60",
)
@click.option(
    "--delay-durations",
    "-dd",
    nargs=4,
    type=click.IntRange(min=1, clamp=False),
    default=(500, 5, 2, 1),
    help="The delay duration, in precision-units, to use during the delay benchmark (blocking and non-blocking) "
    "for each of the tested precisions. Expects a space-separated sequence in the order of: ns, us, ms, s. "
    "Example: -dd 500 5 2 1",
)
def benchmark(
    interval_cycles: int, interval_delay: float, delay_cycles: tuple[int], delay_durations: tuple[int]
) -> None:
    """This function is used to benchmark the PrecisionTimer class performance for the caller host system.

    It is highly advised to use this function to evaluate the precision and performance of the timer for each intended
    host system, as these parameters vary for each tested OS and Platform combination. Additionally, the performance of
    the timer may be affected by the overall system utilization and particular use-patterns.

    Notes:
        This command is accessible from a CLI interface via a shorthand benchmark_timer command, following library
        installation.
    """
    # Initializes the timer class to benchmark
    timer: PrecisionTimer = PrecisionTimer(precision="ns")

    # Extracts the set of precisions to be benchmarked
    precisions = timer.supported_precisions

    # Notifies the user that the benchmark has started
    click.echo("Timer Benchmark: Initialized.")

    # Runs and aggregates interval timing results into a storage array. The interval tests consist of executing the
    # requested delay (via PrecisionTimer 'elapsed' property) and timing the duration of the delay using
    # perf_counter_ns() method from time library. It is advised to use second-precision delay intervals to properly
    # test all supported interval timers, even if this requires a few minutes to run the test cycles. By default, the
    # test takes 4 minutes (1 second x 60 cycles x 4 precisions) to run. Of note, it is very likely that perf_counter_ns
    # and PrecisionTimer use the same system-clock.
    interval_results: list[tuple[str, np.float64, np.float64]] = []
    for precision in precisions:
        # Switches the timer to use the tested precision
        timer.set_precision(precision=precision)  # type: ignore
        elapsed_deltas = []
        # Executes the requested number of benchmarking cycles for each precision
        for _ in tqdm(
            range(interval_cycles), desc=f"Running interval timing benchmark for {precision} precision timer"
        ):
            # Delays for the requested number of seconds, converted into the precision used by the elapsed timer.
            # This relies on a local 'busywait' loop that uses 'elapsed()' property of the timer.
            precision = precision.lower()
            interval: float = convert_time(interval_delay, from_units="s", to_units=precision)  # type: ignore
            start = tm.perf_counter_ns()
            timer.reset()  # Resets the timer
            while timer.elapsed < interval:
                pass
            end = tm.perf_counter_ns()  # Records the time counted by the timer during the delay
            elapsed_time = convert_time(end - start, from_units="ns", to_units=precision)  # type: ignore
            elapsed_deltas.append(elapsed_time)

        # Calculates the mean and std for the recorded elapsed times and adds them to the results' list alongside some
        # ID information.
        # Appends cycle results to the storage list
        interval_results.append(
            (precision, np.around(np.mean(elapsed_deltas), 3), np.around(np.std(elapsed_deltas), 3))  # type: ignore
        )

    # Runs and aggregates delay timing results into a storage array. The delay timing tests rely on executing blocking
    # and non-blocking delay methods for each tested precision. Note, this collection explicitly uses busy-wait method
    # and a separate delay test suite is used to benchmark sleep-using delay methods.
    delay_results_busywait = []
    for index, precision in enumerate(precisions):  # Loops over all precisions
        # noinspection PyTypeChecker
        timer.set_precision(precision=precision)  # type: ignore
        deltas_block: list[float] = []
        deltas_noblock: list[float] = []

        for _ in tqdm(
            range(delay_cycles[index]), desc=f"Running busywait delay benchmark for {precision} precision timer"
        ):
            # Tests blocking delay
            start = tm.perf_counter_ns()
            timer.delay_block(delay=delay_durations[index], allow_sleep=False)
            end = tm.perf_counter_ns()
            deltas_block.append(convert_time((end - start), from_units="ns", to_units=precision))  # type: ignore

            # Tests non-blocking delay
            start = tm.perf_counter_ns()
            timer.delay_noblock(delay=delay_durations[index], allow_sleep=False)
            end = tm.perf_counter_ns()
            deltas_noblock.append(convert_time((end - start), from_units="ns", to_units=precision))  # type: ignore

        # Calculates the mean and std for both blocking and non-blocking delays and adds them to the results' list
        # alongside some ID information.
        delay_results_busywait.append(
            (
                precision,
                delay_durations[index],
                np.around(np.mean(deltas_block), 3),
                np.around(np.std(deltas_block), 3),
                np.around(np.mean(deltas_noblock), 3),
                np.around(np.std(deltas_noblock), 3),
            )
        )

    # This benchmark evaluates ms and s precisions with sleep instead of busywait delay methods. The benchmark is
    # identical to the busywait benchmark otherwise.
    delay_results_sleep = []
    for index, precision in enumerate(["ms", "s"], start=2):  # Loops over all precisions
        # noinspection PyTypeChecker
        timer.set_precision(precision=precision)  # type: ignore
        deltas_block = []
        deltas_noblock = []

        for _ in tqdm(
            range(delay_cycles[index]), desc=f"Running sleep delay benchmark for {precision} precision timer"
        ):
            # Tests blocking delay
            start = tm.perf_counter_ns()
            timer.delay_block(delay=delay_durations[index], allow_sleep=True)
            end = tm.perf_counter_ns()
            deltas_block.append(convert_time((end - start), from_units="ns", to_units=precision))  # type: ignore

            # Tests non-blocking delay
            start = tm.perf_counter_ns()
            timer.delay_noblock(delay=delay_durations[index], allow_sleep=True)
            end = tm.perf_counter_ns()
            deltas_noblock.append(convert_time((end - start), from_units="ns", to_units=precision))  # type: ignore

        # Calculates the mean and std for both blocking and non-blocking delays and adds them to the results' list
        # alongside some ID information.
        delay_results_sleep.append(
            (
                precision,
                delay_durations[index],
                np.around(np.mean(deltas_block), 3),
                np.around(np.std(deltas_block), 3),
                np.around(np.mean(deltas_noblock), 3),
                np.around(np.std(deltas_noblock), 3),
            )
        )

    # Displays the test results
    click.echo("\nResults:")
    click.echo("Interval Timing:")
    click.echo("Precision | Interval Time | Mean Recorded Time | Std Recorded Time")
    click.echo("----------+---------------+--------------------+------------------")
    for index, (precision, mean, std) in enumerate(interval_results, start=1):
        # noinspection PyTypeChecker,LongLine
        click.echo(
            f"{precision:9} | {convert_time(interval_delay, 's', precision):13} | {mean:18.3f} | {std:16.3f}"  # type: ignore
        )

    click.echo("\nBusy-wait Delay Timing:")
    click.echo("Precision | Delay Duration | Mean Block Time | Std Block Time | Mean Noblock Time | Std Noblock Time")
    click.echo("----------+----------------+-----------------+----------------+-------------------+-----------------")
    for precision, delay_duration, block_mean, block_std, noblock_mean, noblock_std in delay_results_busywait:
        print(
            f"{precision:9} | {delay_duration:14} | {block_mean:15.3f} | {block_std:14.3f} | {noblock_mean:17.3f} | "
            f"{noblock_std:16.3f}"
        )

    click.echo("\nSleep Delay Timing:")
    click.echo("Precision | Delay Duration | Mean Block Time | Std Block Time | Mean Noblock Time | Std Noblock Time")
    click.echo("----------+----------------+-----------------+----------------+-------------------+-----------------")
    for precision, delay_duration, block_mean, block_std, noblock_mean, noblock_std in delay_results_sleep:
        click.echo(
            f"{precision:9} | {delay_duration:14} | {block_mean:15.3f} | {block_std:14.3f} | {noblock_mean:17.3f} | "
            f"{noblock_std:16.3f}"
        )

    click.echo("\nBenchmark: Complete.")
