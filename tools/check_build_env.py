"""Verifies that the local host is ready to cross-build and test the configured binary wheels before cibuildwheel runs.

cibuildwheel cross-compiles wheels for several architectures per platform, but testing a foreign-architecture wheel
needs emulation that cibuildwheel does not install. When the emulation layer is missing, the build proceeds and then
fails deep in the test phase with an opaque error. This preflight reads the architecture matrix from ``pyproject.toml``
and checks the host up front, failing fast with concrete remediation instead.

On macOS it confirms Rosetta 2 is present when x86_64 wheels are tested on Apple Silicon, and warns that arm64 wheels
cannot be tested on Intel hosts. On Linux it confirms Docker is running and that QEMU is registered with binfmt_misc for
every non-native architecture. On Windows it confirms the ARM64 MSVC runtime redistributable resolves when ARM64 wheels
are configured, reusing the same discovery the repair step depends on.

The script is intentionally dependency-free so it can run inside the thin tox build environment, which does not install
the project or its runtime dependencies. It reports problems on standard error and exits non-zero, mirroring the repair
helper alongside it.
"""

from __future__ import annotations

import sys
import shutil
import platform
import tomllib
import subprocess
from pathlib import Path

from repair_windows_wheel import discover_crt_dir

_PYPROJECT: Path = Path(__file__).resolve().parent.parent / "pyproject.toml"
"""Location of the project configuration that declares the per-platform architecture build matrix."""

_QEMU_BY_ARCH: dict[str, str] = {
    "aarch64": "qemu-aarch64",
    "x86_64": "qemu-x86_64",
    "i686": "qemu-i386",
    "ppc64le": "qemu-ppc64le",
    "s390x": "qemu-s390x",
}
"""Maps a cibuildwheel Linux architecture to the binfmt_misc handler name QEMU registers for it."""

_NATIVE_LINUX_ARCHS: dict[str, frozenset[str]] = {
    "x86_64": frozenset({"x86_64", "i686"}),
    "aarch64": frozenset({"aarch64"}),
}
"""Maps a Linux host machine to the target architectures it executes natively, without QEMU emulation."""


def main() -> int:
    """Checks host readiness for the current platform and reports problems before cibuildwheel runs."""
    host = sys.platform
    if host == "darwin":
        errors, warnings = _check_macos()
    elif host.startswith("linux"):
        errors, warnings = _check_linux()
    elif host == "win32":
        errors, warnings = _check_windows()
    else:
        message = f"Unable to verify the build environment. The host platform '{host}' is not supported."
        raise SystemExit(message)

    for warning in warnings:
        sys.stdout.write(f"WARNING: {warning}\n")
    if errors:
        report = "\n".join(f"  - {error}" for error in errors)
        message = f"The build environment is not ready. Resolve the following before running cibuildwheel:\n{report}"
        raise SystemExit(message)
    sys.stdout.write("The build environment is ready for cibuildwheel.\n")
    return 0


def _check_macos() -> tuple[list[str], list[str]]:
    """Checks whether macOS can test every configured wheel architecture, given Rosetta 2 emulation constraints."""
    errors: list[str] = []
    warnings: list[str] = []
    host_arch = platform.machine()
    archs = _read_archs(platform_key="macos") or [host_arch]

    if host_arch == "arm64" and "x86_64" in archs:
        # cibuildwheel runs the x86_64 test suite under Rosetta 2; without it the test phase fails.
        probe = subprocess.run(["arch", "-x86_64", "/usr/bin/true"], capture_output=True, check=False)
        if probe.returncode != 0:
            errors.append(
                "Rosetta 2 is required to test x86_64 wheels on Apple Silicon but is not installed. Install it with "
                "'softwareupdate --install-rosetta --agree-to-license'."
            )
    if host_arch == "x86_64" and "arm64" in archs:
        warnings.append(
            "arm64 wheels cannot be tested on an Intel host; cibuildwheel will skip those tests. Set "
            "CIBW_TEST_SKIP='*_arm64 *_universal2:arm64' to silence the warning."
        )
    return errors, warnings


def _check_linux() -> tuple[list[str], list[str]]:
    """Checks whether Docker is running and QEMU is registered for every non-native architecture to build."""
    errors: list[str] = []
    warnings: list[str] = []

    if shutil.which("docker") is None:
        errors.append("Docker is required to build Linux wheels but the 'docker' command was not found on PATH.")
        return errors, warnings
    probe = subprocess.run(["docker", "info"], capture_output=True, check=False)
    if probe.returncode != 0:
        errors.append("Docker is installed but not responding. Start the Docker daemon and try again.")
        return errors, warnings

    host_arch = platform.machine()
    native = _NATIVE_LINUX_ARCHS.get(host_arch, frozenset({host_arch}))
    emulated = [arch for arch in (_read_archs(platform_key="linux") or [host_arch]) if arch not in native]
    missing = sorted(arch for arch in emulated if not _binfmt_registered(arch=arch))
    if missing:
        targets = ", ".join(missing)
        errors.append(
            f"QEMU emulation is not registered for {targets}, which Docker needs to build these architectures. "
            f"Register it with 'docker run --privileged --rm tonistiigi/binfmt --install all'."
        )
    return errors, warnings


def _check_windows() -> tuple[list[str], list[str]]:
    """Checks whether the ARM64 MSVC runtime resolves when ARM64 wheels are part of the build matrix."""
    errors: list[str] = []
    warnings: list[str] = []
    if "ARM64" in _read_archs(platform_key="windows") and discover_crt_dir(arch="arm64") is None:
        errors.append(
            "The ARM64 MSVC C++ runtime redistributable could not be located, which delvewheel needs to repair ARM64 "
            "wheels. Install the ARM64 build tools and the C++ ARM64 runtime via the Visual Studio Installer."
        )
    return errors, warnings


def _read_archs(platform_key: str) -> list[str]:
    """Returns the architectures configured for the given cibuildwheel platform, or an empty list when none are set."""
    with _PYPROJECT.open("rb") as handle:
        config = tomllib.load(handle)
    platform_table = config.get("tool", {}).get("cibuildwheel", {}).get(platform_key, {})
    return list(platform_table.get("archs", []))


def _binfmt_registered(arch: str) -> bool:
    """Returns True when binfmt_misc has an enabled QEMU handler registered for the given architecture."""
    handler = _QEMU_BY_ARCH.get(arch)
    if handler is None:
        return False
    handler_path = Path("/proc/sys/fs/binfmt_misc") / handler
    return handler_path.is_file() and "enabled" in handler_path.read_text(encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
