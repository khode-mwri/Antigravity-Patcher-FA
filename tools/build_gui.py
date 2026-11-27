#!/usr/bin/env python3
"""Build the Antigravity Patcher FA (Persian) tkinter GUI as a one-file exe.

What it does
------------
1. Checks that ``source/gui.py``, ``source/icon.ico`` and ``source/version.txt``
   exist. The repo root is resolved from this script's own ``__file__``, so the
   tool can be run from any working directory.
2. Runs PyInstaller (``sys.executable -m PyInstaller``) with ``cwd=source/`` so
   ``icon.ico`` and ``version.txt`` resolve exactly like the release workflow
   (``.github/workflows/release.yml``): ``--onefile --windowed --uac-admin``,
   the same ``packaging`` hidden imports as the CLI exe, ``--noupx --clean``,
   and -- only when importable locally -- ``--collect-data arabic_reshaper``
   and ``--hidden-import=bidi.algorithm``. ``--icon`` and ``--version-file``
   are Windows-only and are skipped elsewhere. Build artifacts stay out of the
   source tree, under ``tools/_runtime/gui_dist`` (exe) and
   ``tools/_runtime/gui_build`` (PyInstaller work and spec files).
3. Verifies the exe exists and prints its absolute path and size in MB.
4. Unless ``--no-run`` is given, launches the exe once with ``subprocess.Popen``,
   waits 15 seconds, then terminates its process tree. A working GUI keeps its
   main loop running, so "still alive after 15 s" is the success signal; an
   early exit is reported with the captured exit code. The GUI is windowed (no
   console), so its stdout is not captured.

The build takes a few minutes: PyInstaller freezes the whole interpreter and
bundles the RTL (arabic_reshaper / python-bidi) runtime data.

Usage
-----
    python tools/build_gui.py             # build, then smoke-launch the exe
    python tools/build_gui.py --no-run    # build only

Exit codes
----------
0 = build succeeded (and, unless --no-run, the exe survived the launch window;
    an unelevated Windows shell cannot start a ``--uac-admin`` exe and that
    specific condition is reported as a warning, not a failure)
1 = PyInstaller failed, the exe is missing afterwards, or the exe crashed
    during the launch check
2 = prerequisites are missing (required source files)

Note: ``--uac-admin`` embeds a requireAdministrator manifest, so an unelevated
terminal cannot launch the resulting exe. Run this tool from an elevated
terminal if you want the launch check to really exercise the exe.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import signal
import subprocess
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
SOURCE_DIR = REPO_ROOT / "source"
RUNTIME_DIR = TOOLS_DIR / "_runtime"
DIST_DIR = RUNTIME_DIR / "gui_dist"
BUILD_DIR = RUNTIME_DIR / "gui_build"
BUILD_LOG = BUILD_DIR / "gui_build.log"

APP_NAME = "Antigravity_Patcher_FA_GUI"
ENTRY_SCRIPT = "gui.py"
ICON_NAME = "icon.ico"
VERSION_FILE_NAME = "version.txt"

# Same hidden imports as the CLI exe in .github/workflows/release.yml.
HIDDEN_IMPORTS: tuple[str, ...] = (
    "packaging",
    "packaging.version",
    "packaging.specifiers",
    "packaging.requirements",
)

BUILD_TIMEOUT_SECONDS = 900
LAUNCH_TIMEOUT_SECONDS = 15
TAIL_LINES = 30


def module_available(name: str) -> bool:
    """Return True when *name* can be imported by the current interpreter."""
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, AttributeError, ValueError):
        return False


def check_prerequisites() -> list[Path]:
    """Return the required source files that are missing (empty when all exist)."""
    required = (
        SOURCE_DIR / ENTRY_SCRIPT,
        SOURCE_DIR / ICON_NAME,
        SOURCE_DIR / VERSION_FILE_NAME,
    )
    return [path for path in required if not path.is_file()]


def build_command() -> list[str]:
    """Assemble the PyInstaller command line for the GUI executable."""
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--windowed",
        "--uac-admin",
        f"--name={APP_NAME}",
        "--noupx",
        "--clean",
        "--noconfirm",
    ]
    if os.name == "nt":
        # Absolute paths: PyInstaller resolves --version-file against the spec
        # directory (--specpath), not cwd, so bare names break the build.
        command += [
            f"--icon={SOURCE_DIR / ICON_NAME}",
            f"--version-file={SOURCE_DIR / VERSION_FILE_NAME}",
        ]

    command += [f"--hidden-import={name}" for name in HIDDEN_IMPORTS]

    if module_available("arabic_reshaper"):
        command += ["--collect-data", "arabic_reshaper"]
    else:
        print(
            "warning: arabic_reshaper is not importable here; building without "
            "--collect-data arabic_reshaper (its runtime config data will not "
            "be bundled).",
            file=sys.stderr,
        )
    if module_available("bidi.algorithm"):
        command.append("--hidden-import=bidi.algorithm")
    else:
        print(
            "warning: bidi.algorithm is not importable here; building without "
            "--hidden-import=bidi.algorithm.",
            file=sys.stderr,
        )

    command += [
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
        f"--specpath={BUILD_DIR}",
        ENTRY_SCRIPT,
    ]
    return command


def output_tail(text: str, lines: int = TAIL_LINES, chars: int = 8000) -> str:
    """Last *lines* lines of *text*, capped at *chars* characters."""
    if not text.strip():
        return "<no output captured>"
    return "\n".join(text.splitlines()[-lines:])[-chars:]


def save_build_log(text: str) -> str:
    """Best-effort dump of the PyInstaller output; returns a note for messages."""
    try:
        BUILD_LOG.write_text(text, encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return f"(full PyInstaller log: {BUILD_LOG})"


def run_build(command: list[str]) -> int:
    """Run PyInstaller with cwd=source/. Returns 0 on success, non-zero on failure."""
    for directory in (DIST_DIR, BUILD_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    print(f"[1/3] building with PyInstaller (cwd={SOURCE_DIR}) ...")
    print(f"      command: {' '.join(command)}")
    print("      PyInstaller one-file builds take a few minutes; please wait ...")

    try:
        completed = subprocess.run(
            command,
            cwd=str(SOURCE_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=BUILD_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        partial = exc.stdout or ""
        if isinstance(partial, bytes):
            partial = partial.decode("utf-8", errors="replace")
        print(
            f"error: PyInstaller timed out after {BUILD_TIMEOUT_SECONDS} s; "
            f"last {TAIL_LINES} lines of output:",
            file=sys.stderr,
        )
        print(output_tail(partial), file=sys.stderr)
        print(save_build_log(partial), file=sys.stderr)
        return 1
    except OSError as exc:
        print(
            f"error: could not start PyInstaller via {sys.executable} -m PyInstaller: {exc}",
            file=sys.stderr,
        )
        return 1

    output = (completed.stdout or "") + (completed.stderr or "")
    log_note = save_build_log(output)

    if completed.returncode != 0:
        print(
            f"error: PyInstaller failed with exit code {completed.returncode}; "
            f"last {TAIL_LINES} lines of output:",
            file=sys.stderr,
        )
        print(output_tail(output), file=sys.stderr)
        if log_note:
            print(log_note, file=sys.stderr)
        return 1

    return 0


def built_exe_path() -> Path:
    """Where PyInstaller writes the GUI executable."""
    return DIST_DIR / (APP_NAME + (".exe" if os.name == "nt" else ""))


def verify_exe() -> Path | None:
    """Verify the freshly built exe and report its absolute path and size."""
    exe = built_exe_path()
    if not exe.is_file():
        print(
            f"error: PyInstaller reported success but the exe was not found at {exe}",
            file=sys.stderr,
        )
        return None
    size_mb = exe.stat().st_size / (1024 * 1024)
    print(f"[2/3] built exe: {exe.resolve()}")
    print(f"      size: {size_mb:.2f} MB")
    return exe


def terminate_process_tree(proc: subprocess.Popen) -> None:
    """Terminate *proc* and its children (PyInstaller's one-file child process)."""
    if proc.poll() is not None:
        return
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                capture_output=True,
                text=True,
                errors="replace",
            )
        except OSError:
            pass
        try:
            proc.wait(timeout=10)
            return
        except subprocess.TimeoutExpired:
            proc.kill()
            return
    else:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            proc.wait(timeout=10)
            return
        except (ProcessLookupError, PermissionError, subprocess.TimeoutExpired):
            pass
    try:
        proc.kill()
    except OSError:
        pass


