/**
 * @file precision_timer_ext.cpp
 * @brief The C++ extension module that defines and implements the CPrecisionTimer class.
 *
 * @section description Description:
 * This module instantiates the CPrecisionTimer class using the fastest system clock available through the 'chrono'
 * library, which allows the timer to resolve sub-microsecond timer-intervals on sufficiently fast CPUs. The use of the
 * 'chrono' library offers multiplatform support, so this module works on Windows, OSX and Linux.
 *
 * @note This module is bound to python using (<a href="https://github.com/wjakob/nanobind">nanobind</a>) project and is
 * designed to be further wrapped with a pure-python PrecisionTimer wrapper instantiated by the __init__.py of the
 * python module. The binding code is stored in the same file as source code (at the end of this file).
 *
 * @section dependencies Dependencies:
 * - nanobind/nanobind.h: For nanobind-based binding to Python.
 * - nanobind/stl/string.h: To enable working with python string arguments.
 * - chrono: To work with system-exposed time sources.
 * - thread: To control GIL-locking behavior of noblock methods.
 */

// Dependencies:
#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <chrono>
#include <thread>

// Simplifies interacting with the nanobind namespace by shortening it as nb.
namespace nb = nanobind;

/// Provides the ability to work with Python literal string-options.
using namespace nb::literals;

/// Provides the binding for various clock-related operations.
using namespace std::chrono;

/**
 * @class CPrecisionTimer
 * @brief Provides methods for sub-microsecond-precise interval timing and blocking and non-blocking code execution
 * delays.
 *
 * @note The performance of this class scales with the OS and the state of the host system. 'Chrono' library provides a
 * high_resolution_clock, which is automatically set to the highest resolution clock of the host OS (in Python, a very
 * similar approach is used by the perf_counter_ns() function from 'time' standard library). Additionally, all method
 * calls have a certain overhead associated with them (especially the sleep_for() method that has to wait for the
 * scheduler for at least 1 ms on the tested system). The busier the system is, the longer the overhead. Therefore, it
 is highly advisable to benchmark the timer if your application has very tight timing constraints and / or experiences
 resource limitations.
 */
class CPrecisionTimer
{
  public:
    /**
     * @brief Instantiates the CPrecisionTimer class using the requested precision.
     *
     * @param precision The precision of the timer. This controls the units used by the timer for all inputs and
     * outputs, which simplifies class usage as all time conversions are done automatically. Supported values
     * are: 'ns' (nanoseconds), 'us' (microseconds), 'ms' (milliseconds), and 's' (seconds). Defaults to 'us'.
     */
    explicit CPrecisionTimer(const std::string& precision = "us")
    {
        SetPrecision(precision);
    }

    /**
     * @brief Destroys the CPrecisionTimer class.
     *
     * Currently an explicit destructor is not strictly required, but it is still defined with potential future-use in
     * mind.
     */
    ~CPrecisionTimer()
    {}

    /**
     * @brief Resets the timer by replacing the timer reference with the time-value at the time of this method call.
     *
     * Call this method before executing the code which you want to time. When elapsed() method is used, it returns the
     * elapsed time relative to the last reset() method call or class instantiation (whichever happened last).
     */
    void Reset()
    {
        // Re-bases the start_time to use the current time obtained using the highest resolution clock.
        _start_time = high_resolution_clock::now();
    }

    /**
     * @brief Obtains the current value of the monotonic clock and uses it to calculate how much time (using
     * precision-units) has elapsed since the last reset() method call or class instantiation.
     *
     * @note Unless the class reference point is re-established using reset() method, the class will use the same
     * reference time for all elapsed() method calls. The time has no inherent meaning other than relative to the
     * reference point.
     *
     * @returns int64_t The elapsed time in the requested precision.
     */
    int64_t Elapsed()
    {
        auto stop_time = high_resolution_clock::now();
        auto elapsed   = duration_cast<nanoseconds>(stop_time - _start_time);
        return ConvertToPrecision(elapsed.count());
    }

