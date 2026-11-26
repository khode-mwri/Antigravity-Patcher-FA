"""Shared pytest setup for the Antigravity Patcher test suite.

* Puts ``source/`` first on ``sys.path`` so ``import patcher`` / ``import main``
  resolve to the checkout under test without installing anything.
* Pins both rendering layers (``rtl`` and ``console``) to the deterministic
  ``visual`` mode before every test.  The application can persist a user's RTL
  preference in ``rtl_prefs``; a test run on a developer machine must never
  depend on that, and a raw-mode test must not leak into the next test.
"""

import sys
from pathlib import Path

SOURCE_DIR = Path(__file__).resolve().parents[1] / "source"
if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))

import pytest  # noqa: E402  (import after the path setup on purpose)


def _set_visual_mode():
    """Force every rendering layer that exists to visual mode."""
    resetters = []

    try:
        from patcher.utils import rtl
    except Exception:  # pragma: no cover - source tree is broken; tests will fail
        rtl = None
    if rtl is not None:
        set_mode = getattr(rtl, "set_mode", None)
        if set_mode is not None:
            set_mode("visual")
            resetters.append(lambda: set_mode("visual"))

    try:
        from patcher.utils import console
    except Exception:  # pragma: no cover - see above
        console = None
    if console is not None:
        set_render_mode = getattr(console, "set_render_mode", None)
        if set_render_mode is not None:
            set_render_mode("visual")
            resetters.append(lambda: set_render_mode("visual"))

    return resetters


@pytest.fixture(autouse=True)
def deterministic_rendering():
    """Force visual rendering mode around every test (also after failures)."""
    resetters = _set_visual_mode()
    try:
        yield
    finally:
        for reset in resetters:
            reset()
