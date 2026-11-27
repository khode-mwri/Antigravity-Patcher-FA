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

The tail of the file covers the mode-selection policy around rendering:
``rtl_prefs.needs_calibration()`` and ``main._setup_rtl`` / ``main._calibrate_rtl``
(CLI flag > environment > saved choice > calibration, with an explicit
``--rtl auto`` forcing a fresh calibration).
"""

import collections
import os
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


# ─── Mode selection: needs_calibration() and main._setup_rtl ─────────────────
#
# Everything below runs against a throw-away APPDATA / HOME, so the user's real
# ui.json is never read or written.


@pytest.fixture
def prefs_env(tmp_path, monkeypatch):
    """Point rtl_prefs at a temporary preferences directory."""
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    prefs = pytest.importorskip("patcher.utils.rtl_prefs")
    return prefs


@pytest.fixture
def rtl_env(monkeypatch):
    """Keep AG_PATCHER_RTL out of the picture unless a test sets it itself."""
    monkeypatch.delenv("AG_PATCHER_RTL", raising=False)


@pytest.fixture
def calib_recorder(monkeypatch):
    """Replace main._calibrate_rtl with a recorder returning a fixed mode."""
    main_module = pytest.importorskip("main")
    calls = []
    result = {"mode": "visual"}

    def fake_calibrate():
        calls.append(True)
        return result["mode"]

    monkeypatch.setattr(main_module, "_calibrate_rtl", fake_calibrate, raising=False)
    return main_module, calls, result


def _mode_after_setup(main_module, requested):
    """Run _setup_rtl and return (rtl mode, console render mode)."""
    from patcher.utils import console

    main_module._setup_rtl(requested)
    return rtl.get_mode(), console.RENDER_MODE


def test_needs_calibration_true_without_saved_file(prefs_env, rtl_env):
    assert prefs_env.needs_calibration() is True
    assert prefs_env.load_mode() is None


@pytest.mark.parametrize("mode", ["visual", "raw"])
def test_needs_calibration_false_after_save(prefs_env, rtl_env, mode):
    assert prefs_env.save_mode(mode) is True
    assert prefs_env.needs_calibration() is False
    assert prefs_env.load_mode() == mode


def _write_prefs(prefs, content):
    """Write raw preference-file content, creating the directory if needed."""
    path = prefs.prefs_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


@pytest.mark.parametrize(
    "content",
    [
        "",
        "not json at all",
        "[]",
        '{"rtl_mode": ""}',
        '{"rtl_mode": "sideways"}',
        '{"other_key": 1}',
        "null",
    ],
    ids=["empty_file", "garbage", "json_list", "empty_mode", "unknown_mode",
         "missing_key", "null_json"],
)
def test_needs_calibration_true_for_invalid_preferences(prefs_env, rtl_env, content):
    """Empty / malformed / out-of-range preferences must request calibration."""
    _write_prefs(prefs_env, content)
    assert prefs_env.needs_calibration() is True


def test_needs_calibration_is_consistent_with_load_mode(prefs_env, rtl_env):
    """The helper must never disagree with load_mode()'s contract."""
    assert prefs_env.needs_calibration() == (prefs_env.load_mode() is None)
    prefs_env.save_mode("raw")
    assert prefs_env.needs_calibration() == (prefs_env.load_mode() is None)


def test_setup_rtl_cli_flag_beats_saved_choice(prefs_env, rtl_env, calib_recorder):
    """An explicit --rtl visual/raw wins over the saved mode and skips calibration."""
    main_module, calls, _ = calib_recorder
    prefs_env.save_mode("raw")
    assert _mode_after_setup(main_module, "visual") == ("visual", "visual")
    assert calls == [], "calibration must not run when the CLI flag is explicit"


def test_setup_rtl_env_mode_beats_saved_choice(prefs_env, rtl_env, calib_recorder, monkeypatch):
    main_module, calls, _ = calib_recorder
    prefs_env.save_mode("visual")
    monkeypatch.setenv("AG_PATCHER_RTL", "raw")
    assert _mode_after_setup(main_module, None) == ("raw", "raw")
    assert calls == []


def test_setup_rtl_uses_saved_choice_without_calibration(prefs_env, rtl_env, calib_recorder):
    """A valid saved mode is applied as-is; the user is not asked again."""
    main_module, calls, _ = calib_recorder
    prefs_env.save_mode("raw")
    assert _mode_after_setup(main_module, None) == ("raw", "raw")
    assert calls == []


