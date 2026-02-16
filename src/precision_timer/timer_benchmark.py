"""Provides the benchmark used to assess the performance of the PrecisionTimer class on the current host-system."""

import time as tm  # pragma: no cover
from typing import Any  # pragma: no cover

from tqdm import tqdm  # pragma: no cover
import click  # pragma: no cover
import numpy as np  # pragma: no cover
from ataraxis_base_utilities import LogLevel, console  # pragma: no cover

from .timer_class import PrecisionTimer, TimerPrecisions  # pragma: no cover
from ..time_helpers import TimeUnits, convert_time  # pragma: no cover


@click.command()
@click.option(
    "--interval-cycles",
    "-ic",
    type=click.IntRange(min=1, clamp=False),
    default=60,
    show_default=True,
    help="The number of times to repeat the interval benchmark for each of the tested timer precisions.",
)
@click.option(
    "--interval-delay",
    "-id",
    type=click.FloatRange(min=0, min_open=True, clamp=False),
    default=1,
    show_default=True,
    help="The interval duration, in seconds, to use during the interval benchmark for each of the tested timer "
    "precisions.",
)
@click.option(
    "--delay-cycles",
    "-dc",
    nargs=4,
    type=click.IntRange(min=1, clamp=False),
    default=(1000, 1000, 1000, 60),
    show_default=True,
    help="The number of times to repeat the delay benchmark for each of the tested timer precisions. Expects a "
    "space-separated sequence in the order of: ns, us, ms, s.",
)
@click.option(
    "--delay-durations",
    "-dd",
    nargs=4,
    type=click.IntRange(min=1, clamp=False),
    default=(500, 5, 2, 1),
    show_default=True,
    help="The delay duration, in precision-units, to use during the delay benchmark for the tested precisions. "
    "Expects a space-separated sequence in the order of: ns, us, ms, s.",
)
def benchmark(  # pragma: no cover
    interval_cycles: int, interval_delay: float, delay_cycles: tuple[int, ...], delay_durations: tuple[int, ...]
) -> None:
    """Benchmarks the PrecisionTimer class performance on the local host-system. Use this command to determine the
    actual precision of the timer for the local Operating System and CPU clock combination.
    """
    # Enables the console for output.
    console.enable()

    # Initializes the timer class to benchmark.
    timer: PrecisionTimer = PrecisionTimer(precision="ns")

    # Extracts the set of precisions to be benchmarked.
    # noinspection PyTypeChecker
    precisions: tuple[TimerPrecisions, ...] = tuple(TimerPrecisions)

    # Notifies the user that the benchmark has started.
    console.echo(message="Initializing PrecisionTimer benchmark...")

    # Runs and aggregates interval timing results. The interval tests execute the requested delay via PrecisionTimer's
    # 'elapsed' property and time the duration using perf_counter_ns(). It is advised to use second-precision delay
    # intervals to properly test all supported interval timers, even if this requires a few minutes to run. By default,
    # the test takes 4 minutes (1 second x 60 cycles x 4 precisions). Note, perf_counter_ns and PrecisionTimer likely
    # use the same system clock.
    interval_results: list[tuple[TimerPrecisions, np.floating[Any], np.floating[Any]]] = []
    for precision in precisions:
        # Switches the timer to use the tested precision.
        timer.set_precision(precision=precision)
        elapsed_deltas = []
        # Executes the requested number of benchmarking cycles for each precision.
        for _ in tqdm(
            range(interval_cycles), desc=f"Running interval timing benchmark for {precision} precision timer"
        ):
            # Converts the interval delay to the precision used by the elapsed timer and runs a busywait loop.
            interval: float = convert_time(time=interval_delay, from_units=TimeUnits.SECOND, to_units=precision.lower())
            start = tm.perf_counter_ns()
            timer.reset()
            while timer.elapsed < interval:
                pass
            end = tm.perf_counter_ns()
            elapsed_time: float = convert_time(
                time=end - start, from_units=TimeUnits.NANOSECOND, to_units=precision.lower()
            )
            elapsed_deltas.append(elapsed_time)

        # Appends cycle results (mean and std) to the storage list.
        interval_results.append(
            (precision, np.around(np.mean(elapsed_deltas), decimals=3), np.around(np.std(elapsed_deltas), decimals=3))
        )

    # Runs and aggregates busywait delay timing results. Executes blocking and non-blocking delay methods for each
    # tested precision. A separate test suite below benchmarks sleep-based delay methods.
    delay_results_busywait = []
    for index, precision in enumerate(precisions):
        # noinspection PyTypeChecker
        timer.set_precision(precision=precision)
        deltas_block: list[float] = []
        deltas_noblock: list[float] = []

        for _ in tqdm(
            range(delay_cycles[index]), desc=f"Running busywait delay benchmark for {precision} precision timer"
        ):
            # Tests blocking delay.
            start = tm.perf_counter_ns()
            timer.delay(delay=delay_durations[index], allow_sleep=False, block=True)
            end = tm.perf_counter_ns()
            deltas_block.append(convert_time(time=end - start, from_units=TimeUnits.NANOSECOND, to_units=precision))

            # Tests non-blocking delay.
            start = tm.perf_counter_ns()
            timer.delay(delay=delay_durations[index], allow_sleep=False, block=False)
            end = tm.perf_counter_ns()
            deltas_noblock.append(convert_time(time=end - start, from_units=TimeUnits.NANOSECOND, to_units=precision))

        # Appends cycle results (mean and std for blocking and non-blocking delays).
        delay_results_busywait.append(
            (
                precision,
                delay_durations[index],
                np.around(np.mean(deltas_block), decimals=3),
                np.around(np.std(deltas_block), decimals=3),
                np.around(np.mean(deltas_noblock), decimals=3),
                np.around(np.std(deltas_noblock), decimals=3),
            )
        )

    # Evaluates ms and s precisions with sleep instead of busywait delay methods. The benchmark is identical to the
    # busywait benchmark otherwise.
    delay_results_sleep = []
    for index, precision in enumerate((TimerPrecisions.MILLISECOND, TimerPrecisions.SECOND), start=2):
        # noinspection PyTypeChecker
        timer.set_precision(precision=precision)
        deltas_block = []
        deltas_noblock = []

        for _ in tqdm(
            range(delay_cycles[index]), desc=f"Running sleep delay benchmark for {precision} precision timer"
        ):
            # Tests blocking delay.
            start = tm.perf_counter_ns()
            timer.delay(delay=delay_durations[index], allow_sleep=True, block=True)
            end = tm.perf_counter_ns()
            deltas_block.append(convert_time(time=end - start, from_units=TimeUnits.NANOSECOND, to_units=precision))

            # Tests non-blocking delay.
            start = tm.perf_counter_ns()
            timer.delay(delay=delay_durations[index], allow_sleep=True, block=False)
            end = tm.perf_counter_ns()
            deltas_noblock.append(convert_time(time=end - start, from_units=TimeUnits.NANOSECOND, to_units=precision))

        # Appends cycle results (mean and std for blocking and non-blocking delays).
        delay_results_sleep.append(
            (
                precision,
                delay_durations[index],
                np.around(np.mean(deltas_block), decimals=3),
                np.around(np.std(deltas_block), decimals=3),
                np.around(np.mean(deltas_noblock), decimals=3),
                np.around(np.std(deltas_noblock), decimals=3),
            )
        )

    # Displays the test results using click.echo for formatted table output.
    click.echo("\nResults:")
    click.echo("Interval Timing:")
    click.echo("Precision | Interval Time | Mean Recorded Time | Std Recorded Time")
    click.echo("----------+---------------+--------------------+------------------")
    for precision, mean, std in interval_results:
        click.echo(
            f"{precision:9} | "
            f"{convert_time(time=interval_delay, from_units=TimeUnits.SECOND, to_units=precision):13} | "
            f"{mean:18.3f} | {std:16.3f}"
        )

    click.echo("\nBusy-wait Delay Timing:")
    click.echo("Precision | Delay Duration | Mean Block Time | Std Block Time | Mean Noblock Time | Std Noblock Time")
    click.echo("----------+----------------+-----------------+----------------+-------------------+-----------------")
    for precision, delay_duration, block_mean, block_std, noblock_mean, noblock_std in delay_results_busywait:
        click.echo(
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

    console.echo(message="Benchmark: Complete.", level=LogLevel.SUCCESS)
