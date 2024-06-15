.. This file provides the instructions for how to display the API documentation generated using sphinx autodoc
   extension. Use it to declare Python and C++ extension documentation sub-directories via appropriate modules
   (autodoc, doxygenfile and ).

Python Timer API
================

.. automodule:: high_precision_timer.precision_timer.timer_class
   :members:
   :undoc-members:
   :show-inheritance:

Timer Benchmark
===============

.. automodule:: high_precision_timer.precision_timer.timer_benchmark
   :members:
   :undoc-members:
   :show-inheritance:

.. Since benchmark() function is a click-based function, it has to be documented using the click plugin, rather than
.. the automodule used for most other library methods. Nesting allows documenting click-options in-addition to the main
.. function docstring.
.. click:: high_precision_timer.precision_timer.timer_benchmark:benchmark
   :prog: benchmark_timer
   :nested: full

Standalone Python Functions
===========================

.. automodule:: high_precision_timer.precision_timer.utilities
   :members:
   :undoc-members:
   :show-inheritance:

C++ Timer Extension
===================

.. doxygenfile:: precision_timer_ext.cpp
   :project: high-precision-timer