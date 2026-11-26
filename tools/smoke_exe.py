#!/usr/bin/env python3
"""End-to-end smoke test for the Antigravity Patcher *executable*.

What it does
------------
1. Builds a throw-away PyInstaller one-file executable from ``source/`` using
   the same hidden imports as the release workflow, but **without**
   ``--uac-admin`` so it can be started without a UAC prompt:

       python -m PyInstaller --onefile --console --name=ag_smoke --noupx \
           --hidden-import=packaging ... main.py

2. Runs that executable with ``stdin = "0\\n"`` (choose *Exit* in the menu) and
   ``SKIP_ELEVATION=1``, capturing stdout/stderr **to files** (never to a bare
   pipe) and reading them back as UTF-8, so the Persian output is not mangled.
   stdin itself is a short-lived pipe: a *file*-redirected stdin is swallowed
   by the ``chcp`` call inside ``setup_console()`` (see ``run_exe``).

3. Asserts the exe really works as a Persian terminal application:
   * exit code is 0;
   * the output contains ``Antigravity Patcher``;
   * in ``visual`` RTL mode the output contains Arabic *presentation forms*
     (U+FB50-FDFF / U+FE70-FEFC), i.e. arabic-reshaper + python-bidi actually
     ran inside the frozen exe; in ``raw`` mode it must contain logical Arabic
     letters instead and no presentation forms;
   * no Python traceback and none of the app's own "unexpected error" messages;
   * stdout is valid UTF-8 (no mojibake / replacement characters);
   * the bundled-exe asset check (``tools/check_exe_assets.py``) passes;
   * optionally: the first-run RTL calibration writes the pref file (--calibrate).

4. Prints a PASS/FAIL report and exits accordingly.

The build artifacts live under ``tools/_runtime/smoke/`` (never in ``source/``);
the input/output transcripts are kept there as evidence and are re-created on
every run, so the tool is repeatable.

Usage
-----
    python tools/smoke_exe.py                       # build + run (visual mode)
    python tools/smoke_exe.py --mode raw            # verify raw RTL mode
    python tools/smoke_exe.py --calibrate           # first-run calibration path
    python tools/smoke_exe.py --json-out evidence/smoke_report.json
    python tools/smoke_exe.py --no-build --exe path/to/exe   # test a given exe

Exit codes: 0 = PASS, 1 = a smoke assertion failed, 2 = build/run could not start.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TOOLS_DIR.parent
SOURCE_DIR = PROJECT_ROOT / "source"
RUNTIME_DIR = TOOLS_DIR / "_runtime" / "smoke"

EXE_NAME = "ag_smoke"

# Same hidden imports as .github/workflows/release.yml / source/build.txt.
HIDDEN_IMPORTS = [
    "packaging",
    "packaging.version",
    "packaging.specifiers",
    "packaging.requirements",
]

PRESENTATION_FORM_RANGES = ((0xFB50, 0xFDFF), (0xFE70, 0xFEFC))
ARABIC_RANGES = ((0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF))
ANSI_RE = re.compile(r"\x1b(?:\[[0-9;?]*[a-zA-Z]|\]8;;.*?(?:\x1b\\|\x07))")


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def count_ranges(text: str, ranges) -> int:
    """Count characters whose code point falls inside any of *ranges*."""
    return sum(
        1
        for char in text
        if any(lo <= ord(char) <= hi for lo, hi in ranges)
    )


# The application renders Persian through patcher.utils.rtl, so an error string
# printed in visual mode is stored as *presentation forms* and the logical
# phrase below will not match it. When the shaping libraries are importable we
# also test for the reshaped/reordered variant.
try:  # pragma: no cover - depends on the machine running the tool
    from arabic_reshaper import reshape as _reshape  # type: ignore
    from bidi.algorithm import get_display as _get_display  # type: ignore
    _SHAPING_AVAILABLE = True
except Exception:  # libraries are optional for the tool itself
    _reshape = None
    _get_display = None
    _SHAPING_AVAILABLE = False


def visual_form(text: str) -> str | None:
    """Return the shaped/bidi-reordered form of *text*, or None if unavailable."""
    if not _SHAPING_AVAILABLE:
        return None
    try:
        return _get_display(_reshape(text), base_dir="R")
    except Exception:
        return None


def contains_persian(haystack: str, phrase: str) -> bool:
    """True when *phrase* appears in *haystack* either raw or RTL-visualized."""
    if phrase in haystack:
        return True
    shaped = visual_form(phrase)
    return bool(shaped and shaped in haystack)


def source_snapshot() -> dict:
    """Hash the current source tree so evidence states exactly what was tested."""
    digest = hashlib.sha256()
    files = []
    newest = 0.0
    for path in sorted(SOURCE_DIR.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        raw = path.read_bytes()
        rel = path.relative_to(SOURCE_DIR).as_posix()
        files.append({"path": rel, "size": len(raw),
                      "sha256": hashlib.sha256(raw).hexdigest()})
        digest.update(rel.encode("utf-8") + b"\0" + raw)
        newest = max(newest, path.stat().st_mtime)
    return {
        "tree_sha256": digest.hexdigest(),
        "file_count": len(files),
        "newest_mtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(newest)) if newest else None,
        "files": files,
    }


def app_version_from_output(text: str) -> str | None:
    match = re.search(r"Antigravity Patcher\s+v(\d+\.\d+\.\d+)", text)
    if match:
        return match.group(1)
    match = re.search(r"\bv(\d+\.\d+\.\d+)\b", text)
    return match.group(1) if match else None


def tail(text: str, lines: int = 30, chars: int = 4000) -> str:
    """Last *lines* lines of *text*, capped at *chars* characters."""
    return "\n".join(text.splitlines()[-lines:])[-chars:]


# --------------------------------------------------------------------------- #
# build
# --------------------------------------------------------------------------- #
def build_exe(runtime_dir: Path, fresh: bool = True) -> tuple[Path | None, dict]:
    """Build the throw-away one-file exe. Returns (exe path or None, build info)."""
    dist_dir = runtime_dir / "dist"
    work_dir = runtime_dir / "build"
    spec_dir = runtime_dir / "spec"
    log_path = runtime_dir / "build.log"
    runtime_dir.mkdir(parents=True, exist_ok=True)

    if fresh:
        for directory in (dist_dir, work_dir, spec_dir):
            shutil.rmtree(directory, ignore_errors=True)

    command = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--console",
        f"--name={EXE_NAME}",
        "--noupx",
        "--clean",
        "--noconfirm",
        "--log-level=WARN",
        f"--distpath={dist_dir}",
        f"--workpath={work_dir}",
        f"--specpath={spec_dir}",
        *[f"--hidden-import={name}" for name in HIDDEN_IMPORTS],
        "main.py",
    ]
    started = time.time()
    info = {
        "command": " ".join(str(part) for part in command),
        "cwd": str(SOURCE_DIR),
        "log": str(log_path),
        "returncode": None,
        "duration_sec": None,
        "output_tail": "",
        "exe": None,
    }
    if not (SOURCE_DIR / "main.py").is_file():
        info["output_tail"] = f"source/main.py not found under {SOURCE_DIR}"
        return None, info

    print("[1/3] building exe (PyInstaller onefile, no --uac-admin) ...")
    try:
        completed = subprocess.run(
            command,
            cwd=str(SOURCE_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=900,
        )
    except subprocess.TimeoutExpired:
        info["output_tail"] = "PyInstaller build timed out after 900 s"
        return None, info
    except OSError as exc:
        info["output_tail"] = f"could not start PyInstaller: {exc}"
        return None, info

    output = (completed.stdout or "") + (completed.stderr or "")
    log_path.write_text(output, encoding="utf-8", errors="replace")
    info["returncode"] = completed.returncode
    info["duration_sec"] = round(time.time() - started, 1)
    info["output_tail"] = tail(output)

    exe = dist_dir / (EXE_NAME + (".exe" if os.name == "nt" else ""))
    info["exe"] = str(exe)
    if completed.returncode != 0 or not exe.is_file():
        print("      build FAILED (see build.log)")
        return None, info
    print(f"      built {exe} ({exe.stat().st_size:,} bytes, "
          f"{info['duration_sec']}s)")
    return exe, info


# --------------------------------------------------------------------------- #
# run + assertions
# --------------------------------------------------------------------------- #
def run_exe(exe: Path, runtime_dir: Path, mode: str, stdin_text: str,
            calibrate: bool, timeout: int) -> dict:
    """Execute the exe with file-backed stdio and return raw run data."""
    run_dir = runtime_dir / "run"
    shutil.rmtree(run_dir, ignore_errors=True)
    run_dir.mkdir(parents=True, exist_ok=True)
    stdin_path = run_dir / "stdin.txt"
    stdout_path = run_dir / "stdout.txt"
    stderr_path = run_dir / "stderr.txt"
    sandbox_appdata = run_dir / "appdata"
    sandbox_appdata.mkdir(parents=True, exist_ok=True)

    stdin_path.write_text(stdin_text, encoding="utf-8", newline="\n")

    env = os.environ.copy()
    env["SKIP_ELEVATION"] = "1"
    # Keep the user's real %APPDATA%\Antigravity-Patcher\ui.json untouched.
    env["APPDATA"] = str(sandbox_appdata)
    env.pop("AG_PATCHER_TERMINAL", None)
    if calibrate:
        env.pop("AG_PATCHER_RTL", None)
    else:
        env["AG_PATCHER_RTL"] = mode

    started = time.time()
    timed_out = False
    returncode = None
    # stdin is fed through a *pipe* on purpose. source/patcher/utils/console.py
    # calls `os.system("chcp 65001 >nul")` while starting up, and on Windows that
    # consumes a stdin handle that was redirected from a *file* (the app then
    # sees EOF at its first input() prompt). A pipe is immune to that, while
    # stdout/stderr still go to real files so the UTF-8 output is captured
    # verbatim instead of being re-encoded by a pipe.
    stdin_bytes = stdin_text.encode("utf-8")
    try:
        with stdout_path.open("wb") as stdout_fh, \
                stderr_path.open("wb") as stderr_fh:
            completed = subprocess.run(
                [str(exe)],
                input=stdin_bytes,
                stdout=stdout_fh,
                stderr=stderr_fh,
                env=env,
                cwd=str(run_dir),
                timeout=timeout,
            )
            returncode = completed.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
    except OSError as exc:
        return {
            "error": f"could not start exe: {exc}",
            "returncode": None, "timed_out": False,
            "duration_sec": round(time.time() - started, 2),
            "stdin": str(stdin_path), "stdout": str(stdout_path),
            "stderr": str(stderr_path), "env_overrides": {
                "SKIP_ELEVATION": "1",
                "AG_PATCHER_RTL": env.get("AG_PATCHER_RTL"),
                "APPDATA": str(sandbox_appdata),
            },
            "stdin_mode": "pipe",
            "stdout_bytes": 0, "stderr_bytes": 0,
        }

    stdout_bytes = stdout_path.read_bytes()
    stderr_bytes = stderr_path.read_bytes()
    try:
        stdout_text = stdout_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        stdout_text = stdout_bytes.decode("utf-8", errors="replace")
        stdout_text = f"<invalid utf-8 at byte {exc.start}>\n" + stdout_text
    stderr_text = stderr_bytes.decode("utf-8", errors="replace")

    pref_path = sandbox_appdata / "Antigravity-Patcher" / "ui.json"
    pref_content = None
    if pref_path.is_file():
        try:
            pref_content = pref_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            pref_content = "<unreadable>"

    return {
        "error": None,
        "timed_out": timed_out,
        "returncode": returncode,
        "duration_sec": round(time.time() - started, 2),
        "stdin": str(stdin_path),
        "stdin_mode": "pipe",
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        "stdout_bytes": len(stdout_bytes),
        "stderr_bytes": len(stderr_bytes),
        "stdout_utf8_strict": not stdout_text.startswith("<invalid utf-8"),
        "stdout_text": stdout_text,
        "stderr_text": stderr_text,
        "prefs_file": str(pref_path) if pref_path.is_file() else None,
        "prefs_content": pref_content,
        "env_overrides": {
            "SKIP_ELEVATION": "1",
            "AG_PATCHER_RTL": env.get("AG_PATCHER_RTL"),
            "APPDATA": str(sandbox_appdata),
        },
    }


def evaluate(run: dict, mode: str, calibrate: bool) -> list[dict]:
    """Turn the raw run data into a list of named pass/fail checks."""
    checks: list[dict] = []

    def add(name: str, ok: bool, detail: str, required: bool = True) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail,
                       "required": required})

    if run.get("error"):
        add("exe_started", False, run["error"])
        return checks

    stdout = strip_ansi(run.get("stdout_text") or "")
    stderr = strip_ansi(run.get("stderr_text") or "")
    combined = stdout + "\n" + stderr
    presentations = count_ranges(stdout, PRESENTATION_FORM_RANGES)
    arabic_letters = count_ranges(stdout, ARABIC_RANGES)
    replacements = combined.count("\ufffd")

    add("exit_code_zero",
        run["returncode"] == 0 and not run["timed_out"],
        f"returncode={run['returncode']} timed_out={run['timed_out']} "
        f"duration={run['duration_sec']}s")
    add("stdout_utf8",
        bool(run.get("stdout_utf8_strict")),
        "stdout decoded as strict UTF-8" if run.get("stdout_utf8_strict")
        else "stdout is not valid UTF-8 (mojibake risk)")
    add("no_replacement_chars",
        replacements == 0,
        f"U+FFFD replacement characters in output: {replacements}")
    add("banner_app_name",
        "Antigravity Patcher" in stdout,
        "'Antigravity Patcher' banner title " +
        ("found" if "Antigravity Patcher" in stdout else "MISSING"))
    add("menu_rendered",
        "[0]" in stdout and "[1]" in stdout,
        "menu rows [0]/[1] " +
        ("found" if ("[0]" in stdout and "[1]" in stdout) else "MISSING"))
    traceback_found = ("Traceback (most recent call last)" in combined
                       or "Failed to execute script" in combined)
    add("no_traceback", not traceback_found,
        "python traceback " + ("found" if traceback_found else "absent"))
    unexpected_error = (
        contains_persian(stdout, "خطای پیش‌بینی‌نشده")
        or "EOF when reading a line" in combined
        or "EOFError" in combined
    )
    add("no_unexpected_error", not unexpected_error,
        "application error handler " +
        ("was triggered" if unexpected_error else "not triggered"))
    elevation_warning = contains_persian(stdout, "دسترسی مدیریتی دریافت نشد")
    add("no_failed_elevation", not elevation_warning,
        "elevation warning " + ("present" if elevation_warning else "absent"))

    if calibrate:
        add("calibration_pref_saved",
            bool(run.get("prefs_content")) and '"rtl_mode"' in (run.get("prefs_content") or ""),
            f"prefs file={run.get('prefs_file')} content={run.get('prefs_content')!r}")
        add("persian_rendered",
            presentations > 0 or arabic_letters > 0,
            f"presentation_forms={presentations}, arabic_letters={arabic_letters}")
    elif mode == "visual":
        add("persian_presentation_forms",
            presentations > 0,
            f"Arabic presentation forms (U+FB50-FDFF/U+FE70-FEFC) in stdout: {presentations} "
            f"(logical Arabic letters: {arabic_letters})")
    else:  # raw mode
        add("persian_raw_letters",
            arabic_letters > 0,
            f"logical Arabic letters in stdout: {arabic_letters}")
        add("raw_mode_not_reshaped",
            presentations == 0,
            f"presentation forms in raw-mode output: {presentations}")

    return checks


def run_asset_check(exe: Path) -> dict:
    """Run tools/check_exe_assets.py against the built exe and return its report."""
    checker = TOOLS_DIR / "check_exe_assets.py"
    json_out = RUNTIME_DIR / "asset_check.json"
    try:
        completed = subprocess.run(
            [sys.executable, str(checker), str(exe), "--json",
             "--json-out", str(json_out)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=180,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        return {"result": "FAIL", "error": str(exc), "exit_code": None}
    report = {}
    if json_out.is_file():
        try:
            report = json.loads(json_out.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            report = {}
    report["exit_code"] = completed.returncode
    report.setdefault("result", "PASS" if completed.returncode == 0 else "FAIL")
    return report


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def render(report: dict) -> str:
    lines = []
    lines.append("smoke_exe: " + report["exe"])
    lines.append(f"  mode        : {report['mode_value']}"
                 + ("  (first-run calibration path)" if report["calibrate"] else ""))
    lines.append(f"  stdin       : {report['run'].get('stdin')} -> "
                 f"{report['run'].get('stdin_text', '')!r}")
    lines.append(f"  stdout file : {report['run'].get('stdout')}")
    lines.append(f"  stderr file : {report['run'].get('stderr')}")
    lines.append(f"  exit code   : {report['run'].get('returncode')}")
    lines.append(f"  duration    : {report['run'].get('duration_sec')}s")
    lines.append("  checks:")
    for check in report["checks"]:
        mark = "PASS" if check["ok"] else "FAIL"
        tag = "" if check["required"] else " (optional)"
        lines.append(f"    [{mark}] {check['name']}{tag}: {check['detail']}")
    if report.get("assets", {}).get("result"):
        lines.append(f"  bundled assets: {report['assets']['result']}")
    lines.append(f"RESULT: {report['result']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a non-elevated one-file exe from source/ and smoke-test "
                    "its Persian terminal output.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--mode", choices=("visual", "raw"), default="visual",
                        help="RTL rendering mode passed via AG_PATCHER_RTL "
                             "(default: visual)")
    parser.add_argument("--stdin-text", default=None,
                        help="text fed to the exe on stdin (default: '0\\n', or "
                             "'y\\n0\\n' with --calibrate)")
    parser.add_argument("--calibrate", action="store_true",
                        help="do not preset AG_PATCHER_RTL; answer the first-run "
                             "calibration with the stdin text (use 'y\\n0\\n') and "
                             "check that the preference file is written")
    parser.add_argument("--timeout", type=int, default=180,
                        help="seconds to wait for the exe (default: 180)")
    parser.add_argument("--no-build", action="store_true",
                        help="skip PyInstaller and reuse the last built exe")
    parser.add_argument("--exe", help="run this executable instead of building one")
    parser.add_argument("--json-out", metavar="PATH",
                        help="write the JSON report to PATH")
    parser.add_argument("--keep", action="store_true",
                        help="keep all runtime artifacts (they are kept anyway; "
                             "flag exists for symmetry with future cleanup)")
    args = parser.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if args.calibrate and args.stdin_text is None:
        args.stdin_text = "y\n0\n"
    if args.stdin_text is None:
        args.stdin_text = "0\n"

    report: dict = {
        "tool": "smoke_exe",
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "project_root": str(PROJECT_ROOT),
        "source_snapshot": source_snapshot(),
        "mode_value": args.mode,
        "calibrate": args.calibrate,
        "build": None,
        "run": {},
        "checks": [],
        "assets": {},
        "result": "FAIL",
    }

    # --- exe: build or use the provided one --------------------------------
    if args.exe:
        exe = Path(args.exe).expanduser().resolve()
        if not exe.is_file():
            print(f"smoke_exe: not a file: {exe}", file=sys.stderr)
            return 2
        report["exe"] = str(exe)
        report["build"] = {"command": None, "note": "--exe given, no build"}
        print(f"[1/3] using existing exe: {exe}")
    elif args.no_build:
        exe = RUNTIME_DIR / "dist" / (EXE_NAME + (".exe" if os.name == "nt" else ""))
        if not exe.is_file():
            print(f"smoke_exe: --no-build but {exe} does not exist", file=sys.stderr)
            return 2
        report["exe"] = str(exe)
        report["build"] = {"command": None, "note": "--no-build, reused exe"}
        print(f"[1/3] reusing exe: {exe}")
    else:
        exe, build_info = build_exe(RUNTIME_DIR)
        report["build"] = build_info
        if exe is None:
            report["result"] = "BUILD_FAILED"
            report["checks"] = [{
                "name": "pyinstaller_build", "ok": False, "required": True,
                "detail": "PyInstaller failed; see " + str(build_info.get("log")),
            }]
            print(render(report))
            if args.json_out:
                Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
                Path(args.json_out).write_text(
                    json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
            return 2
        report["exe"] = str(exe)

    # Fingerprint the executable under test so the report is self-contained.
    try:
        report["exe_sha256"] = hashlib.sha256(exe.read_bytes()).hexdigest()
        report["exe_size_bytes"] = exe.stat().st_size
    except OSError as exc:
        report["exe_sha256"] = None
        report["exe_size_bytes"] = None
        report["exe_hash_error"] = str(exc)

    # --- run ---------------------------------------------------------------
    print(f"[2/3] running exe (mode={args.mode}, calibrate={args.calibrate}, "
          f"stdin={args.stdin_text!r}) ...")
    run = run_exe(exe, RUNTIME_DIR, args.mode, args.stdin_text,
                  args.calibrate, args.timeout)
    run["stdin_text"] = args.stdin_text
    report["run"] = run
    if run.get("error"):
        print("      " + run["error"])

    # --- evaluate ----------------------------------------------------------
    checks = evaluate(run, args.mode, args.calibrate)
    report["checks"] = checks

    print("[3/3] checking bundled RTL assets ...")
    assets = run_asset_check(exe)
    report["assets"] = {
        "result": assets.get("result"),
        "exit_code": assets.get("exit_code"),
        "required": [
            {"key": item.get("key"), "found": item.get("found")}
            for item in (assets.get("required") or [])
        ],
        "info": [
            {"key": item.get("key"), "found": item.get("found")}
            for item in (assets.get("info") or [])
        ],
        "error": assets.get("error"),
    }
    if assets.get("result") != "PASS":
        checks.append({
            "name": "bundled_rtl_assets", "ok": False, "required": True,
            "detail": f"check_exe_assets exited {assets.get('exit_code')}: "
                      f"{assets.get('error') or assets.get('failures') or 'missing modules'}",
        })
    else:
        checks.append({
            "name": "bundled_rtl_assets", "ok": True, "required": True,
            "detail": "arabic_reshaper, bidi.algorithm and patcher.utils.rtl "
                      "are present in the exe",
        })

    # version + timing info
    report["app_version"] = app_version_from_output(strip_ansi(run.get("stdout_text") or ""))
    report["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    failed = [check for check in checks if check["required"] and not check["ok"]]
    report["result"] = "PASS" if not failed else "FAIL"

    if args.json_out:
        out_path = Path(args.json_out).expanduser()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
        print(f"smoke_exe: JSON report written to {out_path}")

    print("")
    print(render(report))
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
