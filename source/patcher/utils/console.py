import os
import sys
import ctypes
import re
from patcher.constants import (
    VERSION, COLOR_RESET, COLOR_CYAN, COLOR_GREEN, COLOR_YELLOW, COLOR_RED,
    COLOR_BOLD, COLOR_DIM, COLOR_GRAY, COLOR_WHITE, COLOR_UNDERLINE,
    GITHUB_URL, GITHUB_REPO, TELEGRAM_URL, TELEGRAM_HANDLE,
)
from patcher.utils.rtl import visual

# The interface is Persian, so every line is rendered in terminal visual order
# (reshaped + bidi). Inline ANSI colours are disabled in this mode because escape
# sequences cannot take part in the bidi algorithm; whole lines are painted with
# _paint() after the text has been transformed instead.
RTL_MODE = True

# "visual": we pre-shape/reorder every line ourselves and lay the UI out RTL
#           (works in terminals without bidi support: conhost, Windows Terminal, ...).
# "raw":    the text is printed in logical order and the *terminal* applies bidi
#           (works in terminals that already implement the Unicode bidi algorithm);
#           layout must then stay logical/LTR so the terminal can reorder it once.
RENDER_MODE = "visual"

ANSI_OK = False
USE_COLOR = False


def set_render_mode(mode):
    """Switch the rendering/layout strategy. Returns False for unknown modes."""
    global RENDER_MODE
    if mode in ("visual", "raw"):
        RENDER_MODE = mode
        return True
    return False


def is_raw_mode():
    return RENDER_MODE == "raw"


def enable_ansi():
    if os.name != "nt":
        return True
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_uint32()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        new_mode = mode.value | 0x0004  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
        if new_mode == mode.value:
            return True
        return bool(kernel32.SetConsoleMode(handle, new_mode))
    except Exception:
        return False


def _set_utf8_codepage():
    """Switch the console to UTF-8 without spawning chcp (which eats redirected stdin)."""
    try:
        k32 = ctypes.windll.kernel32
        k32.SetConsoleCP(65001)
        k32.SetConsoleOutputCP(65001)
    except Exception:
        pass


def console_class():
    """Window class of the hosting terminal ('' when unknown).

    "ConsoleWindowClass" is the legacy conhost; Windows Terminal reports
    "CASCADIA_HOSTING_WINDOW_CLASS" (or a pseudo window).
    """
    if os.name != "nt":
        return ""
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if not hwnd:
            return ""
        buf = ctypes.create_unicode_buffer(128)
        ctypes.windll.user32.GetClassNameW(hwnd, buf, 128)
        return buf.value
    except Exception:
        return ""


def is_legacy_console():
    """True inside the classic conhost where Persian glyph fallback may fail."""
    return console_class() == "ConsoleWindowClass"


def setup_console():
    global ANSI_OK, USE_COLOR
    if os.name == "nt":
        _set_utf8_codepage()
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
        if hasattr(sys.stderr, "reconfigure"):
            try:
                sys.stderr.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
    ANSI_OK = enable_ansi()
    USE_COLOR = ANSI_OK and not RTL_MODE


_ANSI_OSC_RE = re.compile(r'\x1b\]8;;.*?(?:\x1b\\|\x07)')
_ANSI_CSI_RE = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
_ZERO_WIDTH_RE = re.compile(
    "[\u200b-\u200f\u202a-\u202e\u2060-\u2064\u2066-\u2069\ufeff"
    "\u064b-\u065f\u0670\u06d6-\u06ed]"
)


def strip_ansi(text):
    """Remove ANSI colour/hyperlink sequences from a string."""
    if "\x1b" not in text:
        return text
    clean = _ANSI_OSC_RE.sub('', text)
    return _ANSI_CSI_RE.sub('', clean)


def _paint(text, *styles):
    """Colour a whole, already-rendered line (independent of USE_COLOR)."""
    if not ANSI_OK or not styles:
        return text
    return "".join(styles) + text + COLOR_RESET


def _rtl(text):
    """Shaped/visual version of a plain string, ANSI codes stripped first."""
    return visual(strip_ansi(str(text)))


def color(text, *styles):
    # Inline colours would be reordered by bidi, so they are skipped in RTL mode.
    if not USE_COLOR or not styles:
        return text
    return "".join(styles) + text + COLOR_RESET


def link(url, text=None, *styles):
    """Plain text in RTL mode; ANSI hyperlink when inline colours are enabled."""
    if text is None:
        text = url
    styled_text = color(text, *styles) if styles else text
    if not USE_COLOR:
        return text
    return f"\x1b]8;;{url}\x1b\\{styled_text}\x1b]8;;\x1b\\"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


_MARKER_RE = re.compile(r"^(\s*)\[([*i\+!x])\]\s(.*)$", re.S)


def _render_line(text):
    """Visual-order rendering that keeps a leading [marker] on the left."""
    match = _MARKER_RE.match(text)
    if match:
        indent, marker, rest = match.groups()
        return indent + "[" + marker + "] " + visual(rest)
    return visual(text)


