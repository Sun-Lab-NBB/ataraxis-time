from .timer import (
    PrecisionTimer as PrecisionTimer,
    TimerPrecisions as TimerPrecisions,
)
from ..utilities import (
    TimeUnits as TimeUnits,
    convert_time as convert_time,
)

def benchmark(
    interval_cycles: int, interval_delay: float, delay_cycles: tuple[int, ...], delay_durations: tuple[int, ...]
) -> None: ...
