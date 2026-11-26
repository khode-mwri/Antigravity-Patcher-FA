"""Golden / round-trip tests for :func:`patcher.utils.rtl.visual`.

Terminals do not run the Unicode bidi algorithm and most of them do not shape
Arabic script at all, so every logical Persian line must be transformed into
Arabic *presentation forms* and reordered right-to-left before printing.  These
tests pin that contract down:

* golden output  — Persian input comes out fully shaped (no base letters left);
* round-trip     — the visual line can be mapped back to the logical string;
* idempotency    — rendering an already-visual line is a no-op;
* raw mode       — ``set_mode("raw")`` switches the transformation off;
* edge cases     — empty/``None``/Latin/multiline input stays sane.
"""

import collections
import re

import pytest

from patcher.utils import rtl

# Presentation forms: U+FB50..U+FDFF and U+FE70..U+FEFF.  Only shaped text has
# them, so their presence proves that the shaping/bidi path actually ran.
PRESENTATION_FORM_RE = re.compile("[\ufb50-\ufdfe\ufe70-\ufefc]")

# Base Arabic/Persian *letters* (digits, punctuation and the like are excluded
# on purpose: Persian numbers such as ۱۲ must survive unshaped).
BASE_LETTER_RE = re.compile(
    "[\u0621-\u063a\u0641-\u064a\u066e-\u06d3\u06d5"
    "\u06e5\u06e6\u06ee\u06ef\u06fa-\u06fc\u06fe\u06ff]"
)

# Pure Persian without ZWNJ/harakat: the round-trip must reproduce these
# byte-for-byte (the shaper normalises those marks away; covered separately).
PURE_PERSIAN = {
    "salam_donya": "سلام دنیا",
    "raf_ee_tahrim": "رفع تحریم",
    "choose_option": "گزینه را انتخاب کنید",
    "exit": "خروج",
    "memory": "حافظه",
    # Lam+alef becomes one ligature glyph: reversing must still restore "لا".
    "salam": "سلام",
}

# Persian strings that use ZWNJ (a rendering hint without a glyph of its own).
ZWNJ_PERSIAN = {
    "region_lock": "منطقه\u200cای",
    "unexpected_error": "خطای پیش\u200cبینی\u200cنشده",
}

# Mixed Persian/Latin/numbers/paths.  Bidi reorders the LTR runs as well, so a
# plain reversal is not a valid inverse here; only the character multiset is.
MIXED_PERSIAN = {
    "version": "نسخه v9.9.9 آماده است",
    "path": "مسیر: C:\\Users\\test\\main.js",
    "product": "پچ Antigravity IDE",
    "numbers": "گزینه ۱۲ از ۱۲",
}

GOLDEN_STRINGS = {**PURE_PERSIAN, **ZWNJ_PERSIAN, **MIXED_PERSIAN}

pytestmark = pytest.mark.skipif(
    not getattr(rtl, "AVAILABLE", False),
    reason=(
        "arabic-reshaper/python-bidi are not installed; "
        "run: python -m pip install -r source/requirements.txt"
    ),
)


def _build_reverse_shape_map():
    """Derive presentation-form -> base-letter map from arabic_reshaper tables.

    Building the table from the *installed* library instead of hard-coding it
    keeps the test correct across arabic-reshaper releases.
    """
    from arabic_reshaper import ligatures as shaper_ligatures
    from arabic_reshaper.arabic_reshaper import default_reshaper

    reverse = {}
    for base, forms in default_reshaper.letters.items():
        for form in forms:
            if form:
                reverse[form] = base

    # Multi-letter ligatures (lam+alef, Allah, ...) expand to more than one base
    # letter, so they must be part of the reverse table as sequences.
    for name, replacement in shaper_ligatures.LIGATURES:
        try:
            enabled = default_reshaper.configuration.getboolean(name)
        except Exception:  # pragma: no cover - defensive against library changes
            enabled = False
        if not enabled:
            continue
        match, forms = replacement
        if re.escape(match) != match:  # regex-based ligature: cannot expand
            continue
        for form in forms:
            if form:
                reverse[form] = match
    return reverse


@pytest.fixture(scope="module")
def reverse_map():
    try:
        return _build_reverse_shape_map()
    except Exception as exc:  # pragma: no cover - arabic_reshaper internals moved
        pytest.skip("cannot derive reverse shaping table: %s" % (exc,))


def _unshape(text, reverse_map):
    """Expand presentation forms back into base letters (ligatures included)."""
    return "".join(reverse_map.get(char, char) for char in text)


@pytest.mark.parametrize("text", GOLDEN_STRINGS.values(), ids=list(GOLDEN_STRINGS))
def test_golden_visual_output_is_fully_shaped(text):
    """visual() must emit presentation forms and leave no base letters behind."""
    visual = rtl.visual(text)
    assert PRESENTATION_FORM_RE.search(visual), "no shaped glyphs in %r" % (visual,)
    leftover = BASE_LETTER_RE.findall(visual)
    assert not leftover, "base Arabic letters left unshaped: %r (output %r)" % (
        leftover,
        visual,
    )


@pytest.mark.parametrize("text", GOLDEN_STRINGS.values(), ids=list(GOLDEN_STRINGS))
def test_visual_is_idempotent(text):
    """A line that already contains presentation forms must not change again."""
    once = rtl.visual(text)
    assert rtl.visual(once) == once