def emit(*args, sep=" ", end="\n", flush=False):
    """RTL-aware replacement for print(): one visual-order line per call."""
    text = sep.join(str(a) for a in args)
    print(_render_line(text), end=end, flush=flush)


def ask(prompt_text=""):
    """RTL-aware replacement for input(): prompt is rendered visually."""
    return input(visual(str(prompt_text)))


# Layout constants shared by banner, menu dividers, and summary panels.
# BANNER_INNER_WIDTH is the visible width inside a framed box.
# MENU_WIDTH is the matching outer menu width, including the frame columns.
BANNER_INNER_WIDTH = 47
MENU_WIDTH = BANNER_INNER_WIDTH + 2


def _visible_len(text):
    """Return visible text width without ANSI escape codes or zero-width chars."""
    clean = strip_ansi(text)
    return len(_ZERO_WIDTH_RE.sub('', clean))


# Shared frame helpers for the banner and operation summary panels.
def _frame_border(left_ch, fill_ch, right_ch, accent=COLOR_CYAN):
    """Build a horizontal frame border (empty in raw mode: the terminal lays out)."""
    if is_raw_mode():
        return ""
    return _paint(left_ch + fill_ch * BANNER_INNER_WIDTH + right_ch, accent, COLOR_BOLD)


def _frame_row(left, right="", accent=COLOR_CYAN):
    """Build a frame row: `left` at the start, `right` aligned to the end.

    Both cells are rendered in visual order and measured after shaping, so the
    frame stays aligned with Persian text (ligatures change the glyph count).
    In raw mode the terminal applies bidi itself, so the pair is emitted plainly.
    """
    if is_raw_mode():
        return _rtl(left) + ((" " + _rtl(right)) if right else "")
    left_str = "  " + _rtl(left)
    right_str = _rtl(right)
    fill = BANNER_INNER_WIDTH - _visible_len(left_str) - _visible_len(right_str) - 1
    if fill < 1:
        fill = 1
    body = left_str + (" " * fill) + right_str + " "
    # Correct to exact visible width in case shaping changed the glyph count.
    vis = _visible_len(body)
    if vis < BANNER_INNER_WIDTH:
        body = left_str + (" " * (fill + BANNER_INNER_WIDTH - vis)) + right_str + " "
    elif vis > BANNER_INNER_WIDTH:
        while _visible_len(body) > BANNER_INNER_WIDTH:
            body = body[:-1]
    return _paint("║", accent, COLOR_BOLD) + body + _paint("║", accent, COLOR_BOLD)


def print_banner():
    title_left = "Antigravity Patcher"
    title_right = f"v{VERSION}"

    label_col = 10
    rows_to_show = []
    if GITHUB_URL:
        rows_to_show.append(color("GitHub".ljust(label_col), COLOR_YELLOW) + GITHUB_REPO)
    if TELEGRAM_URL:
        tg_text = TELEGRAM_HANDLE if TELEGRAM_HANDLE else TELEGRAM_URL
        rows_to_show.append(color("Telegram".ljust(label_col), COLOR_YELLOW) + tg_text)

    if is_raw_mode():
        print()
        print(f"  Antigravity Patcher {title_right}")
        print("  رفع تحریم و قفل منطقه‌ای آنتی‌گراویتی")
        print("  تمیز • بدون کلید • بدون ردگیری")
        for row_text in rows_to_show:
            print("  " + row_text)
        print()
        return

    print()
    print(f"  {_frame_border('╔', '═', '╗')}")
    print(f"  {_frame_row(title_left, title_right)}")
    print(f"  {_frame_row('', 'رفع تحریم و قفل منطقه‌ای آنتی‌گراویتی')}")
    print(f"  {_frame_row('', 'تمیز • بدون کلید • بدون ردگیری')}")
    if rows_to_show:
        print(f"  {_frame_border('╟', '─', '╢')}")
        for r in rows_to_show:
            print(f"  {_frame_row(r)}")
    print(f"  {_frame_border('╚', '═', '╝')}")

    print()


def print_panel(title, rows, accent=COLOR_GREEN, show_star=False):
    """Render a compact framed summary panel for operation results.

    show_star — draw the GitHub Star reminder under the panel (used only after a
    successful patch, never after a restore/skip).
    """
    if is_raw_mode():
        print()
        print(f"  {title}")
        print()
        for label, value in rows:
            print(f"  {label}: {value}")
        print()
        if show_star and GITHUB_URL:
            print(f"  ★ اگر این ابزار به کارتان آمد، لطفاً در گیت‌هاب ستاره بدهید: {GITHUB_URL}")
            print()
        return

    print()
    try:
        print(f"  {_frame_border('╔', '═', '╗', accent)}")
        print(f"  {_frame_row('', title, accent=accent)}")
        print(f"  {_frame_border('╟', '─', '╢', accent)}")
        for label, value in rows:
            print(f"  {_frame_row(value, label, accent=accent)}")
        print(f"  {_frame_border('╚', '═', '╝', accent)}")
    except UnicodeEncodeError:
        print(f"--- {title} ---")
        for label, value in rows:
            print(f"  {label}: {value}")
        print("-" * (len(title) + 8))
    print()
    if show_star and GITHUB_URL:
        msg = f"  ★ اگر این ابزار به کارتان آمد، لطفاً در گیت‌هاب ستاره بدهید: {GITHUB_URL}"
        print(_paint(visual(msg), COLOR_YELLOW, COLOR_BOLD))
        print()


