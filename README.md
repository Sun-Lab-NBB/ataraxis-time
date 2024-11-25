# ataraxis-time

A Python library that provides a sub-microsecond-precise thread-safe timer and helper methods to work with date and 
time data.

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
particular system configuration and utilization, most modern CPUs should be capable of sub-microsecond precision using
this timer. Due to using a C-extension to provide interval and delay timing functionality, the library is thread- and
process-safe and releases the GIL when using the appropriate delay command. Additionally, the library offers a set of 
standalone helper functions that can be used to manipulate date and time data.

While the library was written to integrate with other Sun Lab projects, it can be used as a standalone library for 
non-lab projects with no additional modification.
___

## Features

- Supports Windows, Linux, and OSx.
- Sub-microsecond precision on modern CPUs (~ 3 GHz+) during delay and interval timing.
- Releases GIL during (non-blocking) delay timing even when using microsecond and nanosecond precision.
- Pure-python API.
- Fast C++ core with direct extension API access via nanobind.
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

For users, all library dependencies are installed automatically for all supported installation methods 
(see [Installation](#installation) section). For developers, see the [Developers](#developers) section for 
information on installing additional development dependencies.
___

## Installation

### Source

**_Note. Building from source may require additional build components to be available to compile the C++ portion of the
library. It is highly recommended to install from PIP or CONDA instead._**

1. Download this repository to your local machine using your preferred method, such as git-cloning. Optionally, use one
   of the stable releases that include precompiled binary wheels in addition to source code.
2. ```cd``` to the root directory of the project using your command line interface of choice.
3. Run ```python -m pip install .``` to install the project. Alternatively, if using a distribution with precompiled 
   binaries, use ```python -m pip install WHEEL_PATH```, replacing 'WHEEL_PATH' with the path to the wheel file.
4. Optionally, run the timer benchmark using ```benchmark-timer``` command from your command line interface 
   (no need to use 'python' directive). You can use ```benchmark-timer --help``` command to see the list of additional 
   configuration parameters that can be used to customize the benchmark behavior.

### PIP

Use the following command to install the library using PIP: ```pip install ataraxis-time```
___

## Usage

### Precision Timer
The timer API is intentionally minimalistic to simplify class adoption and usage. It is heavily inspired by the
[elapsedMillis](https://github.com/pfeerick/elapsedMillis/blob/master/elapsedMillis.h) library for 
Teensy and Arduino microcontrollers.

All timer class functionality is realized through a fast c-extension wrapped into the PrecisionTimer class. Primarily,
the functionality comes through 3 class methods: reset(), elapsed (property) and delay():

#### Initialization and Configuration
The timer takes the 'precision' to use as the only initialization argument. All instances of the timer class are 
thread- and process-safe and do not interfere with each other. The precision of the timer can be adjusted after 
initialization if needed, which is more efficient than re-initializing the timer.

```
from ataraxis_time import PrecisionTimer

# Currently, the timer supports 4 'precisions: 'ns' (nanoseconds), 'us' (microseconds), 'ms' (milliseconds), and 
# 's' seconds.'
timer = PrecisionTimer('us')

# However, the precision can be adjusted after initialization if needed:
timer.set_precision('ms')  # Switches timer precision to milliseconds
```

#### Interval Timing
Interval timing functionality is realized through two methods: reset() and elapsed. This functionality of the class
is identical to using perf_counter_ns() from 'time' library. The main difference from the 'time' library is that the 
class uses a slightly different interface (reset / elapsed) and automatically converts the output to the desired 
precision.
```
from ataraxis_time import PrecisionTimer
import time as tm

timer = PrecisionTimer('us')

# Interval timing example
timer.reset()  # Resets (re-bases) the timer
tm.sleep(1)  # Simulates work (for 1 second)
print(f'Work time: {timer.elapsed} us')  # This returns the 'work' duration using the precision units of the timer.
```

#### Delay
Delay timing functionality is the primary advantage of this class over the standard 'time' library. At the time of 
writing, the 'time' library can provide nanosecond-precise delays via a 'busywait' perf_counter_ns() loop that does not
release the GIL. Alternatively, it can release the GIL via sleep() method, that is, however, only accurate up to 
millisecond precision (up to 16ms on some Windows platforms). PrecisionTimer class can delay for time-periods up to 
nanosecond precision (on some systems) while releasing or holding the GIL (depends on the method used):
```
from ataraxis_time import PrecisionTimer
import time as tm

timer = PrecisionTimer('us')

# GIL-releasing microsecond delays.
for i in range(10):
    print(f'us delay iteration: {i}')
    timer.delay_block(500)  # Delays for 500 microseconds, does not release the GIL

# Non-GIL-releasing milliseconds delay (uses sleep for millisecond delays to optimize resource usage).
timer.set_precision('ms')  # Switches timer precision to milliseconds
for i in range(10):
    print(f'ms delay iteration: {i}')
    timer.delay_noblock(500)  # Delays for 500 milliseconds, releases the GIL
```

### Date & Time Helper Functions
These are minor helper methods that are not directly part of the timer class showcased above. Since these methods are
not intended for realtime applications, they are implemented using pure python (slow), rather than fast 
c-extension method.

#### Convert Time
This helper method performs time-conversions, rounding to 3 Significant Figures for the chosen precision, and works 
with time-scales from nanoseconds to days.
```
from ataraxis_time.time_helpers import convert_time

# The method can convert single inputs...
initial_time = 12
time_in_seconds = convert_time(time=initial_time, from_units='d', to_units='s')  # Returns 1036800.0

# And Python iterables and numpy arrays
initial_time = np.array([12, 12, 12])
# Returns a numpy aray with all values set to 1036800.0 (uses float_64 format)
time_in_seconds = convert_time(time=initial_time, from_units='d', to_units='s')
```

#### Timestamps
Timestamp methods are used to get timestamps accurate up to microseconds. They work by connecting to one of the global
time-servers and obtaining the current timestamp for the UTC timezone. The method can be used to return the timestamp 
as string (good for naming files) or bytes array (good for serialized communication and logging).
```
from ataraxis_time.time_helpers import get_timestamp, extract_timestamp_from_bytes

# Obtains the current date and time and uses it to generate a timestamp that can be used in file-names (for example).
# The timestamp is precise up to microseconds.
dt = get_timestamp(time_separator='-')  # Returns 2024-06-18-00-06-25-927794 (yyyy-mm-dd-hh-mm-ss-us)

# Also, the method supports giving the timestamp as a serialized array of bytes. This is helpful when it is used as
# part of a serialized communication protocol. For example, this is the format expected by our DataLogger class,
# available from ataraxis-data-structures library.
bytes_dt = get_timestamp(as_bytes=True)  # Returns an 8-byte numpy array.

# To decode the byte-serialized timestamp into a string, use the extract_timestamp_from_bytes() method
dt_2 = extract_timestamp_from_bytes(bytes_dt)  # Returns 2024-06-18-00-06-25-927794 (yyyy-mm-dd-hh-mm-ss-us)
```
___

## API Documentation

See the [API documentation](https://ataraxis-time-api-docs.netlify.app/) for the
detailed description of the methods and classes exposed by components of this library. 
The documentation also covers the C++ source code and benchmark-timer command line interface command.
___

## Developers

This section provides installation, dependency, and build-system instructions for the developers that want to
modify the source code of this library. Additionally, it contains instructions for recreating the conda environments
that were used during development from the included .yml files.

### Installing the library

1. Download this repository to your local machine using your preferred method, such as git-cloning.
2. ```cd``` to the root directory of the project using your command line interface of choice.
3. Install development dependencies. You have multiple options of satisfying this requirement:
   1. **_Preferred Method:_** Use conda or pip to install
      [tox](https://tox.wiki/en/latest/user_guide.html) or use an environment that has it installed and
      call ```tox -e import``` to automatically import the os-specific development environment included with the
      source code in your local conda distribution. Alternatively, you can use ```tox -e create``` to create the 
      environment from scratch and automatically install the necessary dependencies using pyproject.toml file. See 
      [environments](#environments) section for other environment installation methods.
   2. Run ```python -m pip install .'[dev]'``` command to install development dependencies and the library. For some
      systems, you may need to use a slightly modified version of this command: ```python -m pip install .[dev]```.
   3. As long as you have an environment with 
      [tox](https://tox.wiki/en/latest/user_guide.html) installed
      and do not intend to run any code outside the predefined project automation pipelines, 
      tox will automatically install all required dependencies for each task.

### Additional Dependencies

In addition to installing the required python packages, separately install the following dependencies:

1. [Doxygen](https://www.doxygen.nl/manual/install.html), if you want to generate C++ code documentation.
2. An appropriate build tool or Docker, if you intend to build binary wheels via
   [cibuildwheel](https://cibuildwheel.pypa.io/en/stable/) (See the link for information on which dependencies to
   install).
3. [Python](https://www.python.org/downloads/) distributions, one for each version that you intend to support. 
   Currently, this library supports 3.10, 3.11, and 3.12. The easiest way to get tox to work as intended is to have 
   separate python distributions, but using [pyenv](https://github.com/pyenv/pyenv) is a good alternative too. 
   This is needed for the 'test' task to work as intended.

### Development Automation

This project comes with a fully configured set of automation pipelines implemented using 
[tox](https://tox.wiki/en/latest/user_guide.html). Check [tox.ini file](tox.ini) for details about 
available pipelines and their implementation. Alternatively, call ```tox list``` from the root directory of the project
to see the list of available tasks.

**Note!** All commits to this project have to successfully complete the ```tox``` task before being pushed to GitHub. 
To minimize the runtime task for this task, use ```tox --parallel```.

For more information, you can also see the 'Usage' section of the 
[ataraxis-automation project](https://github.com/Sun-Lab-NBB/ataraxis-automation) documentation.

### Environments

All environments used during development are exported as .yml files and as spec.txt files to the [envs](envs) folder.
The environment snapshots were taken on each of the three explicitly supported OS families: Windows 11, OSx (M1) 15.1.1
and Linux Ubuntu 24.04 LTS.

**Note!** Since the OSx environment was built against an M1 (Apple Silicon) platform and may not work on Intel-based 
Apple devices.

To install the development environment for your OS:

1. Download this repository to your local machine using your preferred method, such as git-cloning.
2. ```cd``` into the [envs](envs) folder.
3. Use one of the installation methods below:
   1. **_Preferred Method_**: Install [tox](https://tox.wiki/en/latest/user_guide.html) or use another 
      environment with already installed tox and call ```tox -e import```.
   2. **_Alternative Method_**: Run ```conda env create -f ENVNAME.yml``` or ```mamba env create -f ENVNAME.yml```. 
      Replace 'ENVNAME.yml' with the name of the environment you want to install (axt_dev_osx for OSx, axt_dev_win 
      for Windows, and axt_dev_lin for Linux).

**Hint:** while only the platforms mentioned above were explicitly evaluated, this project is likely to work on any 
common OS, but may require additional configurations steps.

Since the release of [ataraxis-automation](https://github.com/Sun-Lab-NBB/ataraxis-automation) version 2.0.0 you can 
also create the development environment from scratch via pyproject.toml dependencies. To do this, use 
```tox -e create``` from project root directory.

### Automation Troubleshooting

Many packages used in 'tox' automation pipelines (uv, mypy, ruff) and 'tox' itself are prone to various failures. In 
most cases, this is related to their caching behavior. Despite a considerable effort to disable caching behavior known 
to be problematic, in some cases it cannot or should not be eliminated. If you run into an unintelligible error with 
any of the automation components, deleting the corresponding .cache (.tox, .ruff_cache, .mypy_cache, etc.) manually 
or via a cli command is very likely to fix the issue.
___

## Versioning

We use [semantic versioning](https://semver.org/) for this project. For the versions available, see the 
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
- My [NBB](https://nbb.cornell.edu/) Cohort for answering 'random questions' pertaining to the desired library
  functionality.
- [click](https://github.com/pallets/click/) project for providing the low-level command-line-interface functionality 
  for this project.
- [tqdm](https://github.com/tqdm/tqdm) project for providing an easy-to-use progress bar functionality used in our
  benchmark script.
- [numpy](https://github.com/numpy/numpy) project for providing low-level functionality for our benchmark script.
- [elapsedMillis](https://github.com/pfeerick/elapsedMillis/blob/master/elapsedMillis.h) project for providing the 
  inspiration for the API and the functionality of the timer class.
- [nanobind](https://github.com/wjakob/nanobind) project for providing a fast and convenient way of binding c++ code to
  python projects.
- The creators of all other projects used in our development automation pipelines [see pyproject.toml](pyproject.toml).
