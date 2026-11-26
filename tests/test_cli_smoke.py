"""End-to-end smoke test of :func:`patcher.cli.run_cli`.

The interactive Persian CLI is driven with mocked prompts (answer ``"0"`` =
exit) and mocked discovery/network helpers, so the test is hermetic and
deterministic: it must complete without an exception, print the banner, shaped
Persian text and the main menu, and never leak a traceback to stderr.
"""

import io
import re
import sys
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from patcher.utils import console
from patcher.utils import rtl

import patcher.cli as cli

PRESENTATION_FORM_RE = re.compile("[\ufb50-\ufdfe\ufe70-\ufefc]")


def _run_cli():
    """Run run_cli() with everything interactive, local and remote mocked."""
    console.setup_console()  # encoding setup, exactly like main.py does
    stdout, stderr = io.StringIO(), io.StringIO()
    ask_mock = mock.Mock(return_value="0")

    with mock.patch.object(cli, "ask", ask_mock), \
            mock.patch.object(cli, "confirmed", return_value=False), \
            mock.patch.object(cli, "check_for_updates", return_value=False), \
            mock.patch.object(cli, "clear_screen", lambda: None), \
            mock.patch.object(cli, "pause", lambda *args, **kwargs: None), \
            mock.patch.object(cli, "find_install_root", return_value=None), \
            mock.patch.object(cli, "find_manager_binary", return_value=""), \
            mock.patch.object(cli, "find_agy_binary", return_value=""), \
            mock.patch.object(cli, "find_extension_js", return_value=""), \
            mock.patch.object(cli, "find_gemini_antigravity_binary", return_value=""), \
            mock.patch("urllib.request.urlopen",
                       side_effect=AssertionError("network access attempted")), \
            mock.patch.object(sys, "argv", ["main.py"]), \
            redirect_stdout(stdout), redirect_stderr(stderr):
        result = cli.run_cli()

    return result, stdout.getvalue(), stderr.getvalue(), ask_mock


def test_cli_smoke_runs_cleanly_and_renders_persian_ui():
    result, raw_stdout, raw_stderr, ask_mock = _run_cli()

    assert result is None, "run_cli() must return cleanly after option 0"
    assert ask_mock.call_count >= 1, "the CLI never prompted the user"

    clean_stdout = console.strip_ansi(raw_stdout)
    clean_stderr = console.strip_ansi(raw_stderr)

    # no traceback anywhere (a crash inside run_cli would be caught by pytest,
    # but a swallowed traceback/newline would leak into stderr and must not).
    assert "Traceback (most recent call last)" not in raw_stderr
    assert "Traceback (most recent call last)" not in clean_stderr
    assert "Traceback (most recent call last)" not in clean_stdout

    # banner + shaped Persian text
    assert "Antigravity Patcher" in clean_stdout
    assert PRESENTATION_FORM_RE.search(clean_stdout), (
        "the CLI output has no shaped Persian glyphs"
    )

    # main menu: option numbers and shaped labels/hints
    for marker in ("[1]", "[2]", "[12]", "[0]"):
        assert marker in clean_stdout, "main menu option %s is missing" % marker
    assert rtl.visual("خروج") in clean_stdout, "shaped 'exit' label is missing"
    assert rtl.visual("پچ Antigravity IDE") in clean_stdout, "menu label is not shaped"

    # menu section rules use the 51-column layout
    section_rules = [
        line for line in clean_stdout.splitlines() if line.lstrip().startswith("─")
    ]
    assert section_rules, "no menu section rules were rendered"

    # output should be reasonably substantial (banner + info + menu)
    assert len(clean_stdout.splitlines()) >= 30


def test_cli_smoke_stderr_is_clean():
    _, raw_stdout, raw_stderr, _ = _run_cli()
    assert raw_stderr.strip() == "", "run_cli() wrote to stderr: %r" % (raw_stderr,)
    assert raw_stdout.strip() != "", "run_cli() produced no output"