def print_warning_box(title, subtitle):
    """Framed warning for the main menu (plain in raw mode)."""
    print()
    if is_raw_mode():
        print(f"  [!] {_rtl(title)}")
        print(f"      {_rtl(subtitle)}")
        print()
        return
    print(f"  {_frame_border('╔', '═', '╗', COLOR_YELLOW)}")
    print(f"  {_frame_row(title, accent=COLOR_YELLOW)}")
    print(f"  {_frame_row(subtitle, accent=COLOR_YELLOW)}")
    print(f"  {_frame_border('╚', '═', '╝', COLOR_YELLOW)}")
    print()


# Shared marker helpers for all operation output.
def _message(marker, msg, *styles):
    print(_paint("  " + marker + " " + _rtl(msg), *styles))


def info(msg):
    """Neutral progress/status line."""
    print("  [*] " + _rtl(msg))


def hint(msg):
    """Dim hint line."""
    print(_paint("  [i] " + _rtl(msg), COLOR_DIM))


def ok(msg):
    """Green success line."""
    print(_paint("  [+] " + _rtl(msg), COLOR_GREEN, COLOR_BOLD))


def warn(msg):
    """Yellow warning line."""
    print(_paint("  [!] " + _rtl(msg), COLOR_YELLOW))


def err(msg):
    """Red error line."""
    print(_paint("  [!] " + _rtl(msg), COLOR_RED))


def cancel(msg):
    """Dim cancellation line."""
    print(_paint("  [x] " + _rtl(msg), COLOR_DIM))


def step(name, applied, detail=""):
    """Checklist row: green check, red cross, or dim neutral marker for skipped steps."""
    if applied is None:
        marker = _paint("•", COLOR_DIM)
    else:
        marker = _paint("✓", COLOR_GREEN) if applied else _paint("✗", COLOR_RED)
    line = "  " + marker + " " + _rtl(name)
    if detail:
        line += _paint(" — " + _rtl(detail), COLOR_DIM)
    try:
        print(line)
    except UnicodeEncodeError:
        safe_marker = "[*]" if applied is None else ("[+]" if applied else "[x]")
        safe_line = f"  {safe_marker} {name}"
        if detail:
            safe_line += f" - {detail}"
        print(safe_line)


def _center_line(text, width=MENU_WIDTH):
    """Pad a rendered string on the right up to the menu width."""
    visible = _visible_len(text)
    if visible >= width:
        return text
    return text + " " * (width - visible)


# ─── Menu UI helpers ──────────────────────────────────────────────────────────
def print_menu_section(title):
    """Section header, right-aligned with a rule filling the rest of the line."""
    if is_raw_mode():
        print()
        print(f"  ── {_rtl(title)} ──")
        return
    label = " " + _rtl(title) + " "
    dashes = "─" * max(1, MENU_WIDTH - _visible_len(label))
    print("  " + _paint(dashes, COLOR_GRAY) + _paint(label, COLOR_CYAN, COLOR_BOLD))


def print_menu_row(number, label, hint="", accent=COLOR_GREEN):
    """Menu row laid out for RTL: [number] rightmost, then the label, hint leftmost."""
    if is_raw_mode():
        line = f"  [{number}] {_rtl(label)}" if number != "" else f"  {_rtl(label)}"
        if hint:
            line += "  — " + _rtl(hint)
        print(line)
        return

    num_part = _paint(f"[{number}]", accent, COLOR_BOLD) if number != "" else "  "
    label_part = _rtl(label)
    right_block = label_part + "  " + num_part
    right_visible = _visible_len(right_block)
    if not hint:
        print("  " + " " * max(0, MENU_WIDTH - right_visible) + right_block)
        return

    hint_part = _paint(_rtl(hint), COLOR_DIM)
    gap = max(2, MENU_WIDTH - right_visible - _visible_len(hint_part))
    print("  " + hint_part + " " * gap + right_block)


def print_menu_divider():
    """Thin horizontal separator."""
    print(f"  {_paint('─' * MENU_WIDTH, COLOR_GRAY)}")


def print_menu_footer(note=""):
    """Footer under the menu: separator plus an optional note."""
    if is_raw_mode():
        print()
        if note:
            print(f"  {_rtl(note)}")
        return
    print(f"  {_paint('─' * MENU_WIDTH, COLOR_GRAY)}")
    if note:
        print(_paint("  " + _rtl(note), COLOR_DIM))
