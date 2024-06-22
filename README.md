# ataraxis-time

A Python library that provides a sub-microsecond-precise thread-safe timer and methods to work with date and time data.

![PyPI - Version](https://img.shields.io/pypi/v/ataraxis-time)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ataraxis-time)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
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

The library can be used as a standalone module, but it is primarily designed to integrate with the broader 'Ataraxis'
science-automation project, providing date- and time-related functionality to other project modules.
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

**_Note. Building from source may require additional build-components to be available to compile the C++ portion of the
library. It is highly advised to use the option to install from PIP or CONDA instead._**

1. Download this repository to your local machine using your preferred method, such as git-cloning. Optionally, use one
   of the stable releases that include precompiled binary wheels in addition to source code.
2. ```cd``` to the root directory of the project using your CLI of choice.
3. Run ```python -m pip install .``` to install the project. Alternatively, if using a distribution with precompiled 
   binaries, use ```python -m pip install WHEEL_PATH```, replacing 'WHEEL_PATH' with the path to the wheel file.
4. Optionally, run the timer benchmark using ```benchmark_timer``` command from your CLI (no need to use 'python'
   directive). You can use ```benchmark_timer --help``` command to see the list of additional configuration
   parameters that can be used to customize the benchmark behavior.

### PIP

Use the following command to install the library using PIP:
```pip install ataraxis-time```

### Conda / Mamba

**_Note. Due to conda-forge contributing process being more nuanced than pip uploads, conda versions may lag behind
pip and source code distributions._**

Use the following command to install the library using Conda or Mamba:
```conda install ataraxis-time```
___

## Usage

This is a minimal example of how to use the precision timer class from this library:

```
# First, import the timer class.
from ataraxis_time import PrecisionTimer
import time as tm

# Then, instantiate the timer class using the desired precision. Supported precisions are: 'ns' (nanoseconds),
# 'us' (microseconds), 'ms' (milliseconds), and 's' seconds.
timer = PrecisionTimer('us')

# Interval timing example
timer.reset()  # Resets (re-bases) the timer
tm.sleep(1)  # Simulates work (for 1 second)
print(f'Work time: {timer.elapsed} us')  # This returns the 'work' duration using the precision units of the timer.

print()  # Separates interval example from delay examples

# Delay example:
for i in range(10):
    print(f'us delay iteration: {i}')
    timer.delay_block(500)  # Delays for 500 microseconds, does not release the GIL

print()  # Separates the us loop from ms loop

timer.set_precision('ms')  # Switches timer precision to milliseconds
for i in range(10):
    print(f'ms delay iteration: {i}')
    timer.delay_noblock(500)  # Delays for 500 milliseconds, releases the GIL
```

This is a minimal example of how to use helper-functions from this library:
```
# Import the desired function(s) from the time_helpers sub-package.
from ataraxis_time.time_helpers import convert_time, get_timestamp

# Time converter example. The function can convert single inputs and lists / numpy arrays.
initial_time = 12
time_in_seconds = convert_time(time=initial_time, from_units='d', to_units='s')  # Returns 1036800.0

# Obtains the current date and time and uses it to generate a timestamp that can be used in file-names (for example).
dt = get_timestamp(time_separator='-')  # Returns 2024-06-18-00-06-25 (yyyy-mm-dd-hh-mm-ss)
```
___

## API Documentation

See the [API documentation](https://ataraxis-time-api-docs.netlify.app/) for the
detailed description of the methods and classes exposed by components of this library. The documentation also covers the
C++ source code and any cli-interfaces (such as benchmark timer).
___

## Developers

This section provides installation, dependency, and build-system instructions for the developers that want to
modify the source code of this library. Additionally, it contains instructions for recreating the conda environments
that were used during development from the included .yml files.

### Installing the library

1. Download this repository to your local machine using your preferred method, such as git-cloning.
2. ```cd``` to the root directory of the project using your CLI of choice.
3. Install development dependencies. You have multiple options of satisfying this requirement:
   1. **_Preferred Method:_** Use conda or pip to install 
   [tox](https://tox.wiki/en/latest/config.html#provision_tox_env) or use an environment that has it installed and 
   call ```tox -e import-env``` to automatically import the os-specific development environment included with the 
   source code in your local conda distribution.
   2. Run ```python -m pip install .'[dev]'``` command to install development dependencies and the library. For some
   systems, you may need to use a slightly modified version of this command: ```python -m pip install .[dev]```.
   3. As long as you have an environment with [tox](https://tox.wiki/en/latest/config.html#provision_tox_env) installed
   and do not intend to run any code outside the predefined project automation pipelines, tox will automatically 
   install all required dependencies for each task. Generally, this option is **_not_** recommended.

**Note:** When using tox automation, having a local version of the library may interfere with tox methods that attempt
to build the library using an isolated environment. It is advised to remove the library from your test environment, or
disconnect from the environment, prior to running any tox tasks. This problem is rarely observed with the latest version
of the automation pipeline, but is worth mentioning.

### Additional Dependencies

In addition to installing the required python packages, separately install the following dependencies:

- [Doxygen](https://www.doxygen.nl/manual/install.html), if you want to generate C++ code documentation.
- An appropriate build tool or Docker, if you intend to build binary wheels via
  [cibuildwheel](https://cibuildwheel.pypa.io/en/stable/) (See the link for information on which dependencies to
  install).
- [Python](https://www.python.org/downloads/) distributions, one for each version that you intend to support. Currently,
  this library supports 3.10, 3.11 and 3.12. The easiest way to get tox to work as intended is to have separate
  python distributions, but using [pyenv](https://github.com/pyenv/pyenv) is a good alternative too. This is needed for 
  the 'test' task to work as intended

### Development Automation

To help developers, this project comes with a set of fully configured 'tox'-based pipelines for verifying and building
the project. Each of the tox commands builds the project in an isolated environment before carrying out its task. Some 
commands rely on the 'automation.py' module that provides the helper-scripts implemented in python. This module 
is stored in the source code root directory for each Sun Lab project.

- ```tox -e stubs``` Builds the library and uses mypy-stubgen to generate the stubs for the library wheel and move them 
to the appropriate position in the '/src' directory. This enables mypy and other type-checkers to work with this 
library.
- ```tox -e lint``` Checks and, where safe, fixes code formatting, style, and type-hinting.
- ```tox -e {py310, py311, py312}-test``` Builds the library and executes the tests stored in the /tests directory 
using pytest-coverage module.
- ```tox -e combine-test-reports``` Combines coverage reports from all test commands (for each python version) and 
compiles them into an interactive .html file stored inside '/reports' directory.
- ```tox -e doxygen``` Uses externally installed Doxygen distribution to generate documentation from docstrings of
  the C++ source code files.
- ```tox -e docs``` Uses Sphinx to generate API documentation from Python Google-style docstrings. If Doxygen-generated
  .xml files for the C++ extension are available, uses Breathe plugin to convert them to Sphinx-compatible format and
  add them to the final API .html file.
- ```tox``` Sequentially carries out the commands above (in the same order). Use ```tox --parallel``` to parallelize 
command execution (may not work on all platforms).

The commands above are considered 'checkout' commands and generally required to pass before every code push. The 
commands below are not intended to be used as-frequently and, therefore, are not part of the 'generic' tox-flow.

- ```tox -e build``` Builds the sdist and binary wheels for the library for all architectures supported by the host 
machine and saves them to the '/dist' directory.
- ```tox -e upload``` Uploads the sdist and wheels to PIP using twine, if they have not yet been uploaded. Optionally 
use ```tox -e upload -- --replace-token true``` to replace the token stored in .pypirc file.
- ```tox -e recipe``` Uses Grayskull to generate the conda-forge recipe from the latest available PIP-distribution. 
Assumes sdist is included with binary wheels when they are uploaded to PIP.
- ```tox -e export-env``` Exports the os-specific local conda development environment as a .yml and spec.txt file to the
'/envs' directory. This automatically uses the project-specific base-environment-name.
- ```tox -e import-env``` Imports and os-specific conda development environment from the .yml file stored in the '/envs'
directory.
- ```tox -e rename-envs``` Replaces the base-name for all environment files inside the '/envs' directory. Remember to 
also change the base-name argument of the export-env command.

### Environments

All environments used during development are exported as .yml files and as spec.txt files to the [envs](envs) folder. 
The environment snapshots were taken on each of the three supported OS families: Windows 11, OSx 14.5 and 
Ubuntu Cinnamon 24.04 LTS.

To install the development environment for your OS:

1. Download this repository to your local machine using your preferred method, such as git-cloning.
2. ```cd``` into the [envs](envs) folder.
3. Use one of the installation methods below:
   1. **_Preferred Method_**: Install [tox](https://tox.wiki/en/latest/config.html#provision_tox_env) or use another 
   environment with already installed tox and call ```tox -e import-env```.
   2. Alternative Method: Run ```conda env create -f ENVNAME.yml``` or ```mamba env create -f ENVNAME.yml```. 
   Replace 'ENVNAME.yml' with the name of the environment you want to install (axt_dev_osx for OSx, axt_dev_win64 for 
   Windows and axt_dev_lin64 for Linux).

**Note:** the OSx environment was built against M1 (Apple Silicon) platform and may not work on Intel-based Apple 
devices.

___

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
