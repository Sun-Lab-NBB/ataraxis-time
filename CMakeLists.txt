# Specifies the minimum and maximum CMake versions fro the project.
cmake_minimum_required(VERSION 3.15...3.28)

# Specifies project name and declares that it uses C++ language (for extensions)
project(high-precision-timer LANGUAGES CXX)

# Specifies the library name. This is the name of the package that will be available as an 'import' statement target
# after the project is installed into the target Python environment.
set(LIBRARY_NAME high_precision_timer)

# Prevents this instruction set from being executed from contexts other than scikit_build backend.
if (NOT SKBUILD)
  message(WARNING "\
  This CMake file is meant to be executed using 'scikit-build' backend. Running it directly will not produce the desired
  result. Users should use one of the commands below to install the package into their desired environment. Note, the
  'benchmark' version is preferred as it contains the optional dependencies needed for the benchmark_timer command to
  work.
  =====================================================================================================================
   $ python -m pip install .
   or
   $ python -m pip install .'[benchmark]'
  =====================================================================================================================
  Developers should use the 'dev' version to install the development dependencies. Note, additional non-python
  dependencies, such as doxygen, may need to be installed manually. Consult the Readme.md of the repository or the
  'installation' section of the documentation html page for more information.
  ======================================================================================================================
   $ python -m pip install .'[dev]'
  ======================================================================================================================
  For your convenience, OS-specific copies of the environments used for development are also included for all source
  code distributions under /envs directory.
  ")
endif()

# Checks whether the target Python version supports Stable Application Binary Interface (SABI) and uses the result to
# set the scikit SABI_SUPPORTED flag. SABI is a new feature introduced in python 3.12+ that allows reusing compiled
# extensions between major python versions. This way, binary files compiled for 3.12 will work for 3.13 and onward,
# eliminating the need to recompile the binaries seen in all prior versions.
set(SKBUILD_SABI_SUPPORTED ${Python_SABI_SUPPORTED})

# Attempts to import the component packages needed for nanobind to work. This is taken from nanobind example project and
# may change when future versions of nanobind become available. Note, the python version should match the minimum
# version declared in the pyproject.toml file.
find_package(Python 3.10
  REQUIRED COMPONENTS Interpreter Development.Module
  OPTIONAL_COMPONENTS Development.SABIModule)

# Detects the installed nanobind package and imports it into CMake. The nanobind package itself is installed before
# the build is executed due to being the building_backend requirement (see pyproject.toml).
execute_process(
  COMMAND "${Python_EXECUTABLE}" -m nanobind --cmake_dir
  OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE NB_DIR)
list(APPEND CMAKE_PREFIX_PATH "${NB_DIR}")
find_package(nanobind CONFIG REQUIRED)

# Binds the C++ extension to the python precision_timer_ext module. This exposes the C++ API to Python via nanobind
# module.
nanobind_add_module(
  precision_timer_ext
  STABLE_ABI
  NB_STATIC
  src/c_extensions/precision_timer_ext.cpp
)

# Specifies what to include in the library. Uses the global LIBRARY_NAME variable to add content to the same library.
# In this case, includes the extension binding and the pure-python module that further wraps the extension API into
# a python class.
install(TARGETS precision_timer_ext LIBRARY DESTINATION ${LIBRARY_NAME})  # C++ Extension binding (via nanobind).
install(DIRECTORY src/precision_timer DESTINATION ${LIBRARY_NAME})  # Pure Python package, uses C++ extension.
install(DIRECTORY src/time_helpers DESTINATION ${LIBRARY_NAME})  # Pure Python package, provides helper methods
install(FILES src/py.typed DESTINATION ${LIBRARY_NAME})  # Includes py.typed
install(FILES src/__init__.py DESTINATION ${LIBRARY_NAME})  # Includes the main package init
install(FILES src/utilities.py DESTINATION ${LIBRARY_NAME})  # Includes the shared utilities module