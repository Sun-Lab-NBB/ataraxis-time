# ataraxis-time

A Python library that provides a high-precision thread-safe timer and helper methods to work with date and time data.

![PyPI - Version](https://img.shields.io/pypi/v/ataraxis-time)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ataraxis-time)
[![uv](https://tinyurl.com/uvbadge)](https://github.com/astral-sh/uv)
[![Ruff](https://tinyurl.com/ruffbadge)](https://github.com/astral-sh/ruff)
![type-checked: mypy](https://img.shields.io/badge/type--checked-mypy-blue?style=flat-square&logo=python)
![PyPI - License](https://img.shields.io/pypi/l/ataraxis-time)
![PyPI - Status](https://img.shields.io/pypi/status/ataraxis-time)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/ataraxis-time)
___

## Detailed Description

This library uses the 'chrono' C++ library to access the fastest available system clock and use it to provide interval
timing and delay functionality via a Python binding API. While the performance of the timer heavily depends on the
particular system configuration and utilization, most modern CPUs should be capable of microsecond precision using
this timer. Due to using a C-extension to provide interval and delay timing functionality, the library is thread- and
process-safe and releases the GIL when using the appropriate delay command configuration. Additionally, the library 
offers a set of standalone helper functions for manipulating date and time data.

___

## Features

- Supports Windows, Linux, and macOS.
- Microsecond precision on modern CPUs (~ 3 GHz+) during delay and interval timing.
- Releases GIL during (non-blocking) delay timing even when using microsecond and nanosecond precision.
- GPL 3 License.

___

## Table of Contents

- [Dependencies](#dependencies)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Developers](#developers)
- [Versioning](#versioning)
- [Authors](#authors)
- [License](#license)
- [Acknowledgements](#Acknowledgments)

___

## Dependencies

For users, all library dependencies are installed automatically by all supported installation methods 
(see the [Installation](#installation) section).

***Note!*** Developers should see the [Developers](#developers) section for information on installing additional 
development dependencies.

___

## Installation

### Source

Note, installation from source is ***highly discouraged*** for anyone who is not an active project developer.

1. Download this repository to the local machine using the preferred method, such as git-cloning. Use one of the 
   [stable releases](https://github.com/Sun-Lab-NBB/ataraxis-time/tags) that include precompiled binary and source code 
   distribution (sdist) wheels.
2. ```cd``` to the root directory of the project.
3. Run ```python -m pip install .``` to install the project. Alternatively, if using a distribution with precompiled
   binaries, use ```python -m pip install WHEEL_PATH```, replacing 'WHEEL_PATH' with the path to the wheel file.

### pip

Use the following command to install the library using pip: ```pip install ataraxis-time```

___

## Usage

### Precision Timer
The timer API is intentionally minimalistic to simplify class adoption and usage. It is heavily inspired by the
[elapsedMillis](https://github.com/pfeerick/elapsedMillis/blob/master/elapsedMillis.h) library for 
Teensy and Arduino microcontrollers.

All timer class functionality is realized through a fast C-extension class wrapped into the PrecisionTimer class. 
Primarily, the functionality comes through 3 class methods: reset(), elapsed (property), and delay():

#### Initialization and Configuration
The timer takes the 'precision' to use as the only initialization argument. All instances of the timer class are 
thread- and process-safe and do not interfere with each other.

```
from ataraxis_time import PrecisionTimer, TimerPrecisions
from ataraxis_base_utilities import console
console.enable()

# Currently, the timer supports 4 'precisions: 'ns' (nanoseconds), 'us' (microseconds), 'ms' (milliseconds), and
# 's' seconds. All precisions are defined in the TimerPrecisions enumeration.
timer = PrecisionTimer(TimerPrecisions.MICROSECOND)
console.echo(f"Precision: {timer.precision}")

# The precision can be adjusted after initialization if needed. While not recommended, it is possible to provide the
# precision as a string instead of using the TimerPrecisions enumeration.
timer.set_precision('ms')  # Switches timer precision to milliseconds
console.echo(f"Precision: {timer.precision}")
```

#### Interval Timing
Interval timing functionality is realized through two methods: reset() and elapsed. This functionality of the class
is identical to using perf_counter_ns() from the 'time' library. The main difference from the 'time' library is that 
the PrecisionTimer uses a slightly different interface (reset / elapsed) and automatically converts the output to the 
desired precision.
```
from ataraxis_time import PrecisionTimer
import time as tm
from ataraxis_base_utilities import console

timer = PrecisionTimer('us')
console.enable()

# Interval timing example
timer.reset()  # Resets (re-bases) the timer
tm.sleep(1)  # Simulates work (for 1 second)
console.echo(f'Work time: {timer.elapsed} us')
```

#### Delay
Delay timing functionality is the primary advantage of this library over the standard 'time' library. At the time of 
writing, the 'time' library can provide nanosecond-precise delays via a 'busywait' perf_counter_ns() function that does 
not release the GIL. Alternatively, it can release the GIL via the sleep() function, but it is only accurate 
up to millisecond precision. PrecisionTimer class can delay for time-periods within microsecond precision, while 
releasing or holding the GIL.
```
import threading
import time
from ataraxis_time import PrecisionTimer
from ataraxis_base_utilities import console

# Instantiates a global counter for the background thread
counter = 0
stop = False


def count_in_background():
    """Background thread that increments the global counter."""
    global counter
    while not stop:
        counter += 1


# Setup
timer = PrecisionTimer('us')
console.enable()

# Starts the background counter thread
thread = threading.Thread(target=count_in_background, daemon=True)
thread.start()
time.sleep(0.1)

# GIL-releasing microsecond delay:
console.echo("block=False (releases GIL):")
counter = 0  # Resets the counter
timer.delay(100, block=False)  # 100us delay
non_blocking_count = counter
console.echo(f"counter = {counter}")

# Non-GIL-releasing microsecond delay:
console.echo("block=True (holds GIL):")
counter = 0  # Resets the counter
timer.delay(100, block=True)  # 100us delay
blocking_count = counter
console.echo(f"counter = {counter}")

# Cleanup
stop = True

# With microsecond precisions, blocking runtime often results in the counter not being incremented at all.
if blocking_count == 0:
    blocking_count = 1
console.echo(f"Difference: block=False allows ~{non_blocking_count/blocking_count:.0f}x more counting!")
thread.join()
```

### Date & Time Helper Functions
These are minor helper functions that are not directly part of the timer class showcased above. Since these functions 
are not intended for realtime applications, they are implemented entirely in Python.

#### Convert Time
This helper function performs time-conversions, rounding to 3 Significant Figures for the chosen precision, and works 
with time-scales from nanoseconds to days.
```
from ataraxis_time import convert_time, TimeUnits
from ataraxis_base_utilities import console
console.enable()

# The conversion works for Python and NumPy scalars. Use the TimeUnits enumeration to specify input and
# output units. Note, by default, the method returns the converted data as NumPy 64-bit floating scalars.
initial_time = 12
time_in_seconds = convert_time(time=initial_time, from_units=TimeUnits.DAY, to_units=TimeUnits.SECOND)
console.echo(f"12 days is {time_in_seconds} seconds.")

# While discouraged, it is possible to provide the units directly, instead of using the TimeUnits enumeration. Also,
# it is possible to instruct the function to return Python floats.
initial_time = 5
time_in_seconds = convert_time(time=initial_time, from_units="s", to_units="m", as_float=True)
console.echo(f"5 seconds is {time_in_seconds} minutes.")
```

#### Timestamps
Timestamp methods are used to generate and work with microsecond-precise UTC timestamps. They work by connecting to 
one of the global time-servers and getting the current timestamp for the UTC timezone. The generated timestamp can be 
returned as and freely converted between the three supported formats: string, bytes’ array, and an integer number of 
microseconds elapsed since the UTC epoch onset.
```
from ataraxis_time import get_timestamp, convert_timestamp, TimestampFormats
from ataraxis_base_utilities import console

console.enable()

# Gets the current date and time and uses it to generate a timestamp that can be used in file-names (for example).
# The timestamp is precise up to microseconds. Use TimestampFormats to specify the desired format.
dt = get_timestamp(time_separator='-', output_format=TimestampFormats.STRING)
console.echo(f"Current timestamp: {dt}.")

# The function also supports giving the timestamp as a serialized array of bytes. This is helpful when it is used as
# part of a serialized communication protocol.
bytes_dt = get_timestamp(output_format=TimestampFormats.BYTES)
console.echo(f"Byte-serialized current timestamp value: {bytes_dt}.")

# Use the convert_timestamp() function to convert the timestamp to a different format. It supports cross-converting
# all timestamp formats stored in the TimestampFormats enumeration.
integer_dt = convert_timestamp(timestamp=bytes_dt, output_format=TimestampFormats.INTEGER)
string_dt = convert_timestamp(timestamp=integer_dt, output_format=TimestampFormats.STRING)
console.echo(
    f"The timestamp can be read as a string: {string_dt}. It can also be read as the number of microseconds elapsed "
    f"since UTC epoch onset: {integer_dt}."
)
```
___

## API Documentation

See the [API documentation](https://ataraxis-time-api-docs.netlify.app/) for the
detailed description of the methods and classes exposed by the components of this library. 
__*Note*__, the documentation also covers the C++ source code and the ```axt-benchmark``` Command-Line-Interface 
(CLI) command.

___

## Developers

This section provides installation, dependency, and build-system instructions for project developers.

### Installing the Project

***Note!*** This installation method requires **mamba version 2.3.2 or above**.

1. Download this repository to the local machine using the preferred method, such as git-cloning.
2. ```cd``` to the root project directory.
3. Install core Sun lab development dependencies into the ***base*** mamba environment via the 
   ```mamba install tox uv tox-uv``` command.
4. Use the ```tox -e create``` command to create the project-specific development environment followed by 
   ```tox -e install``` command to install the project into that environment as a library.

### Additional Dependencies

In addition to installing the project and all user dependencies, install the following dependencies:

1. [Python](https://www.python.org/downloads/) distributions, one for each version supported by the developed project. 
   Currently, this library supports the three latest stable versions. It is recommended to use a tool like 
   [pyenv](https://github.com/pyenv/pyenv) to install and manage the required versions.
2. [Doxygen](https://www.doxygen.nl/manual/install.html), if you want to generate C++ code documentation.
3. An appropriate build tool or Docker, if you intend to build binary wheels via
   [cibuildwheel](https://cibuildwheel.pypa.io/en/stable/). See the link for information on which dependencies to
   install for each development platform.

### Development Automation

This project comes with a fully configured set of automation pipelines implemented using 
[tox](https://tox.wiki/en/latest/user_guide.html). Check the [tox.ini file](tox.ini) for details about the 
available pipelines and their implementation. Alternatively, call ```tox list``` from the root directory of the project
to see the list of available tasks.

**Note!** All pull requests for this project have to successfully complete the ```tox``` task before being merged. 
To expedite the task’s runtime, use the ```tox --parallel``` command to run some tasks in-parallel.

### Automation Troubleshooting

Many packages used in 'tox' automation pipelines (uv, mypy, ruff) and 'tox' itself may experience runtime failures. In 
most cases, this is related to their caching behavior. If an unintelligible error is encountered with 
any of the automation components, deleting the corresponding .cache (.tox, .ruff_cache, .mypy_cache, etc.) manually 
or via a CLI command typically solves the issue.

___

## Versioning

This project uses [semantic versioning](https://semver.org/). For the versions available, see the 
[tags on this repository](https://github.com/Sun-Lab-NBB/ataraxis-time/tags).

---

## Authors

- Ivan Kondratyev ([Inkaros](https://github.com/Inkaros))

___

## License

This project is licensed under the GPL3 License: see the [LICENSE](LICENSE) file for details.

___

## Acknowledgments

- All Sun Lab [members](https://neuroai.github.io/sunlab/people) for providing the inspiration and comments during the
  development of this library.
- [elapsedMillis](https://github.com/pfeerick/elapsedMillis/blob/master/elapsedMillis.h) project for providing the 
  inspiration for the API and the functionality of the timer class.
- [nanobind](https://github.com/wjakob/nanobind) project for providing a fast and convenient way of binding C++ code to
  Python projects.
- The creators of all other dependencies and projects listed in the [pyproject.toml](pyproject.toml) file.

___