# ataraxis-time

Provides a high-precision thread-safe timer and helper methods to work with date and time data.

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
timing, delay, timeout, and polling functionality via a Python binding API. While the performance of the timer heavily
depends on the particular system configuration and utilization, most modern CPUs should be capable of microsecond
precision using this timer. Due to using a C-extension to provide interval and delay timing functionality, the library
is thread- and process-safe and releases the GIL when using the appropriate delay command configuration. Additionally,
the library offers a set of standalone helper functions for manipulating date and time data, including timestamp
generation and parsing, time-unit conversion, rate-interval conversion, and timedelta interoperability.

## Features

- Supports Windows, Linux, and macOS.
- Microsecond precision on modern CPUs (~ 3 GHz+) during delay and interval timing.
- Releases GIL during (non-blocking) delay timing even when using microsecond and nanosecond precision.
- Timeout guard class for activity-based and duration-based timeout tracking.
- Lap recording, human-readable elapsed time formatting, and periodic polling via an infinite generator.
- Frequency-to-interval and interval-to-frequency conversion helpers.
- Timestamp generation, conversion, and parsing with configurable precision levels.
- Interoperability with Python datetime.timedelta objects.
- Apache 2.0 License.

## Table of Contents

- [Dependencies](#dependencies)
- [Installation](#installation)
- [Usage](#usage)
  - [Precision Timer](#precision-timer)
  - [Timeout](#timeout)
  - [Date and Time Helper Functions](#date-and-time-helper-functions)
- [API Documentation](#api-documentation)
- [Developers](#developers)
- [Versioning](#versioning)
- [Authors](#authors)
- [License](#license)
- [Acknowledgments](#acknowledgments)

___

## Dependencies

For users, all library dependencies are installed automatically by all supported installation
methods. For developers, see the [Developers](#developers) section for information on installing
additional development dependencies.

___

## Installation

### Source

***Note,*** installation from source is ***highly discouraged*** for anyone who is not an active
project developer.

1. Download this repository to the local machine using the preferred method, such as git-cloning.
   Use one of the [stable releases](https://github.com/Sun-Lab-NBB/ataraxis-time/tags) that
   include precompiled binary and source code distribution (sdist) wheels.
2. If the downloaded distribution is stored as a compressed archive, unpack it using the
   appropriate decompression tool.
3. `cd` to the root directory of the prepared project distribution.
4. Run `pip install .` to install the project and its dependencies.

### pip

Use the following command to install the library and all of its dependencies via
[pip](https://pip.pypa.io/en/stable/): `pip install ataraxis-time`

___

## Usage

### Precision Timer

The timer API is intentionally minimalistic to simplify class adoption and usage. It is heavily inspired by the
[elapsedMillis](https://github.com/pfeerick/elapsedMillis/blob/master/elapsedMillis.h) library for
Teensy and Arduino microcontrollers.

All timer class functionality is realized through a fast C-extension class wrapped into the PrecisionTimer class.

#### Initialization and Configuration

The timer takes the 'precision' to use as the only initialization argument. All instances of the timer class are
thread- and process-safe and do not interfere with each other.

```python
from ataraxis_time import PrecisionTimer, TimerPrecisions

# Currently, the timer supports 4 precisions: 'ns' (nanoseconds), 'us' (microseconds), 'ms' (milliseconds), and
# 's' (seconds). All precisions are defined in the TimerPrecisions enumeration.
timer = PrecisionTimer(TimerPrecisions.MICROSECOND)
print(f"Precision: {timer.precision}")

# The precision can be adjusted after initialization if needed. While not recommended, it is possible to provide the
# precision as a string instead of using the TimerPrecisions enumeration.
timer.set_precision('ms')  # Switches timer precision to milliseconds
print(f"Precision: {timer.precision}")
```

#### Interval Timing

Interval timing functionality is realized through two methods: reset() and the elapsed property. This functionality is
identical to using perf_counter_ns() from the 'time' library. The main difference is that PrecisionTimer uses a
slightly different interface (reset / elapsed) and automatically converts the output to the desired precision.

```python
from ataraxis_time import PrecisionTimer
import time as tm

timer = PrecisionTimer('us')

# Interval timing example
timer.reset()  # Resets (re-bases) the timer
tm.sleep(1)  # Simulates work (for 1 second)
print(f'Work time: {timer.elapsed} us')
```

#### Delay

Delay timing functionality is the primary advantage of this library over the standard 'time' library. At the time of
writing, the 'time' library can provide nanosecond-precise delays via a 'busywait' perf_counter_ns() function that does
not release the GIL. Alternatively, it can release the GIL via the sleep() function, but it is only accurate
up to millisecond precision. The PrecisionTimer class can delay for time-periods within microsecond precision, while
releasing or holding the GIL.

```python
import threading
import time
from ataraxis_time import PrecisionTimer

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

# Starts the background counter thread
thread = threading.Thread(target=count_in_background, daemon=True)
thread.start()
time.sleep(0.1)

# GIL-releasing microsecond delay:
print("block=False (releases GIL):")
counter = 0  # Resets the counter
timer.delay(100, block=False)  # 100us delay
non_blocking_count = counter
print(f"counter = {counter}")

# Non-GIL-releasing microsecond delay:
print("block=True (holds GIL):")
counter = 0  # Resets the counter
timer.delay(100, block=True)  # 100us delay
blocking_count = counter
print(f"counter = {counter}")

# Cleanup
stop = True

# With microsecond precisions, blocking runtime often results in the counter not being incremented at all.
if blocking_count == 0:
    blocking_count = 1
print(f"Difference: block=False allows ~{non_blocking_count/blocking_count:.0f}x more counting!")
thread.join()
```

#### Lap Timing

The lap() method records the current elapsed time, appends it to an internal list, and resets the timer. All recorded
lap times are accessible through the laps property.

```python
from ataraxis_time import PrecisionTimer
import time as tm

timer = PrecisionTimer('ms')

# Records three laps
for i in range(3):
    tm.sleep(0.1)  # Simulates work
    duration = timer.lap()
    print(f"Lap {i + 1}: {duration} ms")

# Retrieves all recorded laps as a tuple
print(f"All laps: {timer.laps}")
```

#### Formatted Elapsed Time

The format_elapsed() method returns the current elapsed time as a human-readable string, automatically selecting the
most appropriate units.

```python
from ataraxis_time import PrecisionTimer
import time as tm

timer = PrecisionTimer('us')
tm.sleep(2.5)  # Simulates work
print(f"Elapsed: {timer.format_elapsed()}")  # e.g. "2 s 500.117 ms"
print(f"Detailed: {timer.format_elapsed(max_fields=3)}")  # e.g. "2 s 500 ms 117.0 us"
```

#### Polling

The poll() method provides an infinite generator that yields an iteration count after each delay cycle. This is useful
for periodic task execution.

```python
from ataraxis_time import PrecisionTimer

timer = PrecisionTimer('ms')

# Polls every 100 ms, runs 10 iterations
for count in timer.poll(100):
    print(f"Iteration {count}")
    if count >= 10:
        break
```

### Timeout

The Timeout class provides a timeout guard built on PrecisionTimer. It supports checking whether a specified duration
has elapsed and offers activity-based reset (kick) and full reset with optional duration changes.

```python
from ataraxis_time import Timeout
import time as tm

# Creates a 500 ms timeout
timeout = Timeout(duration=500, precision='ms')

# Checks timeout status
tm.sleep(0.1)
print(f"Expired: {timeout.expired}")  # False
print(f"Remaining: {timeout.remaining} ms")
print(f"Elapsed: {timeout.elapsed} ms")

# Resets the timeout timer without changing the duration (activity-based reset)
timeout.kick()

# Resets the timeout with a new duration
timeout.reset(duration=1000)
```

### Date and Time Helper Functions

These are helper functions that are not directly part of the timer classes showcased above. Since these functions
are not intended for realtime applications, they are implemented entirely in Python.

#### Convert Time

This helper function performs time-conversions, rounding to 3 decimal places, and works with time-scales from
nanoseconds to days.

```python
from ataraxis_time import convert_time, TimeUnits

# The conversion works for Python and NumPy scalars. Use the TimeUnits enumeration to specify input and
# output units. By default, the method returns the converted data as NumPy 64-bit floating scalars.
initial_time = 12
time_in_seconds = convert_time(time=initial_time, from_units=TimeUnits.DAY, to_units=TimeUnits.SECOND)
print(f"12 days is {time_in_seconds} seconds.")

# It is possible to provide the units directly, instead of using the TimeUnits enumeration. Also,
# it is possible to instruct the function to return Python floats.
initial_time = 5
time_in_minutes = convert_time(time=initial_time, from_units="s", to_units="m", as_float=True)
print(f"5 seconds is {time_in_minutes} minutes.")
```

#### Rate and Interval Conversion

The rate_to_interval() and interval_to_rate() functions convert between frequencies (Hz) and time intervals.

```python
from ataraxis_time import rate_to_interval, interval_to_rate, TimeUnits

# Converts a 30 Hz frequency to a microsecond interval
interval_us = rate_to_interval(rate=30, to_units=TimeUnits.MICROSECOND)
print(f"30 Hz = {interval_us} us interval")

# Converts a 1000 us interval back to Hz
rate_hz = interval_to_rate(interval=1000, from_units=TimeUnits.MICROSECOND)
print(f"1000 us = {rate_hz} Hz")
```

#### Timedelta Interoperability

The to_timedelta() and from_timedelta() functions convert between numeric time values and Python datetime.timedelta
objects.

```python
from ataraxis_time import to_timedelta, from_timedelta, TimeUnits

# Converts 500 milliseconds to a timedelta
td = to_timedelta(time=500, from_units=TimeUnits.MILLISECOND)
print(f"500 ms as timedelta: {td}")

# Converts a timedelta back to microseconds
us_value = from_timedelta(timedelta_value=td, to_units=TimeUnits.MICROSECOND)
print(f"Timedelta as microseconds: {us_value}")
```

#### Timestamps

Timestamp methods generate and work with microsecond-precise UTC timestamps. The generated timestamp can be returned
as and freely converted between three supported formats: string, bytes array, and an integer number of microseconds
elapsed since the UTC epoch onset. The precision parameter controls how much detail is included in the output.

```python
from ataraxis_time import get_timestamp, convert_timestamp, TimestampFormats, TimestampPrecisions

# Gets the current date and time as a timestamp. The timestamp is precise up to microseconds by default.
# Use TimestampFormats to specify the desired format.
dt = get_timestamp(time_separator='-', output_format=TimestampFormats.STRING)
print(f"Current timestamp: {dt}.")

# Uses the precision parameter to control the detail level of the output.
dt_day = get_timestamp(output_format=TimestampFormats.STRING, precision=TimestampPrecisions.DAY)
print(f"Day-precision timestamp: {dt_day}.")

# The function also supports giving the timestamp as a serialized array of bytes. This is helpful when it is used as
# part of a serialized communication protocol.
bytes_dt = get_timestamp(output_format=TimestampFormats.BYTES)
print(f"Byte-serialized current timestamp value: {bytes_dt}.")

# Use the convert_timestamp() function to convert the timestamp to a different format. It supports cross-converting
# all timestamp formats stored in the TimestampFormats enumeration.
integer_dt = convert_timestamp(timestamp=bytes_dt, output_format=TimestampFormats.INTEGER)
string_dt = convert_timestamp(timestamp=integer_dt, output_format=TimestampFormats.STRING)
print(
    f"The timestamp can be read as a string: {string_dt}. It can also be read as the number of microseconds elapsed "
    f"since UTC epoch onset: {integer_dt}."
)
```

#### Parse Timestamp

The parse_timestamp() function parses arbitrary datetime strings using strptime-compatible format strings and returns
them as timestamps in any supported format.

```python
from ataraxis_time import parse_timestamp, TimestampFormats

# Parses a datetime string into a microsecond integer timestamp
us_timestamp = parse_timestamp(
    date_string="2024-03-15 14:30:00",
    format_string="%Y-%m-%d %H:%M:%S",
    output_format=TimestampFormats.INTEGER,
)
print(f"Parsed timestamp: {us_timestamp}")

# Parses into a string timestamp with day precision
day_timestamp = parse_timestamp(
    date_string="March 15, 2024",
    format_string="%B %d, %Y",
    output_format=TimestampFormats.STRING,
    precision="day",
)
print(f"Day-precision parsed timestamp: {day_timestamp}")
```

___

## API Documentation

See the [API documentation](https://ataraxis-time-api-docs.netlify.app/) for the detailed
description of the methods and classes exposed by components of this library. The documentation
also covers the C++ source code and the `axt-benchmark` CLI command.

___

## Developers

This section provides installation, dependency, and build-system instructions for the developers
that want to modify the source code of this library.

### Installing the Project

***Note,*** this installation method requires **mamba version 2.3.2 or above**. Currently, all
Sun lab automation pipelines require that mamba is installed through the
[miniforge3](https://github.com/conda-forge/miniforge) installer.

1. Download this repository to the local machine using the preferred method, such as git-cloning.
2. If the downloaded distribution is stored as a compressed archive, unpack it using the
   appropriate decompression tool.
3. `cd` to the root directory of the prepared project distribution.
4. Install the core Sun lab development dependencies into the ***base*** mamba environment via the
   `mamba install tox uv tox-uv` command.
5. Use the `tox -e create` command to create the project-specific development environment followed
   by `tox -e install` command to install the project into that environment as a library.

### Additional Dependencies

In addition to installing the project and all user dependencies, install the following
dependencies:

1. [Python](https://www.python.org/downloads/) distributions, one for each version supported by
   the developed project. Currently, this library supports the three latest stable versions. It is
   recommended to use a tool like [pyenv](https://github.com/pyenv/pyenv) to install and manage
   the required versions.
2. [Doxygen](https://www.doxygen.nl/manual/install.html), if you want to generate C++ code
   documentation.
3. An appropriate build tool or Docker, if you intend to build binary wheels via
   [cibuildwheel](https://cibuildwheel.pypa.io/en/stable/). See the link for information on which
   dependencies to install for each development platform.

### Development Automation

This project uses `tox` for development automation. The following tox environments are available:

| Environment          | Description                                                  |
|----------------------|--------------------------------------------------------------|
| `lint`               | Runs ruff formatting, ruff linting, and mypy type checking   |
| `stubs`              | Generates py.typed marker and .pyi stub files                |
| `{py312,...}-test`   | Runs the test suite via pytest for each supported Python     |
| `coverage`           | Aggregates test coverage into an HTML report                 |
| `docs`               | Builds the API documentation via Sphinx                      |
| `build`              | Builds sdist and wheel distributions                         |
| `upload`             | Uploads distributions to PyPI via twine                      |
| `install`            | Builds and installs the project into its mamba environment   |
| `uninstall`          | Uninstalls the project from its mamba environment            |
| `create`             | Creates the project's mamba development environment          |
| `remove`             | Removes the project's mamba development environment          |
| `provision`          | Recreates the mamba environment from scratch                 |
| `export`             | Exports the mamba environment as .yml and spec.txt files     |
| `import`             | Creates or updates the mamba environment from a .yml file    |

Run any environment using `tox -e ENVIRONMENT`. For example, `tox -e lint`.

***Note,*** all pull requests for this project have to successfully complete the `tox` task before
being merged. To expedite the task's runtime, use the `tox --parallel` command to run some tasks
in parallel.

### Automation Troubleshooting

Many packages used in `tox` automation pipelines (uv, mypy, ruff) and `tox` itself may experience
runtime failures. In most cases, this is related to their caching behavior. If an unintelligible
error is encountered with any of the automation components, deleting the corresponding cache
directories (`.tox`, `.ruff_cache`, `.mypy_cache`, etc.) manually or via a CLI command typically
resolves the issue.

___

## Versioning

This project uses [semantic versioning](https://semver.org/). See the
[tags on this repository](https://github.com/Sun-Lab-NBB/ataraxis-time/tags) for the available
project releases.

___

## Authors

- Ivan Kondratyev ([Inkaros](https://github.com/Inkaros))

___

## License

This project is licensed under the Apache 2.0 License: see the [LICENSE](LICENSE) file for
details.

___

## Acknowledgments

- All Sun lab [members](https://neuroai.github.io/sunlab/people) for providing the inspiration
  and comments during the development of this library.
- [elapsedMillis](https://github.com/pfeerick/elapsedMillis/blob/master/elapsedMillis.h) project
  for providing the inspiration for the API and the functionality of the timer class.
- [nanobind](https://github.com/wjakob/nanobind) project for providing a fast and convenient way
  of binding C++ code to Python projects.
- The creators of all other dependencies and projects listed in the
  [pyproject.toml](pyproject.toml) file.