def test_setup_rtl_calibrates_when_no_saved_mode(prefs_env, rtl_env, calib_recorder):
    main_module, calls, result = calib_recorder
    result["mode"] = "raw"
    assert _mode_after_setup(main_module, None) == ("raw", "raw")
    assert calls == [True], "calibration must run when nothing is saved"
    assert prefs_env.load_mode() == "raw", "the calibrated mode must be persisted"


def test_setup_rtl_calibrates_when_saved_preference_is_invalid(prefs_env, rtl_env, calib_recorder):
    """An old/corrupt ui.json is treated as 'no saved mode' and re-calibrated."""
    main_module, calls, result = calib_recorder
    result["mode"] = "raw"
    _write_prefs(prefs_env, '{"rtl_mode": "broken"}')
    assert _mode_after_setup(main_module, None) == ("raw", "raw")
    assert calls == [True]
    assert prefs_env.load_mode() == "raw"


def test_setup_rtl_auto_forces_calibration_even_with_saved_mode(
    prefs_env, rtl_env, calib_recorder
):
    """--rtl auto must re-run calibration despite a saved (stale) mode."""
    main_module, calls, result = calib_recorder
    prefs_env.save_mode("raw")  # e.g. saved on another machine/terminal
    result["mode"] = "visual"
    assert _mode_after_setup(main_module, "auto") == ("visual", "visual")
    assert calls == [True], "--rtl auto must always ask"
    assert prefs_env.load_mode() == "visual", "the new choice must replace the old one"


def test_setup_rtl_auto_outranks_environment_mode(
    prefs_env, rtl_env, calib_recorder, monkeypatch
):
    """An explicit CLI 'auto' is stronger than AG_PATCHER_RTL=raw."""
    main_module, calls, result = calib_recorder
    prefs_env.save_mode("raw")
    monkeypatch.setenv("AG_PATCHER_RTL", "raw")
    result["mode"] = "visual"
    assert _mode_after_setup(main_module, "auto") == ("visual", "visual")
    assert calls == [True]


def test_setup_rtl_env_auto_forces_calibration(prefs_env, rtl_env, calib_recorder, monkeypatch):
    """AG_PATCHER_RTL=auto also means 'calibrate now' (inherited by relaunches)."""
    main_module, calls, result = calib_recorder
    prefs_env.save_mode("visual")
    monkeypatch.setenv("AG_PATCHER_RTL", "auto")
    result["mode"] = "raw"
    assert _mode_after_setup(main_module, None) == ("raw", "raw")
    assert calls == [True]
    assert prefs_env.load_mode() == "raw"


def test_calibrate_rtl_shows_sample_in_both_modes_before_choosing(
    rtl_env, monkeypatch, capsys
):
    """Calibration must explain the two-pass sample and honour a 'n' then 'y'."""
    main_module = pytest.importorskip("main")
    answers = iter(["n", "y"])
    asked_modes = []
    monkeypatch.setattr(main_module, "ask", lambda prompt="": next(answers))

    original_apply = main_module._apply_mode

    def recording_apply(mode):
        asked_modes.append(mode)
        original_apply(mode)

    monkeypatch.setattr(main_module, "_apply_mode", recording_apply)
    chosen = main_module._calibrate_rtl()

    assert chosen == "raw", "answering n then y must select the second mode"
    assert asked_modes == ["visual", "raw"], "sample must be shown once per mode"
    output = capsys.readouterr().out
    assert "twice" in output.lower(), "the prompt must mention the two-pass sample"
    assert "Sample 1 of 2" in output and "Sample 2 of 2" in output


def test_calibrate_rtl_first_yes_wins_without_showing_second_sample(
    rtl_env, monkeypatch, capsys
):
    """Answering y on the first sample must stop calibration immediately."""
    main_module = pytest.importorskip("main")
    monkeypatch.setattr(main_module, "ask", lambda prompt="": "y")
    chosen = main_module._calibrate_rtl()
    assert chosen == "visual"
    output = capsys.readouterr().out
    assert "Sample 1 of 2" in output
    assert "Sample 2 of 2" not in output


def test_calibrate_rtl_eof_falls_back_to_visual(rtl_env, monkeypatch):
    """EOF/Ctrl-C during calibration must not crash and must restore visual mode."""
    main_module = pytest.importorskip("main")
    from patcher.utils import console

    def raise_eof(prompt=""):
        raise EOFError

    monkeypatch.setattr(main_module, "ask", raise_eof)
    assert main_module._calibrate_rtl() is None
    assert rtl.get_mode() == "visual"
    assert console.RENDER_MODE == "visual"
