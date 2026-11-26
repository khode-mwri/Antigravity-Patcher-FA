"""Persistent UI preferences for the Persian terminal interface.

Some terminals implement the Unicode bidi algorithm themselves, so pre-shaped
"visual" text comes out mirrored there. The user's RTL rendering mode is
therefore calibrated on first run and stored in a tiny JSON file:

    Windows: %APPDATA%\\Antigravity-Patcher\\ui.json
    POSIX:   ~/.config/Antigravity-Patcher/ui.json

Everything here is best-effort: a missing, unreadable, or malformed file simply
means "no saved preference" (``None``), and writes never raise.
"""

import json
import os
import tempfile
from pathlib import Path

APP_DIR_NAME = "Antigravity-Patcher"
PREFS_FILE_NAME = "ui.json"
RTL_KEY = "rtl_mode"
MODES = ("visual", "raw")


def _home_dir():
    """Home directory, used when APPDATA is unavailable."""
    try:
        return Path.home()
    except (RuntimeError, OSError):  # pragma: no cover - exotic environments
        return Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or ".")


def prefs_path():
    """Absolute path of the UI preferences JSON file."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA") or _home_dir())
    else:
        base = _home_dir() / ".config"
    return str(base / APP_DIR_NAME / PREFS_FILE_NAME)


def is_valid(mode):
    """True when ``mode`` is a supported RTL rendering mode."""
    return mode in MODES


def load_mode():
    """Return the saved RTL mode, or ``None`` if absent, invalid or corrupt."""
    try:
        with open(prefs_path(), "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception:  # missing file, permissions, corrupt JSON, ...
        return None
    if not isinstance(data, dict):
        return None
    mode = data.get(RTL_KEY)
    return mode if is_valid(mode) else None


def save_mode(mode):
    """Persist ``mode`` in the preferences file; return True on success.

    The parent directory is created when needed and the file is replaced
    atomically, so a crash mid-write cannot leave a half-written JSON behind.
    Any failure (invalid mode, permissions, disk full, ...) returns ``False``
    instead of raising.
    """
    if not is_valid(mode):
        return False
    path = Path(prefs_path())
    tmp_path = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            prefix=path.name + ".", suffix=".tmp", dir=str(path.parent)
        )
        tmp_path = Path(tmp_name)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump({RTL_KEY: mode}, handle)
        os.replace(str(tmp_path), str(path))
        tmp_path = None
        return True
    except Exception:
        return False
    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink()
            except OSError:
                pass
