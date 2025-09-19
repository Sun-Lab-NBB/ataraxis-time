/**
 * @file precision_timer_ext.cpp
 * @brief The C++ extension module that defines and implements the CPrecisionTimer class.
 *
 * @section description Description:
 * This module instantiates the CPrecisionTimer class using the fastest system clock available through the 'chrono'
 * library, which allows the timer to resolve sub-microsecond timer-intervals on sufficiently fast CPUs. This module
 * works on Windows, macOS, and Linux.
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
 * @brief Provides methods for sub-microsecond-precise interval timing and blocking / non-blocking code execution
 * delays.
 *
 * @note The performance of this class scales with the OS and the state of the host system. The 'chrono' library
 * provides a high_resolution_clock, which is automatically set to the highest resolution clock of the host OS.
 * However, all method calls have a certain overhead associated with them and the busier the OS is, the longer the
 * overhead.
 */
class CPrecisionTimer
{
  public:
    /**
     * @brief Instantiates the CPrecisionTimer class using the requested precision.
     *
     * @param precision The precision of the timer. This controls the units used by the timer for all inputs and
     * outputs. Supported values are: 'ns' (nanoseconds), 'us' (microseconds), 'ms' (milliseconds), and 's' (seconds).
     */
    explicit CPrecisionTimer(const std::string& precision = "us")
    {
        SetPrecision(precision);
    }

    /**
     * @brief Destroys the CPrecisionTimer class.
     */
    ~CPrecisionTimer()
    = default;

    /**
     * @brief Resets the timer.
     */
    void Reset()
    {
        // Re-bases the start_time to use the current time obtained using the highest resolution clock.
        _start_time = high_resolution_clock::now();
    }

    /**
     * @brief Returns the time elapsed since the last reset() method call or class instantiation.
     *
     * @returns int64_t The elapsed time, using the current class precision units.
     */
    [[nodiscard]] int64_t Elapsed() const
    {
        const auto stop_time = high_resolution_clock::now();
        const auto elapsed   = duration_cast<nanoseconds>(stop_time - _start_time);
        return ConvertToPrecision(elapsed.count());
    }

    /**
     * @brief Blocks (delays) in-place for the specified number of time-units (depends on used precision).
     *
     * This method is used to execute arbitrary delays while maintaining or releasing the Global Interpreter Lock (GIL).
     * By default, this method uses a busy-wait approach where the thread constantly checks elapsed time until the exit
     * condition is encountered and releases the GIL while waiting.
     *
     * @warning If sleeping is allowed, there is an overhead of up to 1 millisecond due to scheduling on the Windows OS.
     *
     * @param duration The time to block for. Uses the same units as the instance's precision parameter.
     * @param allow_sleep Determines whether the method should use sleep for delay durations above 1 millisecond. Sleep
     * may be beneficial in some cases as it reduces the CPU load at the expense of an additional overhead compared to
     * the default busy-wait delay approach.
     * @param block Determines whether the method should release the GIL, allowing concurrent execution of other
     * Python threads. If false, the method releases the GIL. If true, the method maintains the GIL, preventing other
     * Python threads from running.
     */
    void Delay(const int64_t duration, const bool allow_sleep = false, const bool block = false) const
    {
        // Converts input delay duration to nanoseconds.
        const auto delay_duration = duration * _precision_duration;

        // Defines a lambda function to perform the actual delay
        auto perform_delay = [&]() {
            // If sleep is allowed and delay duration is sufficiently long to resolve with sleep, uses sleep_for() to
            // release the CPU during blocking.
            if (allow_sleep && _precision_duration >= milliseconds(1))
            {
                std::this_thread::sleep_for(delay_duration);
            }
            // If sleep is not allowed or the requested delay is too short, uses a busy-wait delay approach which
            // uses CPU to improve delay precision.
            else
            {
                const auto start = high_resolution_clock::now();
                while (duration_cast<nanoseconds>(high_resolution_clock::now() - start) < delay_duration);
            }
        };

        // Executes the delay with or without GIL based on the block parameter
        if (!block)
        {
            nb::gil_scoped_release release;  // Releases the GIL for the entire scope
            perform_delay();
        }
        else
        {
            perform_delay();  // Keeps GIL held
        }
    }

    /**
     * @brief Changes the timer precision used by the instance to the requested units.
     *
     * This method can be used to dynamically change the precision used by a class instance during runtime.
     *
     * @param precision The new precision to use. Supported values are: 'ns' (nanoseconds),
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
    [[nodiscard]] std::string GetPrecision() const
    {
        return _precision;
    }

  private:
    /// Stores the reference value used to calculate elapsed time.
    high_resolution_clock::time_point _start_time;

    /// Stores the string-option that describes the units used for inputs and outputs.
    std::string _precision;

    /// Stores the conversion factor that is assigned based on the chosen _precision option. It is used to convert the
    /// input duration values (for delay methods) to nanoseconds and the output duration values from nanoseconds to the
    /// chosen precision units.
    nanoseconds _precision_duration = microseconds(1);

    /**
     * @brief Converts the input value from nanoseconds to the chosen precision units.
     *
     * This method is currently used by the Elapsed() method to convert elapsed time from nanoseconds (used by the
     * class) to the desired precision (requested by the user). However, it is a general converter that may be used by
     * other methods in the future.
     *
     * @param nanoseconds The value in nanoseconds to be converted to the desired precision.
     * @returns int64_t The converted time-value, rounded to the whole number.
     */
    [[nodiscard]]
    int64_t ConvertToPrecision(const int64_t nanoseconds) const
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
 * This nanobind module wraps the CPrecisionTimer class and exposes it to Python via its API.
 *
 * @note The module is available as 'precision_timer_ext' and has to be properly bound to a python package via CMake
 * configuration. Each method exposed to Python API below uses the names given as the first argument to each 'def'
 * method.
 */
// NOLINTNEXTLINE(performance-unnecessary-value-param)
NB_MODULE(precision_timer_ext, m)
{
    m.doc() = "A sub-microsecond-precise timer and non/blocking delay module.";
    nb::class_<CPrecisionTimer>(m, "CPrecisionTimer")
        .def(nb::init<const std::string&>(), "precision"_a = "us")
        .def("Reset", &CPrecisionTimer::Reset, "Resets the reference point of the class to the current time.")
        .def(
            "Elapsed",
            &CPrecisionTimer::Elapsed,
            "Reports the time elapsed since the last reset() method call or class instantiation (whichever happened "
            "last)."
        )
        .def(
            "Delay",
            &CPrecisionTimer::Delay,
            "duration"_a,
            "allow_sleep"_a = false,
            "block"_a = false,
            "Delays for the requested period of time while releasing or maintaining the GIL."
        )
        .def("GetPrecision", &CPrecisionTimer::GetPrecision, "Returns the current precision of the timer.")
        .def("SetPrecision", &CPrecisionTimer::SetPrecision, "precision"_a, "Sets the class precision to new units.");
}
