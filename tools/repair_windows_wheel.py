"""Repairs a freshly built Windows wheel with delvewheel, auto-discovering the MSVC C++ runtime redistributable.

The script is dependency-free so it can run inside the thin tox build environment, which does not install the project
or its runtime dependencies.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
import subprocess

_EXPECTED_ARGUMENT_COUNT: int = 3
"""The number of entries sys.argv carries when the script receives both of its positional arguments."""

_VSWHERE: Path = (
    Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
    / "Microsoft Visual Studio"
    / "Installer"
    / "vswhere.exe"
)
"""Stable, Microsoft-guaranteed location of the Visual Studio locator utility, present for any modern installation."""

_ARCHITECTURE_BY_TAG: dict[str, str] = {"win_arm64": "arm64", "win_amd64": "x64", "win32": "x86"}
"""Maps the wheel-filename platform tag to the Visual Studio redistributable architecture subdirectory name."""


def main() -> int:
    """Resolves the runtime directory for ARM64 targets and runs delvewheel to repair the wheel.

    The compiled extension links against the MSVC C++ runtime, and a typical Windows host carries only the AMD64 copies
    of those DLLs on PATH. delvewheel therefore cannot find an architecture-matching ARM64 runtime to vendor, so this
    function passes the discovered directory to it through '--add-path'.

    Returns:
        The exit code delvewheel reported.

    Raises:
        SystemExit: If the script did not receive exactly two positional arguments.
        FileNotFoundError: If the ARM64 runtime redistributable could not be located for an ARM64 wheel.
    """
    if len(sys.argv) != _EXPECTED_ARGUMENT_COUNT:
        message = (
            f"Unable to repair a Windows wheel using {Path(sys.argv[0]).name}. The script requires exactly two "
            f"positional arguments, the destination directory and the wheel path, but received {len(sys.argv) - 1}."
        )
        raise SystemExit(message)
    destination_directory, wheel = sys.argv[1], sys.argv[2]

    command = [sys.executable, "-m", "delvewheel", "repair", "-v", "-w", destination_directory, wheel]

    tag = next((candidate for candidate in _ARCHITECTURE_BY_TAG if candidate in Path(wheel).name), None)
    # Only ARM64 needs an explicit search path. AMD64 and x86 runtimes are already on the host's PATH.
    if tag == "win_arm64":
        runtime_directory = discover_runtime_directory(architecture=_ARCHITECTURE_BY_TAG[tag])
        if runtime_directory is None:
            message = (
                f"Unable to repair the ARM64 wheel '{Path(wheel).name}'. Could not locate the ARM64 MSVC C++ runtime "
                f"redistributable (a 'Microsoft.VC*.CRT' folder containing 'msvcp140.dll'). Install the ARM64 build "
                f"tools and the C++ ARM64 runtime via the Visual Studio Installer, or set ATARAXIS_ARM64_CRT_DIR to "
                f"the redistributable directory."
            )
            raise FileNotFoundError(message)
        sys.stdout.write(f"Using ARM64 MSVC runtime redistributable: {runtime_directory}\n")
        command += ["--add-path", str(runtime_directory)]

    sys.stdout.flush()
    return subprocess.run(args=command, check=False).returncode


def discover_runtime_directory(architecture: str) -> Path | None:
    """Discovers the MSVC runtime redistributable directory for the requested architecture.

    The resolver adapts to local build infrastructure through a layered fallback chain, so that no machine- or
    version-specific path has to be hardcoded in the project configuration.

    Args:
        architecture: The Visual Studio redistributable architecture subdirectory to search for, such as 'arm64'.

    Returns:
        The directory holding the architecture-matching runtime DLLs, or None when no candidate carries 'msvcp140.dll'.
    """
    # Honors an explicit manual override before probing the toolchain.
    override = os.environ.get("ATARAXIS_ARM64_CRT_DIR")
    if override and (Path(override) / "msvcp140.dll").is_file():
        return Path(override)

    # Falls back to the developer-prompt variable, which points at the redistributable version root.
    redistributable_root = os.environ.get("VCToolsRedistDir")
    if redistributable_root:
        for candidate in sorted((Path(redistributable_root) / architecture).glob("Microsoft.VC*.CRT")):
            if (candidate / "msvcp140.dll").is_file():
                return candidate

    # Queries vswhere for the active Visual Studio installations and resolves each one's redistributable.
    if _VSWHERE.is_file():
        result = subprocess.run(
            args=[str(_VSWHERE), "-products", "*", "-latest", "-prerelease", "-property", "installationPath"],
            capture_output=True,
            text=True,
            check=False,
        )
        for line in result.stdout.splitlines():
            install_path = Path(line.strip())
            if install_path.is_dir():
                runtime_directory = _runtime_directory_for(install_path=install_path, architecture=architecture)
                if runtime_directory is not None:
                    return runtime_directory

    # Globs every Program Files Visual Studio installation as a last resort. The newest version wins.
    program_files = {
        os.environ.get("ProgramFiles", r"C:\Program Files"),
        os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
    }
    matches: list[Path] = []
    for root in filter(None, program_files):
        pattern = str(
            Path("Microsoft Visual Studio")
            / "*"
            / "*"
            / "VC"
            / "Redist"
            / "MSVC"
            / "*"
            / architecture
            / "Microsoft.VC*.CRT"
        )
        matches.extend(path for path in Path(root).glob(pattern) if (path / "msvcp140.dll").is_file())
    return max(matches, key=_version_key) if matches else None


def _runtime_directory_for(install_path: Path, architecture: str) -> Path | None:
    """Returns the runtime redistributable directory for the given architecture within a Visual Studio installation.

    Args:
        install_path: The root directory of the Visual Studio installation to search.
        architecture: The Visual Studio redistributable architecture subdirectory to search for.

    Returns:
        The directory holding the architecture-matching runtime DLLs, or None when the version marker or the runtime
        folder is absent.
    """
    marker = install_path / "VC" / "Auxiliary" / "Build" / "Microsoft.VCRedistVersion.default.txt"
    if not marker.is_file():
        return None
    version = marker.read_text(encoding="utf-8").strip()
    architecture_root = install_path / "VC" / "Redist" / "MSVC" / version / architecture
    for candidate in sorted(architecture_root.glob("Microsoft.VC*.CRT")):
        if (candidate / "msvcp140.dll").is_file():
            return candidate
    return None


def _version_key(path: Path) -> tuple[int, ...]:
    """Builds a sortable numeric key from the MSVC version segment embedded in a redistributable path.

    Allows '14.44.35112' to sort above '14.29.30133' numerically rather than lexicographically.

    Args:
        path: The redistributable directory whose version segment is read.

    Returns:
        The version segment as a tuple of integers, or a zero key when the segment is missing or non-numeric.
    """
    match = re.search(pattern=r"[\\/]Redist[\\/]MSVC[\\/]([0-9.]+)[\\/]", string=str(path))
    return tuple(int(part) for part in match.group(1).split(".")) if match else (0,)


if __name__ == "__main__":
    raise SystemExit(main())
