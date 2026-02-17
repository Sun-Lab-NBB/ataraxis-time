# Claude Code Instructions

## Session start behavior

You MUST invoke the `/explore-codebase` skill at the start of every session to build context before making any
changes. You MUST invoke the relevant style skill (`/python-style`, `/cpp-style`, etc.) before writing or modifying
any source code.

## Style guide compliance

You MUST follow the Sun Lab style conventions when working in this project. Invoke the appropriate skill before
making any changes to the corresponding file type:

| File type          | Required skill     |
|--------------------|--------------------|
| Python source code | `/python-style`    |
| C++ source code    | `/cpp-style`       |
| `pyproject.toml`   | `/pyproject-style` |
| `tox.ini`          | `/tox-config`      |
| `README.md`        | `/readme-style`    |
| Commit messages    | `/commit`          |

You MUST use `console.error(message=message, error=ErrorType)` from `ataraxis-base-utilities` for all error
handling in Python source files. Do not use bare `raise` statements. Error messages follow the format:
`"Unable to [action]. The [parameter] must be [constraint], but got {value}."`.

You MUST route cross-package imports through the package `__init__.py`. Within-package imports use direct module
imports. For example, `src/timers/` imports from `src/utilities/` via `from ..utilities import convert_time`, not
`from ..utilities.time_utilities import convert_time`.

## Cross-referenced library verification

This project depends on the following Sun Lab library:

| Library                 | Import name                | Role                                             |
|-------------------------|----------------------------|--------------------------------------------------|
| ataraxis-base-utilities | `ataraxis_base_utilities`  | Provides `console` for error handling and output |

The `console` object is not enabled in this library's top-level `__init__.py`. It is enabled explicitly in
`benchmark.py` before use. You MUST verify this pattern is preserved when adding new `console.echo()` calls.

## Available skills

| Skill               | Description                                                   |
|---------------------|---------------------------------------------------------------|
| `/explore-codebase` | Performs in-depth codebase exploration at session start       |
| `/python-style`     | Applies Sun Lab Python coding conventions                     |
| `/cpp-style`        | Applies Sun Lab C++ coding conventions                        |
| `/pyproject-style`  | Applies Sun Lab pyproject.toml conventions                    |
| `/tox-config`       | Applies Sun Lab tox.ini conventions                           |
| `/readme-style`     | Applies Sun Lab README.md conventions                         |
| `/commit`           | Drafts style-compliant commit messages from local changes     |
| `/skill-design`     | Generates and verifies skill files and CLAUDE.md instructions |

## Project context

### Architecture

This library is a hybrid Python + C++ extension that provides high-precision thread-safe timing functionality.
The C++ layer uses the `chrono` library to interface with the system's highest available precision clock, exposed
to Python through nanobind bindings.

The library is organized into three packages:

- **`c_extensions`**: C++ source compiled via CMake and scikit-build-core. The `CPrecisionTimer` class provides
  nanosecond-resolution elapsed timing and busywait/sleep delay methods with optional GIL release.
- **`timers`**: Python wrapper layer. `PrecisionTimer` wraps the C++ extension with a high-level API including
  lap tracking, polling, and human-readable time formatting. `Timeout` provides a timeout guard built on
  `PrecisionTimer`. The `benchmark` module exposes the `axt-benchmark` CLI command.
- **`utilities`**: Pure-Python functions for time unit conversion, timestamp formatting and parsing,
  rate/interval conversion, and `timedelta` interoperability.

### Build system

This is a C++ extension project. The build backend is scikit-build-core with nanobind. `CMakeLists.txt` at the
project root compiles `src/c_extensions/precision_timer_ext.cpp` into a platform-specific binary extension.
Binary wheels are built via cibuildwheel. The `# type: ignore[import-not-found]` comment on the C++ extension
import in `timer.py` is expected and should not be removed.

### Key patterns

- **Enumeration-driven precision**: Timer precision is controlled through `TimerPrecisions` (StrEnum) with values
  `"ns"`, `"us"`, `"ms"`, `"s"`. The string value is passed directly to the C++ layer.
- **Benchmark exclusion**: All definitions in `benchmark.py` carry `# pragma: no cover` because the module
  requires interactive CLI execution and cannot be unit tested.
- **File ordering**: Constants appear first, then enumerations, then public functions/classes, then private
  functions. This ordering is enforced by `/python-style`.
- **convert_time flexibility**: The `convert_time()` function accepts both `int` and `float` inputs and returns
  the same type by default (`as_float=False` returns `int`, `as_float=True` returns `float`).

### Development commands

```bash
tox -e lint        # Format, lint, and type-check
tox -e stubs       # Generate .pyi stub files
tox -e py312-test  # Run tests for Python 3.12
tox -e py313-test  # Run tests for Python 3.13
tox -e py314-test  # Run tests for Python 3.14
tox -e coverage    # Aggregate multi-version coverage reports
tox -e docs        # Build Sphinx + Doxygen documentation
tox                # Run full pipeline (uninstall -> export -> lint -> ... -> install)
```

### Testing

Tests use pytest with pytest-xdist for parallel execution (`-n logical --dist loadgroup`). Coverage is collected
per-Python-version and aggregated by the `coverage` tox environment. Test files mirror the source structure under
`tests/` with a `_test.py` suffix. The C++ extension must be installed (via `tox -e install` or
`pip install -e .`) before tests can run, since `CPrecisionTimer` is a compiled binary module.

### CLI entry point

| Command         | Entry point                                | Purpose                                       |
|-----------------|--------------------------------------------|-----------------------------------------------|
| `axt-benchmark` | `ataraxis_time.timers.benchmark:benchmark` | Benchmarks PrecisionTimer on the local system |

The benchmark uses Click for argument parsing and tqdm for progress display. It tests interval timing, busywait
delay, and sleep delay across all four precision modes.
