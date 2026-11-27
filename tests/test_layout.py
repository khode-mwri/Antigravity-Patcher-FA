"""Layout regression tests for the framed Persian terminal UI.

The visual mode UI is drawn on a fixed 51-column grid:

    2 leading spaces + BANNER_INNER_WIDTH(47) + 2 frame columns = 51
    2 leading spaces + MENU_WIDTH(49)                          = 51

Every framed line therefore has to be *exactly* 51 columns wide after shaping
(Persian ligatures change the glyph count, so this is measured with
``console._visible_len``).  Menu option numbers must sit on the right-hand edge
because the menu is read right-to-left.

Raw mode keeps logical character order (the terminal applies bidi itself), so
its grid mirrors the visual one with ASCII spaces: menu rows are right-padded
to the same 51 columns and section titles sit against the right edge with
spaces filling the rest of the block.  Raw text must never be reshaped, and
the option number stays at the *start* of the line (the terminal is expected
to reorder the line exactly once).
"""

import io
import re
from contextlib import contextmanager, redirect_stdout

import pytest

from patcher.utils import console, rtl

EXPECTED_WIDTH = 51  # fixed UI grid, see module docstring
PRESENTATION_FORM_RE = re.compile("[\ufb50-\ufdfe\ufe70-\ufefc]")
# Lines that belong to a frame/rule start with one of these glyphs (after the
# two leading spaces of the layout).
FRAME_LINE_RE = re.compile("^\\s*[╔║╟╚─]")


def _render(func, *args, **kwargs):
    """Render one UI helper and return its lines with ANSI codes stripped."""
    console.setup_console()  # same encoding setup as the real entry point
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        func(*args, **kwargs)
    return console.strip_ansi(buffer.getvalue()).splitlines()


@contextmanager
def _raw_mode(enabled=True):
    """Switch *both* rendering layers to raw mode for the duration of a block."""
    previous_console = console.RENDER_MODE
    previous_rtl = rtl.get_mode()
    previous_align = console.RAW_MODE_ALIGN
    try:
        console.set_render_mode("raw" if enabled else "visual")
        rtl.set_mode("raw" if enabled else "visual")
        console.RAW_MODE_ALIGN = enabled
        yield
    finally:
        console.RAW_MODE_ALIGN = previous_align
        console.set_render_mode(previous_console)
        rtl.set_mode(previous_rtl)


def _render_raw(func, *args, **kwargs):
    """Render one UI helper in raw mode; returns ANSI-stripped lines."""
    with _raw_mode():
        return _render(func, *args, **kwargs)


def _assert_framed_widths(lines):
    """Every frame/rule line must be exactly EXPECTED_WIDTH visible columns."""
    framed = [line for line in lines if FRAME_LINE_RE.match(line)]
    assert framed, "no framed lines found in output: %r" % (lines,)
    bad = {}
    for line in framed:
        width = console._visible_len(line)
        if width != EXPECTED_WIDTH:
            bad[width] = line
    assert not bad, "framed lines with wrong visible width (expected %d): %r" % (
        EXPECTED_WIDTH,
        bad,
    )
    return framed


def test_banner_is_exactly_51_columns():
    lines = _render(console.print_banner)
    framed = _assert_framed_widths(lines)

    assert len(framed) >= 6, "banner lost its frame: %r" % (lines,)
    # The banner is a pure frame: every non-empty line starts with a frame glyph.
    for line in lines:
        if line.strip():
            assert FRAME_LINE_RE.match(line), "unframed banner line: %r" % (line,)

    text = "\n".join(lines)
    assert "Antigravity Patcher" in text
    assert PRESENTATION_FORM_RE.search(text), "banner has no shaped Persian"


PANEL_ROWS = [
    pytest.param([("نسخه", "1.4.0")], id="one_row"),
    pytest.param(
        [("نسخه", "1.4.0"), ("وضعیت", "پچ شد"), ("بکاپ", "ساخته شد")],
        id="three_rows",
    ),
]


@pytest.mark.parametrize("rows", PANEL_ROWS)
def test_panel_is_exactly_51_columns(rows):
    lines = _render(console.print_panel, "نتیجهٔ عملیات", rows)
    _assert_framed_widths(lines)
    text = "\n".join(lines)
    assert PRESENTATION_FORM_RE.search(text), "panel has no shaped Persian"


# The same rows the real main menu renders (numbers, Persian labels and hints),
# including the longest hint/label combinations that are most likely to overflow.
MENU_ROWS = {
    "patch_ide": ("1", "پچ Antigravity IDE", "دور زدن قفل منطقه"),
    "patch_manager": ("2", "پچ Antigravity 2.0", "پچ language_server"),
    "patch_cli": ("3", "پچ Antigravity CLI", "رفع قفل ابزار agy"),
    "patch_vscode": ("4", "پچ افزونهٔ VS Code", "extension.js و باینری agy"),
    "restore_vscode": ("8", "افزونهٔ Antigravity VS Code", "از بکاپ"),
    "check_updates": ("9", "بررسی به‌روزرسانی", "نسخه‌های GitHub"),
    "star": ("10", "ستاره در GitHub", "حمایت از پروژه"),
    "manual_path": ("11", "انتخاب مسیر دستی", "بازنویسی هدف"),
    "about": ("12", "درباره برنامه", "نسخه و نویسنده"),
    "exit": ("0", "خروج", "خروج از پچر"),
    "download": ("1", "باز کردن صفحهٔ دانلود", "در مرورگر"),
    "no_hint": ("5", "Antigravity IDE", "از بکاپ"),
    "skip": ("0", "فعلاً رد شود (منوی اصلی)", ""),
}


