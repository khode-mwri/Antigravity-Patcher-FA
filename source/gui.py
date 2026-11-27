"""Native desktop GUI for the Antigravity Patcher (tkinter + ttk only).

The GUI is a thin presentation layer over the existing command-line patcher:
the very same discovery helpers and ``do_patch*`` / ``do_restore*`` functions
that the CLI menu calls are executed here, so both front-ends stay in sync.

Threading model
---------------
Tk is not thread-safe, so every long-running job runs on a daemon thread:

* discovery ("scan")   -> ``discover_targets``       -> queue ``("scan_done", ...)``
* patch/restore jobs    -> patcher ``do_*`` functions -> queue log lines and
                                                          ``("jobs_done", ...)``
* update check          -> ``check_for_updates``      -> queue ``("update_done", ...)``

The main thread polls the queue every 100 ms (``_poll_events``) and is the
only thread that ever touches a widget.

While patch/restore jobs run, the CLI's interactive helpers (``confirmed``,
``ask`` and ``confirm_with_captcha``) are monkey-patched for the duration so
the patcher can never block on stdin, and ``webbrowser.open`` is neutralised
because the GUI owns all navigation.  The originals are restored in a
``finally`` block.

Persian rendering
-----------------
Tk's text engine performs no Arabic shaping or bidi reordering, so for the
Persian UI every label goes through :func:`L`, which runs the string through
``rtl.visual`` (arabic_reshaper + python-bidi) when the active language is
right-to-left.  Captured patcher output is shaped line by line the same way.
Native dialogs (message boxes, file dialogs) draw text themselves, so they
receive logical Unicode from ``tr`` rather than pre-shaped text.

Importing this module has no side effects: no Tk root is created until
:func:`run_gui` is called.
"""

import os
import queue
import sys
import threading
import tkinter as tk
import webbrowser
from tkinter import filedialog, font as tkfont, messagebox, ttk

