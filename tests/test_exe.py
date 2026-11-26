"""Optional smoke test of a *built* console executable.

Set the ``AG_TEST_EXE`` environment variable to the path of an executable built
with PyInstaller (CI's ``exe-smoke`` job does exactly that) and this test runs it
end-to-end: exit code 0, banner, shaped Persian glyphs, no traceback.

Without the variable the test is skipped, so the regular ``pytest`` matrix stays
hermetic and cross-platform.
"""

import os
import re
import subprocess
from pathlib import Path

import pytest

PRESENTATION_FORM_RE = re.compile("[\ufb50-\ufdfe\ufe70-\ufefc]")
EXE_TIMEOUT_SECONDS = 240


def test_built_exe_renders_shaped_persian_and_exits_zero():
    exe = os.environ.get("AG_TEST_EXE", "").strip()
    if not exe:
        pytest.skip("AG_TEST_EXE is not set (no built executable to test)")

    exe_path = Path(exe).expanduser()
    assert exe_path.is_file(), "AG_TEST_EXE does not point to a file: %s" % exe_path

    env = dict(os.environ)
    env.update(
        {
            "SKIP_ELEVATION": "1",  # never try to re-launch elevated
            # Skip the first-run RTL calibration and force shaped output.
            "AG_PATCHER_RTL": "visual",
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
            # Keep the smoke test offline: point the app's update check at a
            # dead local proxy so it fails fast instead of depending on the
            # runner's internet access ("silent" check, never fatal).
            "HTTP_PROXY": "http://127.0.0.1:9",
            "HTTPS_PROXY": "http://127.0.0.1:9",
        }
    )

    # Two answers: "skip" on the no-install prompt (shown when nothing is found;
    # it consumes the first line) and "exit" in the main menu.  With a single
    # "0" the second input() call hits EOF and the app reports an error.
    completed = subprocess.run(
        [str(exe_path)],
        input="0\n0\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=EXE_TIMEOUT_SECONDS,
    )

    combined = (completed.stdout or "") + "\n" + (completed.stderr or "")
    assert completed.returncode == 0, (
        "built executable exited with %d\n--- stdout ---\n%s\n--- stderr ---\n%s"
        % (completed.returncode, completed.stdout, completed.stderr)
    )
    assert "Antigravity" in (completed.stdout or ""), (
        "banner is missing from the executable output:\n%s" % (completed.stdout,)
    )
    assert PRESENTATION_FORM_RE.search(completed.stdout or ""), (
        "the executable output has no shaped Persian glyphs "
        "(arabic-reshaper/python-bidi not bundled?):\n%s" % (completed.stdout,)
    )
    assert "Traceback (most recent call last)" not in combined, (
        "the executable crashed:\n%s" % (combined,)
    )
