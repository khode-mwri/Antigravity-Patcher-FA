import sys
import os
import shlex
import shutil
import subprocess

from patcher.utils.admin import is_admin, run_as_admin
from patcher.utils.console import setup_console
from patcher.cli import run_cli, confirmed


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
    if os.name == "nt" and os.environ.get("SKIP_ELEVATION") != "1" and not is_admin():
        if run_as_admin():
            sys.exit(0)
        else:
            print("  [!] Could not elevate privileges. The script may fail to modify files.")
    elif os.name == "posix" and not is_admin():
        print("  [!] Root access is required to patch files in the root directory.")
        if confirmed("Re-launch with sudo?"):
            try:
                if getattr(sys, "frozen", False):
                    args = ["sudo", sys.executable] + sys.argv[1:]
                else:
                    args = ["sudo", sys.executable] + sys.argv
                os.execvp("sudo", args)
            except Exception as e:
                print(f"  [!] Failed to re-launch with sudo: {e}")
                sys.exit(1)
        else:
            from patcher.constants import COLOR_YELLOW
            from patcher.utils.console import color
            print(color("  [!] Proceeding without root. Write errors are possible.", COLOR_YELLOW))
            print()

    try:
        run_cli()
    except KeyboardInterrupt:
        print("\n  [i] Exiting...")
        sys.exit(0)
    except (PermissionError, OSError) as e:
        # Страховка от необработанного traceback как на скриншоте
        # (бэкап language_server.agybak -> Errno 1 Operation not permitted):
        # вместо "Failed to execute script 'main'" показываем понятную подсказку.
        print(f"\n  [!] Filesystem error: {e}")
        import sys as _sys

        if _sys.platform == "darwin":
            print("  [i] macOS blocked writing inside Antigravity.app.")
            print("  [i] Close Antigravity and re-run with sudo:")
            print("        sudo python3 main.py   (or sudo ./Antigravity_Patcher_macOS)")
            print("  [i] If it still says 'Operation not permitted', check flags:")
            print("        ls -lO /Applications/Antigravity.app/Contents/resources/bin/language_server")
        else:
            print("  [i] No write access — re-run as admin/root and close Antigravity first.")
        sys.exit(1)
    except Exception as e:
        print(f"\n  [!] Unexpected error: {e}")
        from patcher.constants import GITHUB_REPO
        print(f"  [i] Please report it: https://github.com/{GITHUB_REPO}/issues")
        sys.exit(1)