def test_visual_roundtrip_pure_persian(reverse_map):
    """Pure Persian: un-reverse then unshape gives the exact original string.

    The bidi reversal happens on the reshaped string, so it must be undone
    *before* expanding the presentation forms: one ligature glyph (e.g. lam+alef)
    stands for two base letters and would otherwise break the character order.
    """
    for name, text in PURE_PERSIAN.items():
        visual = rtl.visual(text)
        restored = _unshape(visual[::-1], reverse_map)
        assert restored == text, "%s: round-trip mismatch: %r != %r" % (
            name,
            restored,
            text,
        )


def test_visual_roundtrip_mixed_persian_multiset(reverse_map):
    """Mixed Persian/Latin: bidi reorders LTR runs, so compare multisets only."""
    for name, text in MIXED_PERSIAN.items():
        visual = rtl.visual(text)
        restored = _unshape(visual[::-1], reverse_map)
        assert collections.Counter(restored) == collections.Counter(text), (
            "%s: character multiset changed by render+reverse: %r vs %r"
            % (name, restored, text)
        )


def test_visual_roundtrip_pure_persian_with_zwnj_is_normalised(reverse_map):
    """ZWNJ has no glyph of its own; the shaper drops it (or keeps it as-is).

    Round-trip must therefore match the input modulo ZWNJ.
    """
    zwnj = "\u200c"
    for name, text in ZWNJ_PERSIAN.items():
        restored = _unshape(rtl.visual(text)[::-1], reverse_map)
        assert restored in (text, text.replace(zwnj, "")), (
            "%s: unexpected round-trip result %r (input %r)" % (name, restored, text)
        )


def test_raw_mode_returns_input_unchanged():
    """set_mode('raw') must disable shaping/bidi entirely (terminal does bidi)."""
    set_mode = getattr(rtl, "set_mode", None)
    get_mode = getattr(rtl, "get_mode", None)
    if set_mode is None or get_mode is None:
        pytest.skip("rtl.set_mode/get_mode API is not available in this build")

    previous = get_mode()
    try:
        set_mode("raw")
        assert get_mode() == "raw"
        for text in GOLDEN_STRINGS.values():
            assert rtl.visual(text) == text, "raw mode must not transform %r" % (text,)
        assert rtl.visual_line("سلام") == "سلام"
        assert rtl.visual("خط اول\nخط دوم") == "خط اول\nخط دوم"
    finally:
        set_mode(previous if previous in ("visual", "raw") else "visual")

    assert get_mode() == previous
    # ...and switching back restores the shaped rendering.
    assert PRESENTATION_FORM_RE.search(rtl.visual("سلام"))


def test_set_mode_rejects_unknown_mode_without_breaking_rendering():
    """An invalid mode must not raise nor corrupt the active mode."""
    set_mode = getattr(rtl, "set_mode", None)
    get_mode = getattr(rtl, "get_mode", None)
    if set_mode is None or get_mode is None:
        pytest.skip("rtl.set_mode/get_mode API is not available in this build")

    before = get_mode()
    result = set_mode("definitely-not-a-mode")
    assert result is not True, "unknown mode must not be reported as a success"
    assert get_mode() == before
    assert PRESENTATION_FORM_RE.search(rtl.visual("سلام"))


@pytest.mark.parametrize("value", ["", None], ids=["empty", "none"])
def test_visual_edge_inputs_pass_through(value):
    assert rtl.visual(value) == value


def test_visual_leaves_pure_latin_untouched():
    for text in ("Antigravity Patcher", "C:\\Users\\test\\main.js", "v9.9.9"):
        assert rtl.visual(text) == text


def test_visual_reorders_multiline_text_line_by_line():
    text = "خط اول\nخط دوم"
    visual = rtl.visual(text)
    assert visual != text
    parts = visual.split("\n")
    assert len(parts) == 2, "line count must be preserved"
    for part in parts:
        assert PRESENTATION_FORM_RE.search(part), "line was not shaped: %r" % (part,)
    assert rtl.visual(visual) == visual


def test_visual_keeps_ltr_tokens_intact():
    """Latin words/versions/paths inside Persian lines stay readable in order."""
    assert "Antigravity IDE" in rtl.visual("پچ Antigravity IDE")
    assert "v9.9.9" in rtl.visual("نسخه v9.9.9 آماده است")
    assert "C:\\Users\\test\\main.js" in rtl.visual("مسیر: C:\\Users\\test\\main.js")


def test_has_rtl_detects_persian_text():
    assert rtl.has_rtl("سلام")
    assert rtl.has_rtl("Antigravity پچر")
    assert not rtl.has_rtl("Antigravity Patcher")
    assert not rtl.has_rtl("")


def test_rtl_prefs_contract_is_read_only_safe():
    """The persisted-preference API exists and reading it never raises."""
    prefs = pytest.importorskip("patcher.utils.rtl_prefs")
    path = prefs.prefs_path()
    assert isinstance(path, str) and path
    assert path.replace("\\", "/").endswith("ui.json")

    # Read only: the suite must never overwrite the real user preferences.
    saved = prefs.load_mode()
    assert saved in (None, "visual", "raw")
