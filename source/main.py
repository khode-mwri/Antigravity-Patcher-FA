import sys
import os
import shlex
import shutil
import subprocess

from patcher.utils.admin import is_admin, run_as_admin
from patcher.utils.console import setup_console, emit, ask
from patcher.cli import run_cli, confirmed

RTL_MODES = ("visual", "raw")
RTL_CALIBRATION_SAMPLE = "نمونهٔ متن فارسی: پچ آنتی‌گراویتی — رفع تحریم و قفل منطقه‌ای"

_YES_ANSWERS = ("", "y", "yes", "ب", "بله")


def _extract_rtl_flag(argv):
    """Pull the optional --rtl/--no-rtl switch out of the argument list.

    Supported forms: --rtl visual | --rtl=raw | --no-rtl | --rtl auto
    Returns (mode or None, remaining argv).
    """
    mode = None
    rest = []
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg in ("--no-rtl", "--raw-rtl"):
            mode = "raw"
        elif arg.startswith("--rtl="):
            mode = arg.split("=", 1)[1].strip().lower() or "auto"
        elif arg == "--rtl":
            if index + 1 < len(argv) and not argv[index + 1].startswith("-"):
                mode = argv[index + 1].strip().lower()
                index += 1
            else:
                mode = "auto"
        else:
            rest.append(arg)
        index += 1
    return (mode if mode in RTL_MODES or mode == "auto" else None), rest


def _apply_mode(mode):
    """Apply a rendering mode to both the text transform and the console layout."""
    from patcher.utils import rtl
    from patcher.utils.console import set_render_mode

    rtl.set_mode(mode)
    set_render_mode(mode)


def _calibrate_rtl():
    """Ask the user once which rendering mode is readable in their terminal.

    Terminals without bidi support need the pre-shaped `visual` output, while
    terminals that already apply bidi need the untouched `raw` text and a plain
    (logical-order) layout. Returns the chosen mode, or None when calibration
    could not run / neither mode was readable.
    """
    try:
        emit()
        emit("  [i] کالیبراسیون نمایش فارسی (فقط یک‌بار پرسیده می‌شود)")
        emit("      اگر خط زیر را درست می‌خوانید Enter بزنید؛ اگر برعکس یا ناخوانا بود n بزنید.")
        for mode in RTL_MODES:
            _apply_mode(mode)
            emit()
            emit("      " + RTL_CALIBRATION_SAMPLE)
            answer = ask("  آیا این خط راست‌به‌چپ و خوانا است؟ (y/n): ").strip().lower()
            if answer in _YES_ANSWERS:
                emit()
                return mode
        _apply_mode("visual")
        emit()
        emit("  [!] This terminal cannot display Persian text.")
        emit("      Use Windows Terminal, or run with: --rtl raw")
        emit("      (or set the environment variable AG_PATCHER_RTL=raw)")
        emit()
        return None
    except (EOFError, KeyboardInterrupt, OSError):
        _apply_mode("visual")
        return None


def _setup_rtl(requested_mode):
    """Choose the RTL rendering mode: CLI flag > environment > saved choice > calibration."""
    from patcher.utils import rtl

    if not rtl.AVAILABLE:
        emit("  [!] کتابخانه‌های نمایش فارسی (arabic-reshaper/python-bidi) نصب نیستند؛")
        emit("      متن فارسی ناخوانا می‌شود. اجرا کنید: pip install -r requirements.txt")
        return

    env_mode = os.environ.get("AG_PATCHER_RTL", "").strip().lower()
    if requested_mode in RTL_MODES:
        _apply_mode(requested_mode)
        return
    if env_mode in RTL_MODES:
        _apply_mode(env_mode)
        return

    rtl_prefs = None
    saved = None
    try:
        from patcher.utils import rtl_prefs as _prefs
        rtl_prefs = _prefs
        saved = rtl_prefs.load_mode()
    except Exception:
        rtl_prefs = None
    if saved in RTL_MODES:
        _apply_mode(saved)
        return

    chosen = _calibrate_rtl()
    if chosen in RTL_MODES:
        _apply_mode(chosen)
        if rtl_prefs is not None:
            try:
                rtl_prefs.save_mode(chosen)
            except Exception:
                pass


