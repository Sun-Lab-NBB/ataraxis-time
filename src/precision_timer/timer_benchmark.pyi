from ..time_helpers.helper_functions import convert_time as convert_time
from .timer_class import PrecisionTimer as PrecisionTimer

def benchmark(
    interval_cycles: int, interval_delay: float, delay_cycles: tuple[int], delay_durations: tuple[int]
) -> None: ...
