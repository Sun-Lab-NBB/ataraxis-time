/**
 * @file
 *
 * @brief Defines and implements the CPrecisionTimer class as a nanobind-bound C++ extension module.
 *
 * Uses the monotonic system clock provided by the 'chrono' library, which allows the timer to resolve sub-microsecond
 * intervals on sufficiently fast CPUs. This module works on Windows, macOS, and Linux.
 *
 * @note This module is bound to Python using nanobind and is designed to be further wrapped with a pure-Python
 * PrecisionTimer class.
 */

// Dependencies:
#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <atomic>
#include <chrono>
#include <limits>
#include <stdexcept>
#include <string>
#include <thread>

// Simplifies interacting with the nanobind namespace by shortening it as nb.
namespace nb = nanobind;

/// Provides the ability to work with Python literal string-options.
using namespace nb::literals;

/// Provides the binding for various clock-related operations.
using namespace std::chrono;

/**
 * @brief Provides methods for sub-microsecond-precise interval timing and blocking / non-blocking code execution
 * delays.
 *
 * @note The performance of this class scales with the OS and the state of the host system. The class uses the 'chrono'
 * library's steady_clock, which advances monotonically and is therefore immune to the wall-clock adjustments that
 * network time synchronization applies. However, all method calls have a certain overhead associated with them and the
 * busier the OS is, the longer the overhead.
 *
 * @note Instances are safe to share between threads. The reference point and the precision are held in atomics, so a
 * thread calling Delay() with the GIL released observes a consistent configuration while another thread reconfigures
 * the instance.
 */
class CPrecisionTimer
{
    // Confirms the timer state resolves to lock-free hardware instructions rather than a mutex, which the Elapsed()
    // and Lap() methods depend on to stay usable inside time-critical loops.
    static_assert(
        std::atomic<steady_clock::time_point>::is_always_lock_free,
        "CPrecisionTimer requires a lock-free atomic steady_clock::time_point."
    );
    static_assert(std::atomic<int64_t>::is_always_lock_free, "CPrecisionTimer requires a lock-free atomic int64_t.");

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