def _ensure_interactive_terminal():
    """If launched by double-clicking in a GUI without an attached terminal on macOS/Linux,
    automatically re-launch inside the system's Terminal window."""
    if os.name != "posix" or os.environ.get("AG_PATCHER_TERMINAL") == "1":
        return
    try:
        if sys.stdin.isatty() or sys.stdout.isatty():
            return
    except Exception:
        return

    cmd_args = [sys.executable] + (sys.argv[1:] if getattr(sys, "frozen", False) else sys.argv)
    quoted_cmd = " ".join(shlex.quote(a) for a in cmd_args)
    env = os.environ.copy()
    env["AG_PATCHER_TERMINAL"] = "1"

    if sys.platform == "darwin":
        apple_cmd = f"clear; AG_PATCHER_TERMINAL=1 sudo {quoted_cmd}"
        escaped = apple_cmd.replace("\\", "\\\\").replace('"', '\\"')
        subprocess.Popen([
            "/usr/bin/osascript",
            "-e", 'tell application "Terminal" to activate',
            "-e", f'tell application "Terminal" to do script "{escaped}"',
        ], env=env)
        sys.exit(0)

    if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
        shell_line = f"AG_PATCHER_TERMINAL=1 sudo {quoted_cmd}; exec bash"
        terminals = [
            ("gnome-terminal", ["gnome-terminal", "--", "bash", "-c", shell_line]),
            ("ptyxis", ["ptyxis", "--", "bash", "-c", shell_line]),
            ("kgx", ["kgx", "-e", f"bash -c {shlex.quote(shell_line)}"]),
            ("konsole", ["konsole", "-e", "bash", "-c", shell_line]),
            ("xfce4-terminal", ["xfce4-terminal", "-x", "bash", "-c", shell_line]),
            ("mate-terminal", ["mate-terminal", "-x", "bash", "-c", shell_line]),
            ("tilix", ["tilix", "-e", f"bash -c {shlex.quote(shell_line)}"]),
            ("kitty", ["kitty", "bash", "-c", shell_line]),
            ("alacritty", ["alacritty", "-e", "bash", "-c", shell_line]),
            ("x-terminal-emulator", ["x-terminal-emulator", "-e", f"bash -c {shlex.quote(shell_line)}"]),
            ("xterm", ["xterm", "-e", "bash", "-c", shell_line]),
        ]
        for bin_name, launch_args in terminals:
            if shutil.which(bin_name):
                try:
                    subprocess.Popen(launch_args, env=env)
                    sys.exit(0)
                except Exception:
                    continue


if __name__ == "__main__":
    _ensure_interactive_terminal()
    setup_console()
    requested_rtl, clean_args = _extract_rtl_flag(sys.argv[1:])
    sys.argv = [sys.argv[0]] + clean_args
    if requested_rtl in RTL_MODES:
        # Let a possible elevated re-launch inherit the explicit choice.
        os.environ["AG_PATCHER_RTL"] = requested_rtl
    if os.name == "nt" and os.environ.get("SKIP_ELEVATION") != "1" and not is_admin():
        if run_as_admin():
            sys.exit(0)
        else:
            emit("  [!] دسترسی مدیریتی دریافت نشد. ممکن است اسکریپت در تغییر فایل‌ها ناموفق بماند.")
    elif os.name == "posix" and not is_admin():
        emit("  [!] دسترسی root برای پچ کردن فایل‌ها در پوشهٔ ریشه لازم است.")
        if confirmed("با sudo دوباره اجرا شود؟"):
            try:
                if getattr(sys, "frozen", False):
                    args = ["sudo", sys.executable] + sys.argv[1:]
                else:
                    args = ["sudo", sys.executable] + sys.argv
                os.execvp("sudo", args)
            except Exception as e:
                emit(f"  [!] اجرای دوباره با sudo ناموفق بود: {e}")
                sys.exit(1)
        else:
            from patcher.constants import COLOR_YELLOW
            from patcher.utils.console import color
            emit(color("  [!] بدون root ادامه می‌دهیم. احتمال خطای نوشتن وجود دارد.", COLOR_YELLOW))
            emit()

    _setup_rtl(requested_rtl)

    try:
        run_cli()
    except KeyboardInterrupt:
        emit("\n  [i] در حال خروج...")
        sys.exit(0)
    except (PermissionError, OSError) as e:
        # Страховка от необработанного traceback как на скриншоте
        # (бэкап language_server.agybak -> Errno 1 Operation not permitted):
        # вместо "Failed to execute script 'main'" показываем понятную подсказку.
        emit(f"\n  [!] خطای فایل‌سیستم: {e}")
        import sys as _sys

        if _sys.platform == "darwin":
            emit("  [i] macOS نوشتن داخل Antigravity.app را مسدود کرد.")
            emit("  [i] Antigravity را ببندید و دوباره با sudo اجرا کنید:")
            emit("        sudo python3 main.py   (یا sudo ./Antigravity_Patcher_macOS)")
            emit("  [i] اگر همچنان «Operation not permitted» می‌گوید، فلگ‌ها را بررسی کنید:")
            emit("        ls -lO /Applications/Antigravity.app/Contents/resources/bin/language_server")
        else:
            emit("  [i] دسترسی نوشتن وجود ندارد — با دسترسی admin/root دوباره اجرا کنید و ابتدا Antigravity را ببندید.")
        sys.exit(1)
    except Exception as e:
        emit(f"\n  [!] خطای پیش‌بینی‌نشده: {e}")
        from patcher.constants import GITHUB_REPO
        emit(f"  [i] لطفاً آن را گزارش کنید: https://github.com/{GITHUB_REPO}/issues")
        sys.exit(1)