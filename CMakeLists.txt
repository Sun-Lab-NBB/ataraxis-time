cmake_minimum_required(VERSION 3.28)

project(ataraxis-time LANGUAGES CXX)  # Project name != Library name
set(LIBRARY_NAME ataraxis_time)       # What the user imports

# Prevents this instruction set from being executed from contexts other than scikit_build backend.
if (NOT SKBUILD)
  message(WARNING "\
  This CMake file is meant to be executed using 'scikit-build' backend. Running it directly will not produce the desired
  result. Users should use the following command to install the package into their desired environment:
  =====================================================================================================================
    $ python -m pip install .
  =====================================================================================================================
  Developers should use the 'dev' specification to install the development dependencies. Note, additional non-python
  dependencies, such as doxygen, may need to be installed manually. Consult the 'installation' section of the Readme.md
  of the repository for more information.
  ======================================================================================================================
   $ python -m pip install .'[dev]'
   or
   $ python -m pip install .[dev]
  ======================================================================================================================
  For your convenience, OS-specific copies of the environments used for development are also included for all source
  code distributions under /envs directory.
  ")
endif()

# Verifies that the target Python version supports Stable Application Binary Interface (SABI) and, if so, uses it for
# compilation.
set(SKBUILD_SABI_SUPPORTED ${Python_SABI_SUPPORTED})

# Imports the necessary nanobind components. Note, the Python version has to match the minimum python version supported
# by the library (declared via pyproject.toml).
find_package(Python 3.11
  REQUIRED COMPONENTS Interpreter Development.Module
  OPTIONAL_COMPONENTS Development.SABIModule)

# Detects the installed nanobind package and imports it into CMake. The nanobind package itself is installed before
# the build is executed due to being the building_backend requirement.
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
install(FILES src/py.typed DESTINATION ${LIBRARY_NAME})  # Includes py.typed
install(FILES src/__init__.py DESTINATION ${LIBRARY_NAME})  # Includes the main package init

install(TARGETS precision_timer_ext LIBRARY DESTINATION ${LIBRARY_NAME})  # C++ Extension binding (via nanobind).
install(DIRECTORY src/precision_timer DESTINATION ${LIBRARY_NAME})  # Pure Python package, uses C++ extension.
install(DIRECTORY src/time_helpers DESTINATION ${LIBRARY_NAME})  # Pure Python package, provides helper methods
