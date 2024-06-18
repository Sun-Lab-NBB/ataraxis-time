# AtaraxisTime

A Python library that provides a sub-microsecond-precise thread-safe timer and methods to work with date and time data.

![PyPI - Version](https://img.shields.io/pypi/v/high-precision-timer)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/high-precision-timer)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
![type-checked: mypy](https://img.shields.io/badge/type--checked-mypy-blue?style=flat-square&logo=python)
![PyPI - License](https://img.shields.io/pypi/l/high-precision-timer)
![PyPI - Status](https://img.shields.io/pypi/status/high-precision-timer)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/high-precision-timer)
___

## Detailed Description

This library uses the 'chrono' C++ library to access the fastest available system clock and use it to provide interval
timing and delay functionality via a Python binding API. While the performance of the timer heavily depends on the
particular system configuration and utilization, most modern CPU should be capable of sub-microsecond precision using
this timer. Due to using a C-extension to provide interval and delay timing functionality, the library is thread- and
process-safe.

Additionally, the library offers a set of standalone utility functions that provide further date and time 
related services, such as time conversion and timestamp generation.
___

## Features

- Supports Windows, Linux, and OSx.
- Sub-microsecond precision on modern CPUs (~ 3 GHz+).
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

For users, all library dependencies are installed automatically when using the appropriate installation specification
for all supported installation methods (see [Installation](#Installation) section). For developers, see the
[Developers](#Developers) section for information on installing additional development dependencies.
___

## Installation

### Source

**_Note. Building from source may require additional build-components to be available to compile the C++ portion of the
library. It is highly advised to use the option to install from PIP or CONDA instead._**

1. Download this repository to your local machine using your preferred method, such as git-cloning. Optionally, use one
   of the stable releases that include precompiled binary wheels in addition to source code.
2. ```cd``` to the root directory of the project using your CLI of choice.
3. Run ```python -m pip install .``` to install the project.
4. Optionally, run the timer benchmark using ```benchmark_timer``` command from your CLI (no need to use 'python'
   directive). You can use the ```benchmark_timer --help``` command to see the list of additional configuration
   parameters that can be used to customize the benchmark.

### PIP

Use the following command to install the library using PIP:
```pip install high-precision-timer```

### Conda / Mamba

Use the following command to install the library using Conda or Mamba:
```conda install high-precision-timer```
___

## Usage

This is a minimal example of how to use this library:

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

___

## API Documentation

See the [API documentation](https://high-precision-timer-docs.netlify.app/) for the
detailed description of the methods and their arguments, exposed through the PrecisionTimer python class or the direct
CPrecisionTimer binding class. The documentation also describes the benchmark method and the compatible CLI arguments
used to control benchmark behavior and the standalone utility functions.
___

## Developers

This section provides additional installation, dependency, and build-system instructions for the developers that want to
modify the source code of this library. Additionally, it contains instructions for recreating the conda environments
that were used during development from the included .yml files.

### Installing the library

1. Download this repository to your local machine using your preferred method, such as git-cloning.
2. ```cd``` to the root directory of the project using your CLI of choice.
3. Run ```python -m pip install .'[dev]'``` command to install development dependencies and the library. For some
   systems, you may need to use a slightly modified version of this command: ```python -m pip install .[dev]```.
   Alternatively, see the [environments](#environments) section for details on how to create a development environment
   with all necessary dependencies, using a .yml or requirements.txt file.

**Note:** When using tox automation, having a local version of the library may interfere with tox methods that attempt
to build a library using an isolated environment. It is advised to remove the library from your test environment, or
disconnect from the environment, prior to running any tox tasks.

### Additional Dependencies

In addition to installing the python packages, separately install the following dependencies:

- [Doxygen](https://www.doxygen.nl/manual/install.html), if you want to generate C++ code documentation.
- An appropriate build tools or Docker, if you intend to build binary wheels via
  [cibuildwheel](https://cibuildwheel.pypa.io/en/stable/) (See the link for information on which dependencies to
  install).
- [Python](https://www.python.org/downloads/) distributions, one for each version that you intend to support. Currently,
  this library supports 3.10, 3.11 and 3.12. The easiest way to get tox to work as intended is to have separate
  python distributions, but using [pyenv](https://github.com/pyenv/pyenv) is a good alternative too.

### Development Automation

To help developers, this project comes with a set of fully configured 'tox'-based pipelines for verifying and building
the project. Each of the tox commands builds the project in an isolated environment before carrying out its task.

Below is a list of all available commands and their purpose:

- ```tox -e lint``` Checks and, where safe, fixes code formatting, style, and type-hinting.
- ```tox -e test``` Builds the projects and executes the tests stored in the /tests directory using pytest-coverage
  module.
- ```tox -e doxygen``` Uses the externally installed Doxygen distribution to generate documentation from docstrings of
  the C++ extension file.
- ```tox -e docs``` Uses Sphinx to generate API documentation from Python Google-style docstrings. If Doxygen-generated
  .xml files for the C++ extension are available, uses Breathe plugin to convert them to Sphinx-compatible format and
  add
  them to the final API .html file.
- ```tox --parallel``` Carries out all commands listed above in-parallel (where possible). Remove the '--parallel'
  argument to run the commands sequentially. Note, this command will build and test the library for all supported python
  versions.
- ```tox -e build``` Builds the binary wheels for the library for all architectures supported by the host machine.

### Environments

In addition to tox-based automation, all environments used during development are exported as .yml
files and as spec.txt files to the [envs](envs) folder. The environment snapshots were taken on each of the three
supported OS families: Windows 11, OSx 14.5 and Ubuntu Cinnamon 24.04 LTS.

To install the development environment for your OS:

1. Download this repository to your local machine using your preferred method, such as git-cloning.
2. ```cd``` into the [envs](envs) folder.
3. Run ```conda env create -f ENVNAME.yml``` or ```mamba env create -f ENVNAME.yml```. Replace 'ENVNAME.yml' with the
   name of the environment you want to install (hpt_dev_osx for OSx, hpt_dev_win64 for Windows and hpt_dev_lin64 for
   Linux). Note, the OSx environment was built against M1 (Apple Silicon) platform and may not work on Intel-based Apple
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
