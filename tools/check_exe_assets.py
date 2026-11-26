#!/usr/bin/env python3
"""Inspect a PyInstaller-packaged Antigravity Patcher executable for the
Persian (RTL) runtime assets it needs.

The Persian UI is only readable when the frozen application contains three
runtime dependencies:

    arabic_reshaper    - maps Arabic letters to their presentation forms
    bidi.algorithm     - reorders a line of text into terminal visual order
    patcher.utils.rtl  - the project glue that uses both of the above

PyInstaller bundles those modules inside the executable archive, so a plain
byte/UTF-8 search over the .exe file is enough to tell whether they are present.
Module names are stored as ASCII bytes in the PyInstaller table of contents, so
this works even though the marshalled code itself is compressed.

The script is intentionally dependency-free (stdlib only) and can be run on any
platform against an executable built for any platform.

Usage
-----
    python tools/check_exe_assets.py <path-to-exe>
    python tools/check_exe_assets.py <path-to-exe> --json-out evidence/report.json
    python tools/check_exe_assets.py <path-to-exe> --json          # JSON on stdout
    python tools/check_exe_assets.py <path-to-exe> --strict        # extras count too

Exit codes: 0 = all required assets found, 1 = a required asset is missing,
2 = the executable could not be read.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

# --- What we are looking for -------------------------------------------------
# ``required`` entries decide the pass/fail result; ``info`` entries are only
# reported (they document *why* the app may still work, or what an old build
# may lack), and ``--strict`` promotes them to required.
REQUIRED_ASSETS = [
    {
        "key": "arabic_reshaper",
        "label": "arabic_reshaper (Arabic shaping)",
        "patterns": [b"arabic_reshaper", "arabic_reshaper".encode("utf-8")],
    },
    {
        "key": "bidi",
        "label": "bidi.algorithm (Unicode bidi reordering)",
        "patterns": [b"bidi.algorithm", b"bidi"],
    },
    {
        "key": "patcher.utils.rtl",
        "label": "patcher.utils.rtl (project RTL glue)",
        "patterns": [b"patcher.utils.rtl"],
    },
]

INFO_ASSETS = [
    {
        "key": "packaging",
        "label": "packaging (version comparison for update checks)",
        "patterns": [b"packaging"],
    },
    {
        "key": "patcher.cli",
        "label": "patcher.cli (main application module)",
        "patterns": [b"patcher.cli"],
    },
    {
        "key": "patcher.utils.rtl_prefs",
        "label": "patcher.utils.rtl_prefs (saved visual/raw UI preference)",
        "patterns": [b"patcher.utils.rtl_prefs"],
    },
]

# First bytes of every PyInstaller CArchive ("MEI" + magic + package length).
PYINSTALLER_MAGIC = b"MEI\x0c\x0b\x0a\x0b\x0e"

# Ranges of Arabic *presentation forms* (U+FB50-FDFF, U+FE70-FEFC). A source
# tree with logical-order Persian text normally contains none of these; they
# only show up as regex-table endpoints inside the bundled libraries. The count
# is therefore informational, not a pass criterion.
PRESENTATION_FORM_RANGES = ((0xFB50, 0xFDFF), (0xFE70, 0xFEFC))
ARABIC_LETTER_RANGES = ((0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF))


def _count_occurrences(data: bytes, pattern: bytes) -> int:
    """Count non-overlapping occurrences of *pattern* in *data*."""
    if not pattern:
        return 0
    total = 0
    start = 0
    while True:
        index = data.find(pattern, start)
        if index < 0:
            return total
        total += 1
        start = index + len(pattern)


def _decode_for_stats(data: bytes) -> str:
    """Best-effort UTF-8 decode used only for character statistics."""
    return data.decode("utf-8", errors="ignore")


def _char_stats(data: bytes) -> dict:
    """Count Persian presentation forms and logical Arabic letters in the file."""
    text = _decode_for_stats(data)
    presentations = 0
    arabic_letters = 0
    for char in text:
        code = ord(char)
        if any(lo <= code <= hi for lo, hi in PRESENTATION_FORM_RANGES):
            presentations += 1
        elif any(lo <= code <= hi for lo, hi in ARABIC_LETTER_RANGES):
            arabic_letters += 1
    return {"presentation_form_chars": presentations, "arabic_letter_chars": arabic_letters}


def _check_asset(data: bytes, asset: dict) -> dict:
    """Return the result record for one expected module/asset."""
    # Prefer the most specific (longest) pattern for the reported pattern.
    best_pattern = max(asset["patterns"], key=len)
    occurrences = 0
    matched_pattern = None
    for pattern in asset["patterns"]:
        count = _count_occurrences(data, pattern)
        if count:
            occurrences = count
            matched_pattern = pattern
            break
    return {
        "key": asset["key"],
        "label": asset["label"],
        "found": bool(occurrences),
        "occurrences": occurrences,
        "pattern": (matched_pattern or best_pattern).decode("utf-8", errors="replace"),
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_executable(path: Path, strict: bool = False) -> dict:
    """Run every asset check against *path* and return a report dictionary."""
    data = path.read_bytes()

    required = [_check_asset(data, asset) for asset in REQUIRED_ASSETS]
    info = [_check_asset(data, asset) for asset in INFO_ASSETS]

    pyinstaller = _count_occurrences(data, PYINSTALLER_MAGIC) > 0
    stats = _char_stats(data)

    failures = [item["key"] for item in required if not item["found"]]
    if strict:
        failures += [item["key"] for item in info if not item["found"]]
    if strict and not pyinstaller:
        failures.append("pyinstaller_archive")

    result = "PASS" if not failures else "FAIL"
    return {
        "tool": "check_exe_assets",
        "exe": str(path),
        "size_bytes": len(data),
        "sha256": _sha256(path),
        "pyinstaller_archive": pyinstaller,
        "required": required,
        "info": info,
        "stats": stats,
        "strict": strict,
        "failures": failures,
        "result": result,
    }


def render_text(report: dict) -> str:
    """Human readable rendering of a report (ASCII only, safe in any console)."""
    lines = []
    lines.append("check_exe_assets: " + report["exe"])
    lines.append(f"  size    : {report['size_bytes']:,} bytes")
    lines.append(f"  sha256  : {report['sha256']}")
    lines.append(
        "  archive : "
        + ("PyInstaller CArchive (MEI magic found)" if report["pyinstaller_archive"]
           else "no PyInstaller MEI magic found")
    )
    lines.append("")
    lines.append("  REQUIRED")
    for item in report["required"]:
        mark = "PASS" if item["found"] else "FAIL"
        lines.append(f"    [{mark}] {item['key']:<20} occurrences={item['occurrences']}")
    lines.append("  INFO")
    for item in report["info"]:
        mark = "PASS" if item["found"] else "MISS"
        lines.append(f"    [{mark}] {item['key']:<20} occurrences={item['occurrences']}")
    lines.append("")
    stats = report["stats"]
    lines.append(
        f"  file stats: presentation-form chars={stats['presentation_form_chars']}, "
        f"logical Arabic chars={stats['arabic_letter_chars']}"
    )
    lines.append("  note: the Persian UI strings are shaped at runtime, so the exact "
                 "presentation forms need not be stored in the file.")
    lines.append("")
    if report["failures"]:
        lines.append("  missing required assets: " + ", ".join(report["failures"]))
    lines.append(f"RESULT: {report['result']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check that a built Antigravity Patcher exe bundles the "
                    "Persian RTL modules (arabic_reshaper, bidi, patcher.utils.rtl).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Exit codes:", 1)[-1].strip(),
    )
    parser.add_argument("exe", help="path to the executable to inspect")
    parser.add_argument("--json", action="store_true",
                        help="print the report as JSON instead of text")
    parser.add_argument("--json-out", metavar="PATH",
                        help="also write the JSON report to PATH")
    parser.add_argument("--strict", action="store_true",
                        help="treat informational assets (packaging, rtl_prefs, "
                             "PyInstaller magic) as required too")
    args = parser.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    exe_path = Path(args.exe).expanduser().resolve()
    if not exe_path.is_file():
        print(f"check_exe_assets: not a file: {exe_path}", file=sys.stderr)
        return 2
    try:
        report = inspect_executable(exe_path, strict=args.strict)
    except OSError as exc:
        print(f"check_exe_assets: cannot read {exe_path}: {exc}", file=sys.stderr)
        return 2

    if args.json_out:
        out_path = Path(args.json_out).expanduser()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"check_exe_assets: JSON report written to {out_path}")

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_text(report))

    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