from patcher import i18n
from patcher.agy import discovery as agy_discovery
from patcher.agy import patcher as agy_patcher
from patcher.constants import GITHUB_REPO, GITHUB_URL, TELEGRAM_URL, VERSION
from patcher.ide import discovery as ide_discovery
from patcher.ide import patcher as ide_patcher
from patcher.manager import discovery as manager_discovery
from patcher.manager import patcher as manager_patcher
from patcher.utils import rtl
from patcher.utils import update as update_utils
from patcher.utils.admin import is_admin
from patcher.utils.console import strip_ansi
from patcher.vscode import discovery as vscode_discovery
from patcher.vscode import patcher as vscode_patcher

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Literal brand suffix used in the native window title only (the title bar is
# OS chrome, not translatable UI copy).
APP_TITLE_SUFFIX = "Antigravity Patcher"

ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")

RELEASES_URL = GITHUB_URL + "/releases"
ISSUES_URL = GITHUB_URL + "/issues"

#: License identifier (technical string, shown next to the translated label).
LICENSE_ID = "GPL-3.0"

#: Display order of the target rows and their translation-label keys.
TARGET_ORDER = ("ide", "manager", "cli", "vscode", "vscode_binary")
TARGET_LABEL_KEYS = {
    "ide": "target_ide",
    "manager": "target_manager",
    "cli": "target_cli",
    "vscode": "target_vscode",
    "vscode_binary": "target_vscode_binary",
}

#: Badge foreground colours per status key.
STATUS_COLORS = {
    "found": "#1a7f37",
    "not_found": "#b42318",
    "patched": "#1a7f37",
    "not_patched": "#9a6700",
    "unknown": "#6b7280",
}

#: File-picker filters per target (technical file names only).
PICK_FILETYPES = {
    "ide": (("main.js", "main.js"), ("*.js", "*.js")),
    "manager": (("language_server*", "language_server*"), ("*.exe", "*.exe")),
    "cli": (("agy*", "agy*"), ("*.exe", "*.exe")),
    "vscode": (("extension.js", "extension.js"), ("*.js", "*.js")),
    "vscode_binary": (("antigravity*", "antigravity*"), ("agy*", "agy*"), ("*.exe", "*.exe")),
}

POLL_INTERVAL_MS = 100


# ---------------------------------------------------------------------------
# Translation / display helpers
# ---------------------------------------------------------------------------

def L(key, **kwargs):
    """Translate ``key`` and prepare it for a Tk widget.

    Tk does not shape Arabic script, so for right-to-left languages the
    logical string is converted to visual order (shaped presentation forms,
    reversed) exactly like the terminal front-end does.  For LTR languages
    the plain translation is returned.
    """
    text = i18n.tr(key, **kwargs)
    if i18n.is_rtl():
        return rtl.visual(text)
    return text


def _display(text):
    """Shape a composed (non-key) logical string for display in a Tk widget."""
    if i18n.is_rtl():
        return rtl.visual(text)
    return text


def _compose_label(key, value):
    """Render a ``label: value`` line where only the label is translated."""
    return _display("%s: %s" % (i18n.tr(key), value))


def _middle_truncate(text, limit=64):
    """Shorten a long path with a middle ellipsis (keeps drive and file name)."""
    if len(text) <= limit:
        return text
    keep = max(4, limit - 1)
    head = (keep + 1) // 2
    tail = keep - head
    return text[:head] + "…" + text[-tail:]


# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------

def _resolve_fonts(root):
    """Pick the Windows UI fonts, degrading gracefully on any other system.

    ``tkfont.families`` is queryable only once a Tk root exists; every lookup
    is guarded so a missing or exotic font can never crash the window.
    """
    fonts = {"body": None, "small": None, "bold": None, "brand": None}
    try:
        families = set(tkfont.families(root))
    except Exception:
        families = set()

    def _make(candidates, size, fallback_weight="normal"):
        for family, weight in candidates:
            if family in families:
                try:
                    return tkfont.Font(root=root, family=family, size=size, weight=weight)
                except Exception:
                    continue
        try:
            return tkfont.Font(root=root, size=size, weight=fallback_weight)
        except Exception:
            return None

    fonts["body"] = _make([("Segoe UI", "normal")], 10)
    fonts["small"] = _make([("Segoe UI", "normal")], 9)
    fonts["bold"] = _make([("Segoe UI Semibold", "normal"), ("Segoe UI", "bold")], 10, "bold")
    fonts["brand"] = _make([("Segoe UI Semibold", "normal"), ("Segoe UI", "bold")], 15, "bold")
    return fonts


def _try_style(style, name, **options):
    """Apply a ttk style option, ignoring themes that do not support it."""
    try:
        style.configure(name, **options)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# stdout/stderr capture
# ---------------------------------------------------------------------------

class _QueueWriter:
    """Minimal stdout/stderr replacement forwarding whole lines to a queue.

    The patcher prints through the console helpers (``print`` based), so a
    small line-buffered stream is enough; the main thread shapes and inserts
    each line into the log widget.
    """

    encoding = "utf-8"
    errors = "replace"

    def __init__(self, events):
        self._events = events
        self._buffer = ""

    def write(self, text):
        if not text:
            return 0
        if not isinstance(text, str):
            text = str(text)
        self._buffer += text
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            if line.endswith("\r"):
                line = line[:-1]
            self._events.put(("log", line))
        return len(text)

    def flush(self):
        # Lines are forwarded as soon as their newline arrives.
        return None

    def isatty(self):
        return False

    def writable(self):
        return True

    def close_pending(self):
        """Forward a trailing partial line (no newline) before shutdown."""
        if self._buffer:
            self._events.put(("log", self._buffer))
            self._buffer = ""


# ---------------------------------------------------------------------------
# Discovery (runs on a worker thread; never touches Tk)
# ---------------------------------------------------------------------------

def _run_finder(key):
    """Run the auto-discovery helper for one target (falsy means "not found")."""
    if key == "ide":
        root = ide_discovery.find_install_root()
        return ide_discovery.find_main_js(root) if root else ""
    if key == "manager":
        return manager_discovery.find_manager_binary()
    if key == "cli":
        return agy_discovery.find_agy_binary()
    if key == "vscode":
        return vscode_discovery.find_extension_js()
    if key == "vscode_binary":
        return vscode_discovery.find_gemini_antigravity_binary()
    return ""


def _is_patched(key, path):
    """Ask the matching patcher whether *path* already carries the patch."""
    if key in ("ide", "vscode"):
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            content = handle.read()
        checker = ide_patcher.is_already_patched if key == "ide" else vscode_patcher.is_already_patched
        return bool(checker(content))
    if key == "manager":
        return bool(manager_patcher.is_already_patched(path))
    return bool(agy_patcher.is_already_patched(path))


def _read_version(key, path):
    """Return the installed version when it is cheap to read, else ''."""
    if key == "ide":
        value = ide_discovery.get_ag_version(path)
        if isinstance(value, tuple):
            value = value[0] if value else ""
        return str(value or "")
    if key == "manager":
        return str(manager_discovery.get_antigravity_version(path) or "")
    return ""


def _probe_target(key, override):
    """Collect one target's state: path, patch status and (optional) version."""
    path = override or ""
    if not path:
        try:
            path = _run_finder(key) or ""
        except Exception:
            path = ""
    result = {"path": path, "status": "not_found", "version": ""}
    if not path or not os.path.isfile(path):
        return result
    try:
        result["status"] = "patched" if _is_patched(key, path) else "not_patched"
    except Exception:
        # The file exists but could not be inspected (locked, unreadable, ...).
        result["status"] = "unknown"
    try:
        result["version"] = _read_version(key, path) or ""
    except Exception:
        result["version"] = ""
    return result


def discover_targets(overrides):
    """Probe every target once.  ``overrides`` maps target key -> manual path.

    This reads files only (never patches) and is safe to call from a worker
    thread.  A failure in one probe never affects the other targets.
    """
    overrides = overrides or {}
    results = {}
    for key in TARGET_ORDER:
        try:
            results[key] = _probe_target(key, overrides.get(key, ""))
        except Exception:
            results[key] = {"path": overrides.get(key, "") or "", "status": "unknown", "version": ""}
    return results


# ---------------------------------------------------------------------------
# Patch/restore execution (runs on a worker thread)
# ---------------------------------------------------------------------------

def _run_job(key, action, path):
    """Call the real patcher function for one target/action pair."""
    if key == "ide":
        return ide_patcher.do_patch(path) if action == "patch" else ide_patcher.do_restore(path)
    if key == "manager":
        return manager_patcher.do_patch_manager(path) if action == "patch" else manager_patcher.do_restore_manager(path)
    if key == "vscode":
        return vscode_patcher.do_patch_vscode(path) if action == "patch" else vscode_patcher.do_restore_vscode(path)
    if key in ("cli", "vscode_binary"):
        # The CLI binary and the VS Code extension's downloaded agy binary are
        # patched by the same agy patcher.
        return agy_patcher.do_patch_agy(path) if action == "patch" else agy_patcher.do_restore_agy(path)
    raise ValueError("unknown target: %r" % (key,))


def _install_interactive_stubs():
    """Silence the CLI's interactive helpers for the duration of a GUI job.

    The patcher modules import ``confirmed`` / ``confirm_with_captcha`` lazily
    inside their functions, so replacing the attributes on the modules here is
    enough.  ``webbrowser.open`` is neutralised as well: the GUI opens URLs
    itself and the patcher's fallback dialogs must not spawn browsers behind
    its back.  Returns the originals for ``_restore_interactive_stubs``.
    """
    import patcher.cli as cli_module
    from patcher.utils import captcha as captcha_module

    originals = (
        cli_module,
        cli_module.confirmed,
        cli_module.ask,
        captcha_module,
        captcha_module.confirm_with_captcha,
        webbrowser.open,
    )
    cli_module.confirmed = lambda *_a, **_k: True
    cli_module.ask = lambda *_a, **_k: "0"
    captcha_module.confirm_with_captcha = lambda *_a, **_k: True
    webbrowser.open = lambda *_a, **_k: True
    return originals


def _restore_interactive_stubs(originals):
    """Undo :func:`_install_interactive_stubs` (always called in a finally)."""
    cli_module, confirmed, ask, captcha_module, confirm, open_fn = originals
    cli_module.confirmed = confirmed
    cli_module.ask = ask
    captcha_module.confirm_with_captcha = confirm
    webbrowser.open = open_fn


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class PatcherGUI:
    """The whole desktop window: header, target rows, tools, about and log."""

    def __init__(self, root):
        self.root = root

        # Tk does no Arabic shaping: force the visual-order renderer.
        rtl.set_mode("visual")

        # Window chrome: default size and a minimum that keeps every panel usable.
        try:
            self.root.geometry("1000x700")
            self.root.minsize(880, 620)
        except Exception:
            pass

        # Runtime state -----------------------------------------------------
        self._busy = False            # a scan, patch job or update check is running
        self._scan_active = False     # the busy reason is a discovery scan
        self._log_empty = True
        self._targets = {key: {"path": "", "status": "unknown", "version": ""} for key in TARGET_ORDER}
        self._overrides = {}          # target key -> manually picked path
        self._events = queue.Queue()
        self._scan_thread = None
        self._job_thread = None
        self._poll_after_id = None
        self._row_widgets = {}
        self._tools_buttons = {}
        self._about_buttons = {}

        # Fonts and widgets ---------------------------------------------------
        self._fonts = _resolve_fonts(root)
        self._build_ui()
        self._apply_fonts()
        self._retranslate()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------ UI --
    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)

        row = 0

        # --- Header: brand, tagline and the language selector ---------------
        header = ttk.Frame(outer)
        header.grid(row=row, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        self._brand_label = ttk.Label(header, style="Brand.TLabel")
        self._brand_label.grid(row=0, column=0, sticky="w")
        self._tagline_label = ttk.Label(header, style="Tagline.TLabel")
        self._tagline_label.grid(row=1, column=0, sticky="w")

        language_box = ttk.Frame(header)
        language_box.grid(row=0, column=1, rowspan=2, sticky="e")
        self._lang_label = ttk.Label(language_box, style="Muted.TLabel")
        self._lang_label.grid(row=0, column=0, padx=(0, 8))
        self._lang_combo = ttk.Combobox(language_box, state="readonly", width=12)
        self._lang_combo.grid(row=0, column=1)
        self._lang_combo.bind("<<ComboboxSelected>>", self._on_language_selected)

        # Language defaults to English on every launch (nothing is persisted).
        self._language_pairs = i18n.available_languages()
        self._lang_codes = [code for code, _label in self._language_pairs]
        self._lang_labels = [label for _code, label in self._language_pairs]
        self._lang_combo.configure(values=self._lang_labels)
        current_language = i18n.get_language()
        if current_language in self._lang_codes:
            self._lang_combo.current(self._lang_codes.index(current_language))
        elif self._lang_codes:
            self._lang_combo.current(0)

        row += 1

        # --- Optional admin warning strip -----------------------------------
        self._admin_strip = None
        if os.name == "nt" and not is_admin():
            self._admin_strip = tk.Label(outer, bg="#fff4ce", fg="#664d03", padx=10, pady=6, justify="left")
            self._admin_strip.grid(row=row, column=0, sticky="ew", pady=(8, 0))
            if self._fonts.get("small"):
                self._admin_strip.configure(font=self._fonts["small"])
            row += 1

        # --- Targets panel ---------------------------------------------------
        self._targets_frame = ttk.LabelFrame(outer, padding=(10, 8))
        self._targets_frame.grid(row=row, column=0, sticky="ew", pady=(10, 0))
        self._targets_frame.columnconfigure(0, weight=1)

        toolbar = ttk.Frame(self._targets_frame)
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure(1, weight=1)
        self._status_label = ttk.Label(toolbar, style="Target.TLabel")
        self._status_label.grid(row=0, column=0, sticky="w")
        bulk = ttk.Frame(toolbar)
        bulk.grid(row=0, column=2, sticky="e")
        self._patch_all_btn = ttk.Button(bulk, command=self._on_patch_all)
        self._patch_all_btn.grid(row=0, column=0, padx=(0, 6))
        self._restore_all_btn = ttk.Button(bulk, command=self._on_restore_all)
        self._restore_all_btn.grid(row=0, column=1)

        rows_host = ttk.Frame(self._targets_frame)
        rows_host.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        rows_host.columnconfigure(0, weight=1)
        for index, key in enumerate(TARGET_ORDER):
            self._build_target_row(rows_host, key, index)
        row += 1

        # --- Tools and About, side by side ----------------------------------
        mid = ttk.Frame(outer)
        mid.grid(row=row, column=0, sticky="ew", pady=(10, 0))
        mid.columnconfigure(0, weight=1)
        mid.columnconfigure(1, weight=1)

        self._tools_frame = ttk.LabelFrame(mid, padding=(10, 8))
        self._tools_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self._tools_frame.columnconfigure(0, weight=1)
        self._tools_frame.columnconfigure(1, weight=1)
        tool_commands = {
            "refresh": self.refresh,
            "open_releases": lambda: self._open_url(RELEASES_URL),
            "open_issues": lambda: self._open_url(ISSUES_URL),
            "star_repo": lambda: self._open_url(GITHUB_URL),
            "check_updates": self._on_check_updates,
        }
        for index, (tool_key, command) in enumerate(tool_commands.items()):
            button = ttk.Button(self._tools_frame, command=command)
            button.grid(row=index // 2, column=index % 2, sticky="ew", padx=3, pady=3)
            self._tools_buttons[tool_key] = button

        self._about_frame = ttk.LabelFrame(mid, padding=(10, 8))
        self._about_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self._about_frame.columnconfigure(0, weight=1)
        about = self._about_frame
        self._about_brand = ttk.Label(about, style="Target.TLabel")
        self._about_brand.grid(row=0, column=0, sticky="w")
        self._about_version = ttk.Label(about, style="Muted.TLabel")
        self._about_version.grid(row=1, column=0, sticky="w")
        self._about_body_label = ttk.Label(about, style="Muted.TLabel", wraplength=400, justify="left")
        self._about_body_label.grid(row=2, column=0, sticky="ew", pady=(4, 4))
        self._about_license = ttk.Label(about, style="Muted.TLabel")
        self._about_license.grid(row=3, column=0, sticky="w")
        self._about_repo = ttk.Label(about, style="Muted.TLabel")
        self._about_repo.grid(row=4, column=0, sticky="w")
        self._about_telegram = ttk.Label(about, style="Muted.TLabel")
        self._about_telegram.grid(row=5, column=0, sticky="w")
        about_buttons = ttk.Frame(about)
        about_buttons.grid(row=6, column=0, sticky="w", pady=(6, 0))
        repo_btn = ttk.Button(about_buttons, command=lambda: self._open_url(GITHUB_URL))
        repo_btn.grid(row=0, column=0, padx=(0, 6))
        telegram_btn = ttk.Button(about_buttons, command=lambda: self._open_url(TELEGRAM_URL))
        telegram_btn.grid(row=0, column=1)
        self._about_buttons = {"repo": repo_btn, "telegram": telegram_btn}
        row += 1

        # --- Log panel (bottom, ~10 rows tall) -------------------------------
        self._log_frame = ttk.LabelFrame(outer, padding=(10, 8))
        self._log_frame.grid(row=row, column=0, sticky="nsew", pady=(10, 0))
        self._log_frame.columnconfigure(0, weight=1)
        self._log_frame.rowconfigure(1, weight=1)
        outer.rowconfigure(row, weight=1)

        log_toolbar = ttk.Frame(self._log_frame)
        log_toolbar.grid(row=0, column=0, columnspan=2, sticky="ew")
        log_toolbar.columnconfigure(0, weight=1)
        # The shared catalog has no dedicated "clear" key yet; tr() falls back
        # to the key itself and picks up a translation if one is ever added.
        self._clear_btn = ttk.Button(log_toolbar, command=self._on_clear_log, text=L("clear"))
        self._clear_btn.grid(row=0, column=1, sticky="e")

        log_scroll = ttk.Scrollbar(self._log_frame, orient="vertical")
        log_scroll.grid(row=1, column=1, sticky="ns")
        text_kwargs = {
            "height": 10,
            "wrap": "word",
            "state": "disabled",
            "borderwidth": 1,
            "relief": "solid",
            "yscrollcommand": log_scroll.set,
        }
        if self._fonts.get("body"):
            text_kwargs["font"] = self._fonts["body"]
        self._log = tk.Text(self._log_frame, **text_kwargs)
        self._log.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        log_scroll.configure(command=self._log.yview)
        self._log.tag_configure("body")
        self._log.tag_configure("hint", foreground="#8a8f98")
        if self._fonts.get("small"):
            self._log.tag_configure("hint", font=self._fonts["small"])

    def _build_target_row(self, parent, key, index):
        """One target row: name + version, dim path line, badge and buttons."""
        frame = ttk.Frame(parent, padding=(2, 5))
        frame.grid(row=index * 2, column=0, sticky="ew")
        frame.columnconfigure(0, weight=1)

        left = ttk.Frame(frame)
        left.grid(row=0, column=0, sticky="ew")
        left.columnconfigure(0, weight=1)

        name_line = ttk.Frame(left)
        name_line.grid(row=0, column=0, sticky="ew")
        name = ttk.Label(name_line, style="Target.TLabel")
        name.grid(row=0, column=0, sticky="w")
        version = ttk.Label(name_line, style="Muted.TLabel")
        version.grid(row=0, column=1, sticky="w", padx=(10, 0))
        name_line.columnconfigure(2, weight=1)

        path = ttk.Label(left, style="Muted.TLabel", cursor="hand2")
        path.grid(row=1, column=0, sticky="ew", pady=(1, 0))
        # Tooltip-free full path: clicking the dim path line logs it verbatim.
        path.bind("<Button-1>", lambda _event, k=key: self._on_path_click(k))

        badge = ttk.Label(frame, style="Badge.TLabel", width=14, anchor="center")
        badge.grid(row=0, column=1, padx=(10, 12))

        actions = ttk.Frame(frame)
        actions.grid(row=0, column=2, sticky="e")
        patch_btn = ttk.Button(actions, width=9, command=lambda k=key: self._on_patch(k))
        patch_btn.grid(row=0, column=0, padx=(0, 4))
        restore_btn = ttk.Button(actions, width=9, command=lambda k=key: self._on_restore(k))
        restore_btn.grid(row=0, column=1, padx=(0, 4))
        browse_btn = ttk.Button(actions, width=12, command=lambda k=key: self._on_pick_path(k))
        browse_btn.grid(row=0, column=2)

        self._row_widgets[key] = {
            "name": name,
            "version": version,
            "path": path,
            "status": badge,
            "patch": patch_btn,
            "restore": restore_btn,
            "browse": browse_btn,
        }
        if index < len(TARGET_ORDER) - 1:
            ttk.Separator(parent, orient="horizontal").grid(row=index * 2 + 1, column=0, sticky="ew", pady=2)

    def _apply_fonts(self):
        """Install the resolved fonts on the ttk styles and the log widget."""
        style = ttk.Style(self.root)
        fonts = self._fonts or {}
        if fonts.get("body"):
            for name in ("TLabel", "TButton", "TCombobox"):
                _try_style(style, name, font=fonts["body"])
        if fonts.get("brand"):
            _try_style(style, "Brand.TLabel", font=fonts["brand"], foreground="#16324f")
        if fonts.get("small"):
            _try_style(style, "Tagline.TLabel", font=fonts["small"], foreground="#5f6b76")
            _try_style(style, "Muted.TLabel", font=fonts["small"], foreground="#6b7280")
        if fonts.get("bold"):
            _try_style(style, "Target.TLabel", font=fonts["bold"])
            _try_style(style, "Badge.TLabel", font=fonts["bold"])
            _try_style(style, "TLabelframe.Label", font=fonts["bold"])

    # --------------------------------------------------------- translation --
    def _retranslate(self):
        """Re-apply every translatable string (startup and live language switch)."""
        # The window title is drawn by the OS title bar, which applies its own
        # bidi/shaping, so it receives the logical tr() text, not L().
        self.root.title("%s — %s" % (i18n.tr("app_brand"), APP_TITLE_SUFFIX))

        self._brand_label.configure(text=L("app_brand"))
        self._tagline_label.configure(text=L("app_tagline"))
        self._lang_label.configure(text=L("language"))

        self._targets_frame.configure(text=L("sec_targets"))
        self._log_frame.configure(text=L("sec_log"))
        self._tools_frame.configure(text=L("sec_tools"))
        self._about_frame.configure(text=L("sec_about"))

        self._status_label.configure(text=L("status_scanning" if self._scan_active else "status_title"))
        self._patch_all_btn.configure(text=L("patch_all"))
        self._restore_all_btn.configure(text=L("restore_all"))

        for key, button in self._tools_buttons.items():
            button.configure(text=L(key))
        for key, button in self._about_buttons.items():
            button.configure(text=L(key))

        for key, widgets in self._row_widgets.items():
            widgets["name"].configure(text=L(TARGET_LABEL_KEYS[key]))
            widgets["patch"].configure(text=L("patch"))
            widgets["restore"].configure(text=L("restore"))
            widgets["browse"].configure(text=L("pick_path"))
        for key in TARGET_ORDER:
            self._update_target_row(key)

        self._about_brand.configure(text=L("app_brand"))
        self._about_version.configure(text="v%s" % VERSION)
        self._about_body_label.configure(text=L("about_body"))
        self._about_license.configure(text=_compose_label("license", LICENSE_ID))
        self._about_repo.configure(text=_compose_label("repo", GITHUB_REPO))
        self._about_telegram.configure(text=_compose_label("telegram", TELEGRAM_URL))
        self._clear_btn.configure(text=L("clear"))

        if self._admin_strip is not None:
            self._admin_strip.configure(text=L("need_admin_note"))

        if self._log_empty:
            self._show_log_hint()
        self._apply_direction()

    def _apply_direction(self):
        """Right-align and right-anchor text for RTL languages.

        Tk mirrors nothing on its own; the static column layout stays, and
        every label flips its text alignment (and the panel titles their
        anchor corner), which is what "anchored/justified right" needs.
        Called on startup and after every language change.
        """
        rtl_active = i18n.is_rtl()
        anchor = "e" if rtl_active else "w"
        justify = "right" if rtl_active else "left"

        self._brand_label.configure(anchor=anchor)
        self._tagline_label.configure(anchor=anchor)
        for widgets in self._row_widgets.values():
            widgets["name"].configure(anchor=anchor)
            widgets["version"].configure(anchor=anchor)
            widgets["path"].configure(anchor=anchor, justify=justify)
        for label in (self._about_brand, self._about_version, self._about_license,
                      self._about_repo, self._about_telegram):
            label.configure(anchor=anchor)
        self._about_body_label.configure(anchor=anchor, justify=justify)

        for frame in (self._targets_frame, self._log_frame, self._tools_frame, self._about_frame):
            try:
                frame.configure(labelanchor="ne" if rtl_active else "nw")
            except Exception:
                pass

        try:
            self._log.tag_configure("body", justify=justify)
            self._log.tag_configure("hint", justify=justify)
        except Exception:
            pass

        if self._admin_strip is not None:
            self._admin_strip.configure(anchor=anchor, justify=justify)

    def _update_target_row(self, key):
        """Refresh the dynamic parts (path, version, badge) of one target row."""
        widgets = self._row_widgets.get(key)
        if not widgets:
            return
        target = self._targets.get(key) or {}
        path_text = target.get("path") or ""
        widgets["path"].configure(text=_display(_middle_truncate(path_text)) if path_text else "")
        version_text = target.get("version") or ""
        widgets["version"].configure(text=_compose_label("version", version_text) if version_text else "")
        status = target.get("status") or "unknown"
        if status not in STATUS_COLORS:
            status = "unknown"
        widgets["status"].configure(text=L(status), foreground=STATUS_COLORS[status])

    def _refresh_rows(self):
        for key in TARGET_ORDER:
            self._update_target_row(key)
        self._refresh_action_states()

    # ---------------------------------------------------------- busy state --
    def _ensure_free(self):
        """Return True when no operation is running, else show the busy dialog."""
        if self._busy:
            messagebox.showwarning(i18n.tr("busy_title"), i18n.tr("busy_msg"), parent=self.root)
            return False
        return True

    def _set_busy(self, busy):
        self._busy = bool(busy)
        self._refresh_action_states()

    def _refresh_action_states(self):
        """Enable/disable action buttons according to target presence and busy."""
        for key in TARGET_ORDER:
            widgets = self._row_widgets.get(key) or {}
            target = self._targets.get(key) or {}
            has_target = bool(target.get("path")) and target.get("status") != "not_found"
            for name in ("patch", "restore"):
                button = widgets.get(name)
                if button is not None:
                    button.state(["!disabled"] if (has_target and not self._busy) else ["disabled"])
            browse = widgets.get("browse")
            if browse is not None:
                browse.state(["!disabled"] if not self._busy else ["disabled"])

        any_target = any(
            bool((self._targets.get(key) or {}).get("path"))
            and (self._targets.get(key) or {}).get("status") != "not_found"
            for key in TARGET_ORDER
        )
        for button in (self._patch_all_btn, self._restore_all_btn):
            button.state(["!disabled"] if (any_target and not self._busy) else ["disabled"])
        for button in list(self._tools_buttons.values()) + list(self._about_buttons.values()):
            button.state(["!disabled"] if not self._busy else ["disabled"])

    # -------------------------------------------------------------- logging --
    def _show_log_hint(self):
        """Show the dim 'log is empty' hint and mark the log empty."""
        try:
            self._log.configure(state="normal")
            self._log.delete("1.0", "end")
            self._log.insert("end", L("log_empty_hint") + "\n", ("hint",))
        finally:
            self._log.configure(state="disabled")
        self._log_empty = True

    def _append_log_text(self, display_text):
        """Append one already display-ready line to the read-only log."""
        try:
            self._log.configure(state="normal")
            if self._log_empty:
                self._log.delete("1.0", "end")
                self._log_empty = False
            self._log.insert("end", display_text + "\n", ("body",))
            self._log.see("end")
        finally:
            self._log.configure(state="disabled")

    def _shape_log_line(self, line):
        """Shape one captured patcher line for Tk (ANSI stripped, RTL visual)."""
        return rtl.visual(strip_ansi(str(line)))

    def _on_clear_log(self):
        self._show_log_hint()

    def _on_path_click(self, key):
        target = self._targets.get(key) or {}
        path = target.get("path") or ""
        if path:
            self._append_log_text(self._shape_log_line(path))

    # --------------------------------------------------------------- events --
    def start(self):
        """Schedule the event pump and kick off the startup discovery scan."""
        try:
            self._poll_after_id = self.root.after(POLL_INTERVAL_MS, self._poll_events)
        except Exception:
            self._poll_after_id = None
        self.refresh()

    def _poll_events(self):
        self._poll_after_id = None
        try:
            self._drain_events()
        finally:
            try:
                if self.root.winfo_exists():
                    self._poll_after_id = self.root.after(POLL_INTERVAL_MS, self._poll_events)
            except Exception:
                self._poll_after_id = None

    def _drain_events(self):
        """Apply every queued worker event.  Main thread only."""
        while True:
            try:
                kind, payload = self._events.get_nowait()
            except queue.Empty:
                break
            try:
                if kind == "log":
                    self._append_log_text(self._shape_log_line(payload))
                elif kind == "scan_done":
                    self._on_scan_done(payload)
                elif kind == "jobs_done":
                    self._on_jobs_done(payload)
                elif kind == "update_done":
                    self._on_update_done(payload)
            except Exception:
                # A broken event must never kill the poller (no tracebacks).
                continue

    # ------------------------------------------------------------- scanning --
    def refresh(self):
        """Start a discovery scan on a worker thread."""
        if not self._ensure_free():
            return
        self._scan_active = True
        self._set_busy(True)
        self._status_label.configure(text=L("status_scanning"))
        overrides = dict(self._overrides)
        self._scan_thread = threading.Thread(target=self._scan_worker, args=(overrides,), daemon=True)
        self._scan_thread.start()

    def _scan_worker(self, overrides):
        try:
            results = discover_targets(overrides)
        except Exception:
            results = {}
        self._events.put(("scan_done", results))

    def _on_scan_done(self, payload):
        payload = payload or {}
        for key in TARGET_ORDER:
            data = payload.get(key) or {}
            self._targets[key] = {
                "path": data.get("path") or "",
                "status": data.get("status") or "unknown",
                "version": data.get("version") or "",
            }
        self._scan_active = False
        self._set_busy(False)
        self._status_label.configure(text=L("status_title"))
        self._refresh_rows()

    # -------------------------------------------------------- patch/restore --
    def _confirm(self, message_key, key):
        return messagebox.askyesno(
            i18n.tr("confirm_title"),
            i18n.tr(message_key, target=i18n.tr(TARGET_LABEL_KEYS[key])),
            parent=self.root,
        )

    def _on_patch(self, key):
        if not self._ensure_free():
            return
        target = self._targets.get(key) or {}
        path = target.get("path") or ""
        if not path or target.get("status") == "not_found":
            messagebox.showerror(i18n.tr("dlg_error_title"), i18n.tr("not_found"), parent=self.root)
            return
        if not self._confirm("confirm_patch_msg", key):
            return
        self._start_jobs([(key, "patch", path)])

    def _on_restore(self, key):
        if not self._ensure_free():
            return
        target = self._targets.get(key) or {}
        path = target.get("path") or ""
        if not path or target.get("status") == "not_found":
            messagebox.showerror(i18n.tr("dlg_error_title"), i18n.tr("not_found"), parent=self.root)
            return
        if not self._confirm("confirm_restore_msg", key):
            return
        self._start_jobs([(key, "restore", path)])

    def _on_patch_all(self):
        self._run_all("patch")

    def _on_restore_all(self):
        self._run_all("restore")

    def _run_all(self, action):
        """Confirm and run an action for every found target, sequentially."""
        if not self._ensure_free():
            return
        message_key = "confirm_patch_msg" if action == "patch" else "confirm_restore_msg"
        jobs = []
        for key in TARGET_ORDER:
            target = self._targets.get(key) or {}
            path = target.get("path") or ""
            if not path or target.get("status") == "not_found":
                continue
            if not self._confirm(message_key, key):
                continue
            jobs.append((key, action, path))
        if jobs:
            self._start_jobs(jobs)

    def _start_jobs(self, jobs):
        if self._busy:
            messagebox.showwarning(i18n.tr("busy_title"), i18n.tr("busy_msg"), parent=self.root)
            return
        self._set_busy(True)
        self._job_thread = threading.Thread(target=self._jobs_worker, args=(list(jobs),), daemon=True)
        self._job_thread.start()

    def _jobs_worker(self, jobs):
        """Run patch/restore jobs with stdout/stderr captured and stubs installed."""
        writer = _QueueWriter(self._events)
        old_stdout, old_stderr = sys.stdout, sys.stderr
        originals = None
        results = []
        sys.stdout = writer
        sys.stderr = writer
        try:
            try:
                originals = _install_interactive_stubs()
            except Exception:
                originals = None
            for key, action, path in jobs:
                running_key = "running_patch" if action == "patch" else "running_restore"
                self._events.put(("log", L(running_key, target=i18n.tr(TARGET_LABEL_KEYS[key]))))
                ok = False
                try:
                    outcome = _run_job(key, action, path)
                    ok = outcome is not False
                except Exception as exc:
                    # Technical detail line; never a traceback on stderr.
                    self._events.put(("log", "%s: %s" % (type(exc).__name__, exc)))
                self._events.put(("log", L("done_ok" if ok else "done_fail")))
                self._events.put(("log", ""))
                results.append((key, action, ok))
        finally:
            writer.close_pending()
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            if originals is not None:
                try:
                    _restore_interactive_stubs(originals)
                except Exception:
                    pass
            self._events.put(("jobs_done", results))

    def _on_jobs_done(self, results):
        results = results or []
        self._set_busy(False)
        self._status_label.configure(text=L("status_title"))
        if results:
            any_failed = any(not entry[2] for entry in results)
            if any_failed:
                messagebox.showerror(i18n.tr("dlg_error_title"), i18n.tr("done_fail"), parent=self.root)
            else:
                messagebox.showinfo(i18n.tr("dlg_success_title"), i18n.tr("done_ok"), parent=self.root)
        # Statuses changed on disk: rescan (this re-enters the busy state).
        self.refresh()

    # ---------------------------------------------------------- path picker --
    def _resolve_picked_path(self, key, chosen):
        """Resolve a manually picked file to the real target file, or ''."""
        try:
            if key == "ide":
                resolved = ide_discovery.resolve_target_path(chosen)
            elif key == "manager":
                resolved = manager_discovery.resolve_manager_path(chosen)
            elif key == "cli":
                resolved = agy_discovery.resolve_agy_path(chosen)
            elif key == "vscode":
                resolved = vscode_discovery.resolve_extension_path(chosen)
            else:
                resolved = agy_discovery.resolve_agy_path(chosen)
        except Exception:
            resolved = ""
        if resolved and os.path.isfile(resolved):
            return resolved
        return ""

    def _on_pick_path(self, key):
        if not self._ensure_free():
            return
        target = self._targets.get(key) or {}
        current = target.get("path") or ""
        options = {}
        initial_dir = os.path.dirname(current) if current else ""
        if initial_dir and os.path.isdir(initial_dir):
            options["initialdir"] = initial_dir
        # Native dialog: logical Unicode title (the OS applies bidi itself).
        options["title"] = i18n.tr("pick_path")
        options["filetypes"] = tuple(PICK_FILETYPES.get(key, ())) + (("*.*", "*.*"),)
        try:
            chosen = filedialog.askopenfilename(parent=self.root, **options)
        except Exception:
            chosen = ""
        if not chosen:
            return
        resolved = self._resolve_picked_path(key, chosen)
        if not resolved:
            messagebox.showerror(i18n.tr("dlg_error_title"), i18n.tr("done_fail"), parent=self.root)
            return
        self._overrides[key] = resolved
        self.refresh()

    # --------------------------------------------------------------- tools ---
    def _open_url(self, url):
        if not self._ensure_free():
            return
        try:
            webbrowser.open(url)
        except Exception:
            self._append_log_text(L("done_fail"))

    def _on_check_updates(self):
        if not self._ensure_free():
            return
        self._set_busy(True)
        threading.Thread(target=self._update_worker, daemon=True).start()

    def _update_worker(self):
        try:
            available = update_utils.check_for_updates(silent=True)
            result = update_utils.get_last_update_result()
        except Exception as exc:
            available, result = False, ("error", str(exc))
        self._events.put(("update_done", (available, result)))

    def _on_update_done(self, payload):
        available, result = False, None
        if isinstance(payload, tuple) and len(payload) >= 2:
            available, result = payload[0], payload[1]
        self._set_busy(False)
        if available and isinstance(result, tuple) and result and result[0] == "update_available":
            tag = result[1] if len(result) > 1 else ""
            self._append_log_text(L("updates_available", tag=tag, version=VERSION))
            messagebox.showinfo(
                i18n.tr("dlg_success_title"),
                i18n.tr("updates_available", tag=tag, version=VERSION),
                parent=self.root,
            )
        elif result == "up_to_date":
            self._append_log_text(L("updates_latest", version=VERSION))
            messagebox.showinfo(
                i18n.tr("dlg_success_title"),
                i18n.tr("updates_latest", version=VERSION),
                parent=self.root,
            )
        else:
            self._append_log_text(L("done_fail"))
            messagebox.showerror(i18n.tr("dlg_error_title"), i18n.tr("done_fail"), parent=self.root)

    # ------------------------------------------------------------ language ---
    def _on_language_selected(self, _event=None):
        index = self._lang_combo.current()
        if index < 0 or index >= len(self._lang_codes):
            return
        if not i18n.set_language(self._lang_codes[index]):
            return
        self._retranslate()
        self._append_log_text(L("lang_changed_hint"))

    # -------------------------------------------------------------- close ----
    def _on_close(self):
        if self._poll_after_id is not None:
            try:
                self.root.after_cancel(self._poll_after_id)
            except Exception:
                pass
            self._poll_after_id = None
        try:
            self.root.destroy()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _apply_window_icon(root):
    """Use source/icon.ico when present; never fail on a missing icon."""
    try:
        if os.path.isfile(ICON_PATH):
            root.iconbitmap(ICON_PATH)
    except Exception:
        pass


def run_gui():
    """Open the patcher window (module import stays side-effect free)."""
    rtl.set_mode("visual")
    root = tk.Tk()
    root.geometry("1000x700")
    root.minsize(880, 620)
    _apply_window_icon(root)
    app = PatcherGUI(root)
    app.start()
    root.mainloop()


if __name__ == "__main__":
    run_gui()