@pytest.mark.parametrize("row", MENU_ROWS.values(), ids=list(MENU_ROWS))
def test_menu_row_fits_width_and_number_is_rightmost(row):
    number, label, hint = row
    lines = _render(console.print_menu_row, number, label, hint)
    assert len(lines) == 1, "print_menu_row must print exactly one line"

    line = lines[0]
    width = console._visible_len(line)
    assert width <= EXPECTED_WIDTH, "menu row overflows the %d-column grid: %r" % (
        EXPECTED_WIDTH,
        line,
    )
    assert line.rstrip().endswith("[%s]" % number), (
        "option number is not the right-most token: %r" % (line,)
    )
    assert PRESENTATION_FORM_RE.search(line), "menu row has no shaped Persian"


@pytest.mark.parametrize("number", [str(n) for n in range(13)], ids=lambda n: "opt" + n)
def test_menu_row_number_is_last_visible_token(number):
    lines = _render(console.print_menu_row, number, "گزینهٔ نمونه", "توضیح کوتاه")
    line = lines[0].rstrip()
    assert console._visible_len(lines[0]) <= EXPECTED_WIDTH
    assert line.endswith("[%s]" % number), "'[%s]' must be at the end: %r" % (
        number,
        lines[0],
    )


def test_menu_row_without_number_keeps_number_column_empty():
    """Numberless rows still respect the 51-column grid and draw no option tag."""
    lines = _render(console.print_menu_row, "", "دربارهٔ ابزار", "")
    line = lines[0]
    assert console._visible_len(line) == EXPECTED_WIDTH
    assert "[" not in line, "unexpected option bracket: %r" % (line,)


@pytest.mark.parametrize(
    "title",
    ["پچ", "بازگردانی", "ابزارها", "انتخاب دستی مسیر", "درباره برنامه"],
)
def test_menu_section_rule_is_exactly_51_columns(title):
    lines = _render(console.print_menu_section, title)
    assert len(lines) == 1
    assert FRAME_LINE_RE.match(lines[0]), "section header must start with a rule"
    assert console._visible_len(lines[0]) == EXPECTED_WIDTH, (
        "section rule is %d columns wide, expected %d: %r"
        % (console._visible_len(lines[0]), EXPECTED_WIDTH, lines[0])
    )


def test_menu_divider_is_exactly_51_columns():
    lines = _render(console.print_menu_divider)
    assert len(lines) == 1
    assert console._visible_len(lines[0]) == EXPECTED_WIDTH


def test_menu_footer_rule_is_exactly_51_columns():
    # The optional note below the rule may be longer; only the rule is checked.
    lines = _render(console.print_menu_footer, "نکته: به‌روزرسانی‌ها را بررسی کنید.")
    _assert_framed_widths(lines[:1])
    assert len(lines) == 2, "footer with a note must print a rule and the note"


# ─── Raw-mode layout ──────────────────────────────────────────────────────────
# Raw mode prints logical order (no shaping/bidi); its alignment must come from
# plain-ASCII padding on the 51-column grid instead.


def test_raw_mode_align_toggle_is_enabled_by_default():
    assert console.RAW_MODE_ALIGN is True


@pytest.mark.parametrize("row", MENU_ROWS.values(), ids=list(MENU_ROWS))
def test_raw_menu_row_is_padded_to_the_menu_block(row):
    """Raw rows are right-padded so every row ends on the same 51st column.

    Rows whose logical text already exceeds MENU_WIDTH are exempt (same as
    visual mode, which never truncates a row).
    """
    number, label, hint = row
    lines = _render_raw(console.print_menu_row, number, label, hint)
    assert len(lines) == 1, "print_menu_row must print exactly one line"

    line = lines[0]
    width = console._visible_len(line)
    body_width = width - 2  # 2-space layout indent
    if body_width > console.MENU_WIDTH:
        # Longer rows are never truncated (same policy as visual mode); they
        # simply get no extra padding, so the line has no trailing spaces.
        assert line == line.rstrip(), (
            "row wider than the block must not be padded: %r" % (line,)
        )
    else:
        assert body_width == console.MENU_WIDTH, (
            "raw menu row is not padded to the %d-column block (got %d): %r"
            % (console.MENU_WIDTH, body_width, line)
        )

    # Raw mode: no reshaping at all — base Persian letters stay base letters.
    assert not PRESENTATION_FORM_RE.search(line), (
        "raw menu row must not contain shaped glyphs: %r" % (line,)
    )
    # The number stays at the visual start of the line for the terminal's bidi.
    assert line.lstrip().startswith("[%s]" % number), (
        "raw menu row must start with '[%s]': %r" % (number, line)
    )


