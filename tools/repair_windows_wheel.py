"""Repairs a freshly built Windows wheel with delvewheel, auto-discovering the MSVC C++ runtime redistributable.

Supports Windows ARM64 wheels built by cibuildwheel. The compiled extension links against the MSVC C++ runtime
(``msvcp140.dll``, ``vcruntime140*.dll``). On a typical Windows host only the AMD64 copies of these DLLs are present on
``PATH`` (under ``System32``); the ARM64 copies ship only inside the Visual Studio redistributable tree, which is not on
``PATH``. delvewheel therefore cannot find an architecture-matching runtime to vendor and aborts. Rather than hardcode a
machine- and version-specific redistributable path in ``pyproject.toml``, this script discovers the correct directory at
build time and passes it to delvewheel via ``--add-path``.

The resolver adapts to local build infrastructure through a layered fallback chain. It first honors an explicit
``ATARAXIS_ARM64_CRT_DIR`` override, then the ``VCToolsRedistDir`` variable set inside a Visual Studio developer command
prompt. Then it queries ``vswhere.exe`` (installed at a stable Microsoft-guaranteed path) and reads the
``Microsoft.VCRedistVersion.default.txt`` marker for the default redistributable version, and finally globs every
Program Files Visual Studio installation for the newest redistributable. For non-ARM64 wheels it simply forwards to
delvewheel without an extra search path, preserving the default repair behavior for AMD64 and x86 builds.
"""

from __future__ import annotations

import os
import re
import sys
import glob
import subprocess
from pathlib import Path

_VSWHERE: Path = (
    Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
    / "Microsoft Visual Studio"
    / "Installer"
    / "vswhere.exe"
)
"""Stable, Microsoft-guaranteed location of the Visual Studio locator utility, present for any modern installation."""

_ARCH_BY_TAG: dict[str, str] = {"win_arm64": "arm64", "win_amd64": "x64", "win32": "x86"}
"""Maps the wheel-filename platform tag to the Visual Studio redistributable architecture subdirectory name."""


def main() -> int:
    """Resolves the runtime directory for ARM64 targets and runs delvewheel to repair the wheel."""
    if len(sys.argv) != 3:
        message = (
            f"Unable to repair a Windows wheel using {Path(sys.argv[0]).name}. The script requires exactly two "
            f"positional arguments, the destination directory and the wheel path, but received {len(sys.argv) - 1}."
        )
        raise SystemExit(message)
    dest_dir, wheel = sys.argv[1], sys.argv[2]

    command = [sys.executable, "-m", "delvewheel", "repair", "-v", "-w", dest_dir, wheel]

    tag = next((candidate for candidate in _ARCH_BY_TAG if candidate in Path(wheel).name), None)
    # Only ARM64 needs an explicit search path; AMD64 and x86 runtimes are already on the host's PATH.
    if tag == "win_arm64":
        crt_dir = discover_crt_dir(arch=_ARCH_BY_TAG[tag])
        if crt_dir is None:
            message = (
                f"Unable to repair the ARM64 wheel '{Path(wheel).name}'. Could not locate the ARM64 MSVC C++ runtime "
                f"redistributable (a 'Microsoft.VC*.CRT' folder containing 'msvcp140.dll'). Install the ARM64 build "
                f"tools and the C++ ARM64 runtime via the Visual Studio Installer, or set ATARAXIS_ARM64_CRT_DIR to "
                f"the redistributable directory."
            )
            raise FileNotFoundError(message)
        sys.stdout.write(f"Using ARM64 MSVC runtime redistributable: {crt_dir}\n")
        command += ["--add-path", str(crt_dir)]

    sys.stdout.flush()
    return subprocess.run(command, check=False).returncode


def discover_crt_dir(arch: str) -> Path | None:
    """Discovers the MSVC runtime redistributable directory for the requested architecture via the fallback chain."""
    # Honor an explicit manual override before probing the toolchain.
    override = os.environ.get("ATARAXIS_ARM64_CRT_DIR")
    if override and (Path(override) / "msvcp140.dll").is_file():
        return Path(override)

    # Fall back to the developer-prompt variable, which points at the redistributable version root.
    redist_root = os.environ.get("VCToolsRedistDir")
    if redist_root:
        for candidate in sorted((Path(redist_root) / arch).glob("Microsoft.VC*.CRT")):
            if (candidate / "msvcp140.dll").is_file():
                return candidate

    # Query vswhere for the active Visual Studio installation(s) and resolve each one's redistributable.
    if _VSWHERE.is_file():
        result = subprocess.run(
            [str(_VSWHERE), "-products", "*", "-latest", "-prerelease", "-property", "installationPath"],
            capture_output=True,
            text=True,
            check=False,
        )
        for line in result.stdout.splitlines():
            install_path = Path(line.strip())
            if install_path.is_dir():
                crt_dir = _crt_dir_for(install_path=install_path, arch=arch)
                if crt_dir is not None:
                    return crt_dir

    # Glob every Program Files Visual Studio installation as a last resort; the newest version wins.
    program_files = {
        os.environ.get("ProgramFiles", r"C:\Program Files"),
        os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
    }
    matches: list[str] = []
    for root in filter(None, program_files):
        pattern = str(
            Path(root)
            / "Microsoft Visual Studio"
            / "*"
            / "*"
            / "VC"
            / "Redist"
            / "MSVC"
            / "*"
            / arch
            / "Microsoft.VC*.CRT"
        )
        matches.extend(path for path in glob.glob(pattern) if (Path(path) / "msvcp140.dll").is_file())
    return Path(max(matches, key=_version_key)) if matches else None


def _crt_dir_for(install_path: Path, arch: str) -> Path | None:
    """Returns the runtime redistributable directory for the given architecture within a Visual Studio installation.

    Reads the ``Microsoft.VCRedistVersion.default.txt`` marker to determine the default redistributable version, then
    resolves the ``Microsoft.VC*.CRT`` folder that actually contains ``msvcp140.dll``. Returns None when the marker or
    the runtime folder is absent.
    """
    marker = install_path / "VC" / "Auxiliary" / "Build" / "Microsoft.VCRedistVersion.default.txt"
    if not marker.is_file():
        return None
    version = marker.read_text(encoding="utf-8").strip()
    arch_root = install_path / "VC" / "Redist" / "MSVC" / version / arch
    for candidate in sorted(arch_root.glob("Microsoft.VC*.CRT")):
        if (candidate / "msvcp140.dll").is_file():
            return candidate
    return None


def _version_key(path: str) -> tuple[int, ...]:
    """Builds a sortable numeric key from the MSVC version segment embedded in a redistributable path.

    Allows '14.44.35112' to sort above '14.29.30133' numerically rather than lexicographically. Non-numeric or missing
    segments collapse to a zero key so such paths sort last.
    """
    match = re.search(pattern=r"\\Redist\\MSVC\\([0-9.]+)\\", string=path)
    return tuple(int(part) for part in match.group(1).split(".")) if match else (0,)


if __name__ == "__main__":
    raise SystemExit(main())
