"""Static checks over the ``source/`` tree.

Two classes of regressions are caught here:

1. **Encoding hygiene** — every text file in ``source/`` is valid UTF-8 and
   Persian text uses the Persian letters ی (U+06CC) / ک (U+06A9), never the
   Arabic look-alikes ي (U+064A) / ك (U+0643).
2. **Rendering coverage** — every Persian string literal in the source tree is
   accepted by :func:`patcher.utils.rtl.visual`, i.e. the UI rendering path can
   shape it into Arabic presentation forms instead of printing disconnected,
   reversed letters.

The rendering check works on the AST, so it sees the *actual* strings (after
escape processing) and reports ``file:line`` for every failure.
"""

import ast
import re
from pathlib import Path

import pytest

from patcher.utils import rtl

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = REPO_ROOT / "source"

PRESENTATION_FORM_RE = re.compile("[\ufb50-\ufdfe\ufe70-\ufefc]")

# Base Arabic/Persian letters: used as a fallback when arabic_reshaper's own
# letter table is unavailable.
BASE_LETTER_RE = re.compile(
    "[\u0621-\u063a\u0641-\u064a\u066e-\u06d3\u06d5"
    "\u06e5\u06e6\u06ee\u06ef\u06fa-\u06fc\u06fe\u06ff]"
)

ARABIC_YEH = "\u064a"
ARABIC_KAF = "\u0643"

# Text-like files whose encoding is checked. Binary assets (icon.ico, *.exe,
# __pycache__/*.pyc, ...) are intentionally excluded.
TEXT_SUFFIXES = frozenset(
    {".py", ".txt", ".md", ".json", ".yml", ".yaml", ".ini", ".cfg"}
)
# Build artifacts may exist next to the sources after a local PyInstaller build;
# they are not source files and must not be scanned.
SKIP_DIR_NAMES = frozenset({"__pycache__", "build", "dist", ".mypy_cache"})

pytestmark = pytest.mark.skipif(
    not getattr(rtl, "AVAILABLE", False),
    reason=(
        "arabic-reshaper/python-bidi are not installed; "
        "run: python -m pip install -r source/requirements.txt"
    ),
)


def _relative(path):
    try:
        return path.relative_to(REPO_ROOT)
    except ValueError:  # pragma: no cover - path outside the repository
        return path


def _iter_files(suffixes):
    for path in sorted(SOURCE_DIR.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.suffix.lower() in suffixes:
            yield path


def _read_text(path):
    """Decode a source file, tolerating a UTF-8 BOM (Python accepts one)."""
    return path.read_bytes().decode("utf-8-sig")


def _reshapable_letters():
    """Letters the installed arabic_reshaper knows how to shape (or None)."""
    try:
        from arabic_reshaper.arabic_reshaper import default_reshaper
    except Exception:  # pragma: no cover - library internals changed
        return None
    return frozenset(default_reshaper.letters)


def _iter_python_string_literals():
    """Yield ``(path, line, value)`` for every string constant in source/."""
    for path in _iter_files({".py"}):
        tree = ast.parse(_read_text(path), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                yield path, node.lineno, node.value


def test_source_text_files_are_valid_utf8():
    assert (SOURCE_DIR / "main.py").is_file(), "source/main.py is missing"
    assert (SOURCE_DIR / "patcher" / "cli.py").is_file(), "source/patcher/cli.py is missing"

    failures = []
    for path in _iter_files(TEXT_SUFFIXES):
        try:
            path.read_bytes().decode("utf-8")
        except UnicodeDecodeError as exc:
            failures.append("%s: %s" % (_relative(path), exc))
    assert not failures, "source files are not valid UTF-8:\n" + "\n".join(failures)


def test_source_uses_persian_letters_not_arabic_variants():
    """Persian text must use ی/ک (U+06CC/U+06A9), not Arabic ي/ك."""
    offenders = []
    for path in _iter_files(TEXT_SUFFIXES):
        for lineno, line in enumerate(_read_text(path).splitlines(), 1):
            if ARABIC_YEH in line or ARABIC_KAF in line:
                offenders.append(
                    "%s:%d: %s" % (_relative(path), lineno, line.strip()[:100])
                )
    assert not offenders, (
        "Arabic look-alike letters found (use Persian ی U+06CC / ک U+06A9):\n"
        + "\n".join(offenders)
    )


def test_every_persian_source_string_is_shapeable():
    """All Persian string literals must render into presentation forms."""
    reshapable = _reshapable_letters()

    def contains_persian(text):
        if reshapable is not None:
            return bool(reshapable.intersection(text))
        return bool(BASE_LETTER_RE.search(text))

    checked = 0
    failures = []
    for path, lineno, value in _iter_python_string_literals():
        if not contains_persian(value):
            continue
        checked += 1
        shaped = rtl.visual(value)
        if not PRESENTATION_FORM_RE.search(shaped):
            failures.append(
                "%s:%d: visual() produced no presentation forms for %r (got %r)"
                % (_relative(path), lineno, value[:80], shaped[:80])
            )
            continue
        # A logical-order string must be *fully* shaped.  (Strings that already
        # contain presentation forms — e.g. documentation examples — are
        # returned unchanged by design and only need to keep shaping glyphs.)
        already_visual = bool(PRESENTATION_FORM_RE.search(value))
        if not already_visual and contains_persian(shaped):
            failures.append(
                "%s:%d: base letters left unshaped: %r (got %r)"
                % (_relative(path), lineno, value[:80], shaped[:80])
            )

    assert checked >= 100, (
        "only %d Persian strings found in source/; the AST scan looks broken" % checked
    )
    assert not failures, "Persian strings without a readable render path:\n" + "\n".join(
        failures
    )