        // Establishes the initial reference point so that elapsed time is measured from instantiation, matching the
        // behavior documented by the Elapsed() method.
        Reset();
    }

    /// Resets the timer.
    void Reset()
    {
        // Re-bases the start_time to use the current time obtained using the monotonic clock.
        _start_time.store(steady_clock::now());
    }

    /**
     * @brief Returns the time elapsed since the last Reset() or Lap() method call, or since class instantiation.
     *
     * @returns The elapsed time, using the current class precision units.
     */
    [[nodiscard]]
    int64_t Elapsed() const
    {
        const auto stop_time = steady_clock::now();
        const auto elapsed   = duration_cast<nanoseconds>(stop_time - _start_time.load());
        return ConvertToPrecision(elapsed.count());
    }

    /**
     * @brief Re-bases the timer and returns the time that elapsed since the previous reference point.
     *
     * Installs the new reference point and reads the one it replaces in a single atomic exchange, so the returned
     * interval begins exactly where the preceding interval ended. Consecutive calls therefore partition the elapsed
     * time, and concurrent calls from separate threads each receive a distinct slice of it.
     *
     * @returns The duration of the completed lap, using the current class precision units.
     */
    [[nodiscard]]
    int64_t Lap()
    {
        const auto stop_time = steady_clock::now();
        const auto previous  = _start_time.exchange(stop_time);
        return ConvertToPrecision(duration_cast<nanoseconds>(stop_time - previous).count());
    }

    /**
     * @brief Blocks (delays) in-place for the specified number of time-units (depends on used precision).
     *
     * Executes arbitrary delays while maintaining or releasing the Global Interpreter Lock (GIL).
     * By default, this method uses a busy-wait approach where the thread constantly checks elapsed time until the exit
     * condition is encountered and releases the GIL while waiting.
     *
     * @warning If sleeping is allowed, there is an overhead of up to 1 millisecond due to scheduling on the Windows OS.
     *
     * @param duration The time to block for. Uses the same units as the instance's precision parameter.
     * @param allow_sleep Determines whether the method may use sleep instead of busy-wait. Sleep is used only when
     * the instance precision is 'ms' or 's', regardless of the requested delay duration. It reduces CPU load at the
     * expense of additional overhead compared to the default busy-wait delay approach.
     * @param block Determines whether the method should release the GIL, allowing concurrent execution of other
     * Python threads. If false, the method releases the GIL. If true, the method maintains the GIL, preventing other
     * Python threads from running.
     *
     * @throws std::overflow_error If converting the duration to nanoseconds would exceed the range of a 64-bit signed
     * integer at the instance's current precision.
     */
    void Delay(const int64_t duration, const bool allow_sleep = false, const bool block = false) const
    {
        // Samples the precision once, because this method runs with the GIL released and SetPrecision() may replace
        // the value from another thread meanwhile. One sample keeps the overflow guard, the nanosecond conversion, and
        // the sleep decision consistent with each other.
        const int64_t precision_nanoseconds = _precision_nanoseconds.load();
        const int64_t maximum_duration      = std::numeric_limits<int64_t>::max() / precision_nanoseconds;

        // Rejects durations that the nanosecond conversion below cannot represent. Signed overflow is undefined
        // behavior, and the wrapped negative value would make the method return immediately instead of blocking.
        if (duration > maximum_duration || duration < -maximum_duration)
        {
            const std::string message =
                "Unable to delay the requested period of time. The 'duration' magnitude must "
                "not exceed " +
                std::to_string(maximum_duration) + " at the current timer precision, but received " +
                std::to_string(duration) + ".";
            throw std::overflow_error(message);
        }

        // Converts input delay duration to nanoseconds.
        const auto delay_duration = nanoseconds(duration * precision_nanoseconds);

        // Defines a lambda function to perform the actual delay
        auto perform_delay = [&]() {
            // If sleep is allowed and the instance precision is coarse enough (ms or s) to resolve the delay with
            // sleep, uses sleep_for() to release the CPU during blocking.
            if (allow_sleep && precision_nanoseconds >= kNanosecondsPerMillisecond)
            {
                std::this_thread::sleep_for(delay_duration);
            }
            // If sleep is not allowed or the instance precision is finer than a millisecond, uses a busy-wait
            // delay approach which uses CPU to improve delay precision.
            else
            {
                const auto start = steady_clock::now();
                while (duration_cast<nanoseconds>(steady_clock::now() - start) < delay_duration);
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
     * @param precision The new precision to use. Supported values are: 'ns' (nanoseconds), 'us' (microseconds),
     * 'ms' (milliseconds), and 's' (seconds).
     *
     * @throws std::invalid_argument If the precision does not exactly match one of the four supported options.
     */
    void SetPrecision(const std::string& precision)
    {
        // Resolves the requested option into locals before touching any member. A rejected precision therefore leaves
        // the instance on its previous valid configuration rather than in a partially updated state.
        kPrecisionUnits resolved_units;
        int64_t resolved_nanoseconds;
        if (precision == "ns")
        {
            resolved_units       = kPrecisionUnits::kNanosecond;
            resolved_nanoseconds = 1;
        }
        else if (precision == "us")
        {
            resolved_units       = kPrecisionUnits::kMicrosecond;
            resolved_nanoseconds = kNanosecondsPerMicrosecond;
        }
        else if (precision == "ms")
        {
            resolved_units       = kPrecisionUnits::kMillisecond;
            resolved_nanoseconds = kNanosecondsPerMillisecond;
        }
        else if (precision == "s")
        {
            resolved_units       = kPrecisionUnits::kSecond;
            resolved_nanoseconds = kNanosecondsPerSecond;
        }
        else
        {
            const std::string message =
                "Unable to set the timer precision. The precision must be one of 'ns', 'us', "
                "'ms', or 's', but received '" +
                precision + "'.";
            throw std::invalid_argument(message);
        }

        // Publishes the resolved configuration. Elapsed() reads the units and Delay() reads the nanosecond magnitude,
        // and no method reads both, so the two stores need no ordering relative to each other.
        _precision_units.store(resolved_units);
        _precision_nanoseconds.store(resolved_nanoseconds);
    }

    /// Returns the current precision of the timer ('ns', 'us', 'ms', or 's').
    [[nodiscard]]
    std::string get_precision() const
    {
        switch (_precision_units.load())
        {
            case kPrecisionUnits::kNanosecond: return "ns";
            case kPrecisionUnits::kMicrosecond: return "us";
            case kPrecisionUnits::kMillisecond: return "ms";
            case kPrecisionUnits::kSecond: return "s";
        }
        const std::string message =
            "Unable to report the timer precision. The internal precision state must be one of the four "
            "kPrecisionUnits members.";
        throw std::invalid_argument(message);
    }

    /// Returns a string representation of the CPrecisionTimer instance.
    [[nodiscard]]
    std::string Repr() const
    {
        return "CPrecisionTimer(precision=" + get_precision() + ")";
    }

    /// Destroys the CPrecisionTimer class.
    ~CPrecisionTimer() = default;

  private:
    /// Defines the timer precision options as a compact value, so that conversions dispatch on an integer rather than
    /// re-parsing a precision string on every call.
    enum class kPrecisionUnits : uint8_t
    {
        kNanosecond,   ///< The timer reports and accepts values in nanoseconds.
        kMicrosecond,  ///< The timer reports and accepts values in microseconds.
        kMillisecond,  ///< The timer reports and accepts values in milliseconds.
        kSecond,       ///< The timer reports and accepts values in seconds.
    };

    /// Stores the number of nanoseconds contained in a single microsecond.
    static constexpr int64_t kNanosecondsPerMicrosecond = 1'000;

    /// Stores the number of nanoseconds contained in a single millisecond.
    static constexpr int64_t kNanosecondsPerMillisecond = 1'000'000;

    /// Stores the number of nanoseconds contained in a single second.
    static constexpr int64_t kNanosecondsPerSecond = 1'000'000'000;

    /// Stores the reference point that elapsed intervals are measured from.
    std::atomic<steady_clock::time_point> _start_time;

    /// Stores the resolved form of the selected precision option, used to select the conversion divisor.
    std::atomic<kPrecisionUnits> _precision_units = kPrecisionUnits::kMicrosecond;

    /// Stores the number of nanoseconds in one unit of the selected precision, used as the conversion multiplier
    /// for delay durations.
    std::atomic<int64_t> _precision_nanoseconds = kNanosecondsPerMicrosecond;

    /**
     * @brief Converts the input value from nanoseconds to the chosen precision units.
     *
     * @param nanoseconds The value in nanoseconds to be converted to the desired precision.
     * @returns The converted time-value, truncated to the whole number via integer division toward zero.
     */
    [[nodiscard]]
    int64_t ConvertToPrecision(const int64_t nanoseconds) const
    {
        switch (_precision_units.load())
        {
            case kPrecisionUnits::kNanosecond: return nanoseconds;
            case kPrecisionUnits::kMicrosecond: return nanoseconds / kNanosecondsPerMicrosecond;
            case kPrecisionUnits::kMillisecond: return nanoseconds / kNanosecondsPerMillisecond;
            case kPrecisionUnits::kSecond: return nanoseconds / kNanosecondsPerSecond;
        }
        const std::string message =
            "Unable to convert the value to the timer precision. The internal precision state must be one of the "
            "four kPrecisionUnits members.";
        throw std::invalid_argument(message);
    }
};

/**
 * @brief Binds the CPrecisionTimer class to the Python API via nanobind.
 *
 * The module is available as 'precision_timer_ext' and must be bound to a Python package via CMake configuration.
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
            "Reports the time elapsed since the last Reset() or Lap() method call, or since class instantiation."
        )
        .def(
            "Lap",
            &CPrecisionTimer::Lap,
            "Re-bases the reference point to the current time and reports the interval that just ended."
        )
        .def(
            "Delay",
            &CPrecisionTimer::Delay,
            "duration"_a,
            "allow_sleep"_a = false,
            "block"_a       = false,
            "Delays for the requested period of time while releasing or maintaining the GIL."
        )
        .def("get_precision", &CPrecisionTimer::get_precision, "Returns the current precision of the timer.")
        .def("SetPrecision", &CPrecisionTimer::SetPrecision, "precision"_a, "Sets the class precision to new units.")
        .def("__repr__", &CPrecisionTimer::Repr);
}
