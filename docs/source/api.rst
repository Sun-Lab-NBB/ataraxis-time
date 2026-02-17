.. This file provides the instructions for how to display the API documentation generated using sphinx autodoc
   extension. Use it to declare Python and C++ extension documentation sub-directories via appropriate modules
   (automodule, doxygenfile and sphinx-click).

Timers
======

.. automodule:: ataraxis_time.timers
   :members:
   :undoc-members:
   :show-inheritance:

Timer Benchmark
===============

.. click:: ataraxis_time.timers.benchmark:benchmark
   :prog: axt-benchmark
   :nested: full

Utilities
=========

.. automodule:: ataraxis_time.utilities
   :members:
   :undoc-members:
   :show-inheritance:

C++ Timer Extension
===================

.. doxygenfile:: precision_timer_ext.cpp
   :project: ataraxis-time