def test_raw_menu_row_without_number_starts_with_label_and_is_padded():
    lines = _render_raw(console.print_menu_row, "", "دربارهٔ ابزار", "")
    line = lines[0]
    assert console._visible_len(line) == 2 + console.MENU_WIDTH
    assert "[" not in line, "unexpected option bracket: %r" % (line,)
    assert line.startswith("  " + "دربارهٔ ابزار"), (
        "numberless raw row must start with the logical label: %r" % (line,)
    )


@pytest.mark.parametrize(
    "title",
    ["پچ", "بازگردانی", "ابزارها", "انتخاب دستی مسیر", "درباره برنامه"],
)
def test_raw_menu_section_title_sits_on_the_right_edge(title):
    """Raw section header: spaces fill the block, the title hugs the right margin."""
    lines = _render_raw(console.print_menu_section, title)
    # print_menu_section starts with a blank spacer line in raw mode.
    assert len(lines) == 2, "raw section must print a spacer and the header"
    assert lines[0] == ""
    line = lines[1]
    assert console._visible_len(line) == 2 + console.MENU_WIDTH, (
        "raw section header is %d columns, expected %d: %r"
        % (console._visible_len(line), 2 + console.MENU_WIDTH, line)
    )
    assert line.startswith("  "), "section header must keep the 2-space indent"
    assert line.rstrip().endswith(title), (
        "section title must end the line (right edge): %r" % (line,)
    )
    # Padding before the title is plain ASCII spaces, nothing else.
    title_start = line.rfind(title)
    assert set(line[2:title_start]) == {" "}, (
        "raw section padding must be ASCII spaces only: %r" % (line,)
    )
    assert not PRESENTATION_FORM_RE.search(line), (
        "raw section header must not contain shaped glyphs: %r" % (line,)
    )


def test_raw_menu_section_align_can_be_disabled():
    """RAW_MODE_ALIGN=False restores the old plain '── title ──' form."""
    with _raw_mode():
        console.RAW_MODE_ALIGN = False
        lines = _render(console.print_menu_section, "پچ")
    assert lines[-1] == "  ── پچ ──"


def test_raw_menu_row_align_can_be_disabled():
    with _raw_mode():
        console.RAW_MODE_ALIGN = False
        lines = _render(console.print_menu_row, "1", "خروج", "خروج از پچر")
    assert lines[0] == "  [1] خروج  — خروج از پچر"


def test_raw_menu_row_wider_than_block_is_never_truncated_or_padded():
    """Rows already wider than MENU_WIDTH keep their logical text untouched.

    The shipped menu contains one such row ([4], "پچ افزونهٔ VS Code" plus the
    "extension.js و باینری agy" hint): without shaping its logical width exceeds
    the 49-column block.  Raw mode must print it in full — the same policy as
    visual mode, which never truncates a row — and add no trailing padding.
    """
    number, label, hint = MENU_ROWS["patch_vscode"]
    lines = _render_raw(console.print_menu_row, number, label, hint)
    assert len(lines) == 1, "print_menu_row must print exactly one line"

    line = lines[0]
    # Raw mode is pass-through, so the expected line is the plain logical text.
    expected = "  [%s] %s  — %s" % (number, label, hint)
    assert line == expected, "over-wide raw row was altered: %r" % (line,)
    assert console._visible_len(line) > 2 + console.MENU_WIDTH, (
        "test fixture row is not actually wider than the block: %r" % (line,)
    )
    assert not PRESENTATION_FORM_RE.search(line), (
        "raw menu row must not contain shaped glyphs: %r" % (line,)
    )


def test_raw_menu_rows_all_end_on_the_same_column():
    """A block of raw rows (indented + padded) shares one right edge."""
    block = [
        ("1", "پچ Antigravity IDE", "دور زدن قفل منطقه"),
        ("9", "بررسی به‌روزرسانی", "نسخه‌های GitHub"),
        ("11", "انتخاب مسیر دستی", "بازنویسی هدف"),
        ("0", "خروج", "خروج از پچر"),
    ]
    widths = set()
    with _raw_mode():
        for row in block:
            lines = _render(console.print_menu_row, *row)
            widths.add(console._visible_len(lines[0]))
    assert widths == {2 + console.MENU_WIDTH}, (
        "raw menu rows do not share one right edge: widths %r" % (sorted(widths),)
    )


def test_visual_mode_output_is_unaffected_by_raw_mode_padding():
    """Padding must not leak into visual mode (visual keeps its own right-aligned text)."""
    sample = ("4", "پچ افزونهٔ VS Code", "extension.js و باینری agy")
    visual_line = _render(console.print_menu_row, *sample)[0]
    assert console._visible_len(visual_line) == EXPECTED_WIDTH
    assert visual_line.rstrip().endswith("[4]"), (
        "visual row must still put the number rightmost: %r" % (visual_line,)
    )
    assert PRESENTATION_FORM_RE.search(visual_line)
