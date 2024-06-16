"""Tests the benchmark() function.

To improve testing latency, the tests run with parameters considerably lower than those used by default when the
benchmark is invoked using the cli interface.
"""

import pytest  # type: ignore
from ataraxis_time import benchmark
from click.testing import CliRunner  # type: ignore


@pytest.fixture
def runner() -> CliRunner:
    """Creates the click runner used to control the tested benchmark() function."""
    return CliRunner()


def test_benchmark_custom_parameters(runner: CliRunner) -> None:
    """Verifies the benchmark() using custom parameters to reduce test runtime speed."""
    # noinspection PyTypeChecker
    result = runner.invoke(
        benchmark,
        [
            "--interval-cycles",
            "1",
            "--interval-delay",
            "0.5",
            "--delay-cycles",
            10,
            10,
            10,
            1,
            "--delay-durations",
            100,
            2,
            1,
            1,
        ],
    )
    assert result.exit_code == 0
    assert "Timer Benchmark: Initialized." in result.output
    assert "Interval Timing:" in result.output
    assert "Busy-wait Delay Timing:" in result.output
    assert "Sleep Delay Timing:" in result.output
    assert "Benchmark: Complete." in result.output


def test_benchmark_invalid_cli_arguments(runner: CliRunner) -> None:
    """Verifies error-handling in response to invalid CLI arguments.

    Generally, the method should be able to handle all
    invalid arguments at the level of the cli input and, combined with other tests, this should be sufficient to
    conclude it works as intended in all expected use cases.
    """

    # Test invalid --interval-cycles
    # noinspection PyTypeChecker
    result = runner.invoke(benchmark, ["--interval-cycles", "invalid"])
    assert result.exit_code != 0
    assert "Invalid value for '--interval-cycles'" in result.output

    # noinspection PyTypeChecker
    result = runner.invoke(benchmark, ["--interval-cycles", "-1"])
    assert result.exit_code != 0
    assert "Invalid value for '--interval-cycles'" in result.output

    # noinspection PyTypeChecker
    result = runner.invoke(benchmark, ["--interval-cycles", "0"])
    assert result.exit_code != 0
    assert "Invalid value for '--interval-cycles'" in result.output

    # Test invalid --interval-delay
    # noinspection PyTypeChecker
    result = runner.invoke(benchmark, ["--interval-delay", "invalid"])
    assert result.exit_code != 0
    assert "Invalid value for '--interval-delay'" in result.output

    # noinspection PyTypeChecker
    result = runner.invoke(benchmark, ["--interval-delay", "-1"])
    assert result.exit_code != 0
    assert "Invalid value for '--interval-delay'" in result.output

    # noinspection PyTypeChecker
    result = runner.invoke(benchmark, ["--interval-delay", "0"])
    assert result.exit_code != 0
    assert "Invalid value for '--interval-delay'" in result.output

    # Test invalid --delay-cycles
    # noinspection PyTypeChecker
    result = runner.invoke(benchmark, ["--delay-cycles", 100, 100])
    assert result.exit_code != 0
    assert "Option '--delay-cycles' requires 4 arguments." in result.output

    # noinspection PyTypeChecker
    result = runner.invoke(benchmark, ["--delay-cycles", 100, "invalid", 100, 60])
    assert result.exit_code != 0
    assert "Invalid value for '--delay-cycles'" in result.output

    # noinspection PyTypeChecker
    result = runner.invoke(benchmark, ["--delay-cycles", 100, -1, 100, 60])
    assert result.exit_code != 0
    assert "Invalid value for '--delay-cycles'" in result.output

    # noinspection PyTypeChecker
    result = runner.invoke(benchmark, ["--delay-cycles", 100, 0, 100, 60])
    assert result.exit_code != 0
    assert "Invalid value for '--delay-cycles'" in result.output

    # Test invalid --delay-durations
    # noinspection PyTypeChecker
    result = runner.invoke(benchmark, ["--delay-durations", 100, 2])
    assert result.exit_code != 0
    assert "--delay-durations' requires 4 arguments." in result.output

    # noinspection PyTypeChecker
    result = runner.invoke(benchmark, ["--delay-durations", 100, "invalid", 2, 1])
    assert result.exit_code != 0
    assert "Invalid value for '--delay-durations'" in result.output

    # noinspection PyTypeChecker
    result = runner.invoke(benchmark, ["--delay-durations", 100, -1, 2, 1])
    assert result.exit_code != 0
    assert "Invalid value for '--delay-durations'" in result.output

    # noinspection PyTypeChecker
    result = runner.invoke(benchmark, ["--delay-durations", 100, 0, 2, 1])
    assert result.exit_code != 0
    assert "Invalid value for '--delay-durations'" in result.output
