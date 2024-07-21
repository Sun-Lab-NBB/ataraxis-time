from .timer_class import PrecisionTimer as PrecisionTimer
from ..time_helpers.helper_functions import convert_time as convert_time

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