    /**
     * @brief Releases GIL and blocks (delays) in-place for the specified number of time-units (depends on used
     * precision).
     *
     * This method is used to execute arbitrary delays while releasing GIL to enable other threads to run while
     * blocking. By default, this method uses a busy-wait approach where the thread constantly checks elapsed time
     * until the exit condition is encountered. Optionally, the method can be allowed to use sleep_for() for durations
     * above 1 millisecond (sleep_for only has ms precision), which will release the CPU.
     *
     * @warning If sleeping is allowed, there is an overhead of up to 1 ms due to scheduling on Windows. Unix schedulers
     * so far seem considerably better, but may still experience overheads.
     *
     * @note While the timer supports sub-microsecond precision, the minimum precision on the tested system was ~200 ns
     * and that incurred a static overhead of ~100 ns to setup and tear-down the timer. It is likely that the overhead
     * and precision will be worse for most other systems.
     *
     * @param duration The time to block for. Uses the same units as the precision parameter.
     * @param allow_sleep A boolean flag that determines whether the method should use sleep for delay durations above 1
     * millisecond. Sleep may be beneficial in some cases as it reduces the CPU load at the expense of a significantly
     * larger overhead compared to default busy-wait approach.
     */
    void DelayNoblock(int64_t duration, bool allow_sleep = false) const
    {
        nb::gil_scoped_release release; // Releases GIL to allow other threads to run while blocking.

        // Converts input delay duration to nanoseconds.
        auto delay_duration = duration * _precision_duration;

        // If sleep is allowed and delay duration is sufficiently long to resolve with sleep, uses sleep_for() to
        // release the CPU during blocking.
        if (allow_sleep && _precision_duration >= milliseconds(1))
        {
            std::this_thread::sleep_for(delay_duration);
        }

        // If sleep is not allowed or the requested delay is too short, uses a busy-wait delay approach which uses CPU
        // to improve delay precision.
        else
        {
            auto start = high_resolution_clock::now();
            while (duration_cast<nanoseconds>(high_resolution_clock::now() - start) < delay_duration)
                ;
        }
    }

    /**
     * @brief Similar to DelayNoblock() method, but this method does NOT release the GIL, preventing other threads from
     * running, as it blocks (delays) in-place for the specified number of time-units (depends on used precision).
     *
     * This method is used to execute arbitrary delays while maintaining GIL to prevent other threads from running.
     * By default, this method uses a busy-wait approach where the thread constantly checks elapsed time
     * until the exit condition is encountered. Optionally, the method can be allowed to use sleep_for() for durations
     * above 1 millisecond (sleep_for only has ms precision), which will release the CPU.
     *
     * @warning If sleeping is allowed, there is an overhead of up to 1 ms due to scheduling on Windows. Unix schedulers
     * so far seem considerably better, but may still experience overheads.
     *
     * @note While the timer supports sub-microsecond precision, the minimum precision on the tested system was ~200 ns
     * and that incurred a static overhead of ~100 ns to setup and tear-down he timer. It is likely that the overhead
     * and precision will be worse for most other systems.
     *
     * @param duration The time to block for. Uses the same units as the precision parameter.
     * @param allow_sleep A boolean flag that determines whether the method should use sleep for delay durations above 1
     * millisecond. Sleep may be beneficial in some cases as it reduces the CPU load at the expense of a significantly
     * larger overhead compared to default busy-wait approach.
     */
    void DelayBlock(int64_t duration, bool allow_sleep = false) const
    {
        // Note, no GIL release. This method can be used to halt multithreaded execution.

        // Determines the delay_duration using the class precision and the requested duration.
        auto delay_duration = duration * _precision_duration;

        // If allowed and the requested delay is sufficiently long to resolve with sleep, uses sleep_for() to
        // release the CPU during blocking.
        if (allow_sleep && _precision_duration >= milliseconds(1))
        {
            std::this_thread::sleep_for(delay_duration);
        }

        // Otherwise, uses a busy-wait delay approach which uses CPU to improve delay precision.
        else
        {
            auto start = high_resolution_clock::now();
            while (duration_cast<nanoseconds>(high_resolution_clock::now() - start) < delay_duration)
                ;
        }
    }

