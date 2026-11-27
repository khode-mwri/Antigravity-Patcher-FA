"""Headless smoke test for the tkinter GUI.

The GUI is optional to construct: on machines without a display (Linux CI)
``tkinter.Tk()`` raises, so the whole module is skipped there. Where a display
exists (Windows/macOS runners, developer machines) the test builds the real
window with discovery stubbed to "nothing installed", switches language
through all three catalogs and asserts the Persian text gets shaped.
"""

import io
import sys
from contextlib import redirect_stdout

import pytest

from patcher import i18n

pytestmark = pytest.mark.skipif(
    not sys.platform.startswith(("win", "darwin")),
    reason="no display available (Linux CI) — the GUI smoke test needs Tk",
)


def _tk_root():
    tk = pytest.importorskip("tkinter")
    try:
        return tk.Tk()
    except Exception as exc:  # pragma: no cover - headless Windows service session
        pytest.skip("Tk cannot open a window here: %r" % (exc,))


def test_gui_builds_and_retranslates_in_three_languages(monkeypatch):
    import gui

    # Stub discovery so nothing on the machine is detected or touched.
    for name in (
        "find_main_js", "find_install_root", "find_manager_binary",
        "find_agy_binary", "find_extension_js", "find_gemini_antigravity_binary",
    ):
        if hasattr(gui, name):
            monkeypatch.setattr(gui, name, lambda *a, **k: "")

    root = _tk_root()
    try:
        app = gui.PatcherGUI(root)
        root.update_idletasks()

        for code in ("en", "fa", "ru", "en"):
            assert i18n.set_language(code) is True
            app._retranslate()
            root.update_idletasks()

        i18n.set_language("fa")
        app._retranslate()
        root.update_idletasks()
        assert i18n.is_rtl() is True
        brand = app.brand_var.get() if hasattr(app, "brand_var") else None
        if brand is not None:
            from patcher.utils import rtl
            assert brand == rtl.visual(i18n.tr("app_brand"))
    finally:
        i18n.set_language("en")
        root.destroy()


def test_gui_module_import_has_no_side_effects():
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        import gui  # noqa: F401
    assert buffer.getvalue() == ""
    assert hasattr(gui, "run_gui")
