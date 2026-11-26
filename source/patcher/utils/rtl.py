"""Right-to-left (Persian) rendering helpers.

Terminals do not run the Unicode bidi algorithm (and most do not shape Arabic
script at all), so Persian text printed in logical order comes out reversed and
with disconnected letters. To get readable output everywhere we convert each
line to *visual* order before printing:

    logical  "رفع تحریم"
    visual   "ﻢﯾﺮﺤﺗ ﻊﻓﺭ"      (shaped presentation forms, reversed)

`arabic_reshaper` maps the letters to their presentation forms and
`python-bidi` applies the UAX#9 bidi algorithm with an RTL paragraph direction,
so mixed Persian/Latin lines (versions, paths, URIs) stay intact.

Rendering modes
---------------
Some terminals implement the bidi algorithm themselves; those would mirror the
already-visual text, so the user sees "mirrored" Persian. For them the tool can
switch to ``raw`` mode, where `visual()` / `visual_line()` return the input
untouched. The selected mode is stored between runs by
`patcher.utils.rtl_prefs` (first-run calibration).

``visual`` (default) — reshape + bidi reorder, one line at a time.
``raw``            — no transformation at all; the terminal handles bidi.

If the libraries are missing the text is returned unchanged so the tool keeps
working (it just looks garbled, exactly like the un-patched behaviour).
"""

import re

try:  # optional at runtime, required for a readable Persian UI
    from arabic_reshaper import reshape as _reshape
    from bidi.algorithm import get_display as _get_display
    AVAILABLE = True
except Exception:  # pragma: no cover - only hit when deps are not installed
    _reshape = None
    _get_display = None
    AVAILABLE = False

# Active rendering mode. `visual` = shape + reorder (default, for bidi-less
# terminals); `raw` = pass-through for terminals that apply bidi themselves.
MODE = "visual"
_MODES = ("visual", "raw")

# Hebrew, Arabic, Syriac, Thaana, N'Ko, Arabic Extended, presentation forms.
_RTL_RE = re.compile(
    "[\u0590-\u05ff\u0600-\u06ff\u0700-\u074f\u0750-\u077f"
    "\u0780-\u07bf\u07c0-\u07ff\u0800-\u08ff\ufb1d-\ufdff\ufe70-\ufefc]"
)
# Arabic presentation forms only appear in text that was already reshaped, so a
# line containing them is already in visual order and must not be reversed again.
_SHAPED_RE = re.compile("[\ufb50-\ufdff\ufe70-\ufefc]")


def get_mode():
    """Return the active rendering mode, either ``"visual"`` or ``"raw"``."""
    return MODE


def set_mode(mode):
    """Switch the rendering mode.

    Only ``"visual"`` and ``"raw"`` are accepted. Returns ``True`` when the mode
    was changed and ``False`` (leaving the current mode untouched) otherwise.
    """
    global MODE
    if mode in _MODES:
        MODE = mode
        return True
    return False


def has_rtl(text):
    """True when the string contains right-to-left letters (mode independent)."""
    if not isinstance(text, str) or not text:
        return False
    return bool(_RTL_RE.search(text))


def is_visual(text):
    """True when the string already contains shaped glyphs (mode independent)."""
    if not isinstance(text, str) or not text:
        return False
    return bool(_SHAPED_RE.search(text))


def visual_line(line):
    """Return one line of text in terminal visual order.

    No-op in ``raw`` mode, for pure-LTR text, and for text that already holds
    presentation forms (it would otherwise be reshaped/reversed twice).
    """
    if (
        MODE == "raw"
        or not line
        or not AVAILABLE
        or not has_rtl(line)
        or is_visual(line)
    ):
        return line
    try:
        return _get_display(_reshape(line), base_dir="R")
    except Exception:  # pragma: no cover - defensive: never break the UI
        return line


def visual(text):
    """Return text in terminal visual order, line by line.

    In ``raw`` mode the text is returned exactly as given (the terminal itself
    takes care of bidi).
    """
    if MODE == "raw" or not text or not isinstance(text, str):
        return text
    if "\n" not in text:
        return visual_line(text)
    return "\n".join(visual_line(line) for line in text.split("\n"))