def launch_check(exe: Path) -> int:
    """Start the exe once and confirm it is still alive after the launch window."""
    print(
        f"[3/3] launch check: starting the exe for {LAUNCH_TIMEOUT_SECONDS} s "
        "(the GUI is windowed; no console output is expected) ..."
    )
    popen_kwargs: dict[str, object] = {}
    if os.name == "nt":
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs["start_new_session"] = True

    try:
        proc = subprocess.Popen([str(exe)], **popen_kwargs)
    except OSError as exc:
        if getattr(exc, "winerror", None) == 740:
            print(
                "warning: Windows refused to start the exe without elevation "
                "(WinError 740). The exe carries a\n"
                "         requireAdministrator manifest (--uac-admin); re-run this "
                "tool from an elevated terminal\n"
                "         to exercise the launch check, or pass --no-run.",
                file=sys.stderr,
            )
            return 0
        print(f"warning: could not launch the exe: {exc}", file=sys.stderr)
        return 1

    try:
        returncode = proc.wait(timeout=LAUNCH_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        print(
            f"      still running after {LAUNCH_TIMEOUT_SECONDS} s -> start OK; "
            "terminating the process tree ..."
        )
        terminate_process_tree(proc)
        return 0

    print(f"      exe exited on its own within the launch window (exit code {returncode}).")
    if returncode == 0:
        return 0
    print(
        "error: the GUI exited with a non-zero code before the launch window "
        "ended; the build starts but crashes.",
        file=sys.stderr,
    )
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="build_gui.py",
        description=(
            "Build the Antigravity Patcher FA tkinter GUI as a one-file windowed "
            "PyInstaller executable, then smoke-launch it."
        ),
        epilog=(
            "The PyInstaller build takes a few minutes. Unless --no-run is given, "
            "the freshly built exe is then started once for 15 seconds to prove it "
            "launches, and its process tree is terminated afterwards."
        ),
    )
    parser.add_argument(
        "--no-run",
        action="store_true",
        help="build only; skip the 15-second launch check",
    )
    args = parser.parse_args(argv)

    print(f"repo root: {REPO_ROOT}")
    print(f"source   : {SOURCE_DIR}")

    missing = check_prerequisites()
    if missing:
        print(
            "error: cannot build the GUI exe; required file(s) are missing:",
            file=sys.stderr,
        )
        for path in missing:
            print(f"  - {path}", file=sys.stderr)
        return 2

    returncode = run_build(build_command())
    if returncode != 0:
        return returncode

    exe = verify_exe()
    if exe is None:
        return 1

    if args.no_run:
        print("[3/3] --no-run given; skipping the launch check.")
        return 0

    return launch_check(exe)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        sys.exit(130)
