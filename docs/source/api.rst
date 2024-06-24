.. This file provides the instructions for how to display the API documentation generated using sphinx autodoc
   extension. Use it to declare Python and C++ extension documentation sub-directories via appropriate modules
   (automodule, doxygenfile and sphinx-click).

Precision Timer API
===================

.. automodule:: ataraxis_time.precision_timer.timer_class
   :members:
   :undoc-members:
   :show-inheritance:

Timer Benchmark
===============

.. automodule:: ataraxis_time.precision_timer.timer_benchmark
   :members:
   :undoc-members:
   :show-inheritance:

.. click:: ataraxis_time.precision_timer.timer_benchmark:benchmark
   :prog: benchmark-timer
   :nested: full

Helper Functions
================

.. automodule:: ataraxis_time.time_helpers.helper_functions
   :members:
   :undoc-members:
   :show-inheritance:

C++ Timer Extension
===================

.. doxygenfile:: precision_timer_ext.cpp
   :project: ataraxis-time
