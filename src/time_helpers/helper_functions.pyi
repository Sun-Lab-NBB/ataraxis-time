import numpy as np
from ..utilities import format_message as format_message
from numpy.typing import NDArray as NDArray
from typing import Literal

def convert_time(time: int | float | NDArray[np.int8 | np.int16 | np.int32 | np.int64 | np.uint8 | np.uint16 | np.uint32 | np.uint64 | np.float16 | np.float32 | np.float64] | list[int | float], from_units: Literal['ns', 'us', 'ms', 's', 'm', 'h', 'd'], to_units: Literal['ns', 'us', 'ms', 's', 'm', 'h', 'd']) -> float | NDArray[np.float64] | list[float]: ...
def get_timestamp(time_separator: str = ...) -> str: ...