    /**
     * @brief Changes the precision of the timer class to the requested units.
     *
     * This method can be used to dynamically change the precision of the class without re-instantiating the class
     * during runtime, improving overall runtime speeds.
     *
     * @param precision The new precision to set the timer to. Supported values are: 'ns' (nanoseconds),
     * 'us' (microseconds), ms' (milliseconds), and 's' (seconds).'
     */
    void SetPrecision(const std::string& precision)
    {
        _precision = precision;
        switch (precision[0])
        {
            case 'n': _precision_duration = nanoseconds(1); break;
            case 'u': _precision_duration = microseconds(1); break;
            case 'm': _precision_duration = milliseconds(1); break;
            case 's': _precision_duration = seconds(1); break;
            default: throw std::invalid_argument("Unsupported precision. Use 'ns', 'us', 'ms', or 's'.");
        }
    }

    /**
     * @brief Returns the current precision (time-units) of the timer.
     *
     * @returns std::string The current precision of the timer ('ns', 'us', 'ms', or 's').
     */
    std::string GetPrecision() const
    {
        return _precision;
    }

  private:
    /// Stores the reference value used to calculate elapsed time.
    std::chrono::high_resolution_clock::time_point _start_time;

    /// Stores the string-option that describes the units used for inputs and outputs.
    std::string _precision;

    /// Stores the conversion factor that is assigned based on the chosen _precision option. It is used to convert the
    /// input duration values (for delay methods) to nanoseconds and the output duration values from nanoseconds to the
    /// chosen precision units.
    nanoseconds _precision_duration;

    /**
     * @brief Converts the input value from nanoseconds to the chosen precision units.
     *
     * This method is currently used by the Elapsed() method to convert elapsed time from nanoseconds (used by the
     * class) to the desired precision (requested by the user). However, it is a general converter that may be used by
     * other methods in the future.
     *
     * @param nanoseconds The value in nanoseconds to be converted to the desired precision.
     * @returns int64_t The converted time-value rounded to the whole number.
     */
    int64_t ConvertToPrecision(int64_t nanoseconds) const
    {
        switch (_precision[0])
        {
            case 'n': return nanoseconds;
            case 'u': return nanoseconds / 1000;
            case 'm': return nanoseconds / 1000000;
            case 's': return nanoseconds / 1000000000;
            default: throw std::invalid_argument("Unsupported precision");
        }
    }
};

/**
 * @brief The nanobind module that binds (exposes) the CPrecisionTimer class to the Python API.
 *
 * This modules wraps the CPrecisionTimer class and exposes it to Python via it's API.
 *
 * @note The module is available as 'precision_timer_ext' and has to be properly bound to a python package via CMake
 * configuration. Each method exposed to Python API below uses the names given as the first argument to each 'def'
 * method.
 */
NB_MODULE(precision_timer_ext, m)
{
    m.doc() = "A sub-microsecond-precise timer and non/blocking delay module.";
    nb::class_<CPrecisionTimer>(m, "CPrecisionTimer")
        .def(nb::init<const std::string&>(), "precision"_a = "us")
        .def("Reset", &CPrecisionTimer::Reset, "Resets the reference point of the class to the current time.")
        .def("Elapsed", &CPrecisionTimer::Elapsed,
        "Reports the elapsed time since the last reset() method call or class instantiation (whichever happened last).")
        .def("DelayNoblock", &CPrecisionTimer::DelayNoblock, "duration"_a, "allow_sleep"_a = false,
        "Delays for the requested period of time while releasing GIL")
        .def("DelayBlock", &CPrecisionTimer::DelayBlock, "duration"_a, "allow_sleep"_a = false,
        "Delays for the requested period of time without releasing GIL")
        .def("GetPrecision", &CPrecisionTimer::GetPrecision, "Returns the current precision of the timer.")
        .def("SetPrecision", &CPrecisionTimer::SetPrecision, "precision"_a, "Sets the class precision to new units.");
}
