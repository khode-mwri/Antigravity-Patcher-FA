import json
import sys
import urllib.request
import urllib.error
import webbrowser

from patcher.constants import (
    VERSION, COLOR_CYAN, COLOR_GREEN, COLOR_YELLOW, COLOR_RED, COLOR_BOLD, COLOR_UNDERLINE,
    GITHUB_REPO
)
from patcher.utils.console import print_warning_box, color, link, info, ok, warn, err, hint, _frame_border, _frame_row, emit


RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases"
ISSUES_URL = f"https://github.com/{GITHUB_REPO}/issues"
API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

LAST_UPDATE_RESULT = None


def get_last_update_result():
    return LAST_UPDATE_RESULT


def set_last_update_result(result):
    global LAST_UPDATE_RESULT
    LAST_UPDATE_RESULT = result


def print_network_error_warning(reason="network_error"):
    """Print a noticeable warning and recommendation when check_for_updates fails interactively."""
    if reason == "rate_limited":
        warn("بررسی به‌روزرسانی ممکن نشد (محدودیت نرخ درخواست GitHub).")
        hint("GitHub برای درخواست‌های بدون توکن سهمیهٔ ساعتی دارد؛ چند دقیقه بعد دوباره تلاش کنید.")
    else:
        warn("بررسی به‌روزرسانی ممکن نشد (خطای شبکه).")
        hint("پیشنهاد: اتصال اینترنت یا VPN خود را برای اتصال به GitHub بررسی کنید.")


def print_network_error_banner(reason="network_error"):
    """Print a framed warning banner in the main menu when the update check failed."""
    if reason == "rate_limited":
        title = "بررسی به‌روزرسانی ناموفق — محدودیت GitHub"
        subtitle = "سهمیهٔ ساعتی تمام شد؛ بعداً تلاش کنید"
    else:
        title = "بررسی به‌روزرسانی ناموفق (خطای شبکه)"
        subtitle = "اتصال یا VPN را برای GitHub بررسی کنید"
    print_warning_box(title, subtitle)


def print_update_status_notice():
    """Prints update notice, up-to-date status, or network error warning banner in the main menu."""
    if LAST_UPDATE_RESULT in ("network_error", "rate_limited"):
        print_network_error_banner(LAST_UPDATE_RESULT)
    elif isinstance(LAST_UPDATE_RESULT, tuple) and LAST_UPDATE_RESULT[0] == "update_available":
        _, tag, url = LAST_UPDATE_RESULT
        info(f"نسخهٔ جدید موجود است: {color(tag, COLOR_GREEN, COLOR_BOLD)} (نسخهٔ فعلی: {color(VERSION, COLOR_YELLOW)})")
        hint(f"دانلود: {color(url, COLOR_CYAN)}")
        emit()
    elif LAST_UPDATE_RESULT == "up_to_date":
        ok(f"پچر به‌روز است (v{VERSION})")
        emit()


def _parse_version(v):
    """Parse a version string like '1.2.6' into a tuple of ints."""
    v = v.strip().lstrip("vV")
    parts = []
    for p in v.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            break
    return tuple(parts)


def _fetch_latest_release(timeout=5):
    """Fetch latest release info from GitHub API.

    Returns (tag, html_url, reason); on failure tag is None and reason is either
    "rate_limited" (GitHub 403/429 quota for unauthenticated requests) or
    "network_error" (DNS, TLS, timeout, ...) so the UI can explain the real cause.
    """
    req = urllib.request.Request(API_URL, headers={
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": f"OpenAGPatcher/{VERSION}",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            tag = data.get("tag_name", "")
            html_url = data.get("html_url", "")
            return tag, html_url, None
    except urllib.error.HTTPError as e:
        reason = "rate_limited" if e.code in (403, 429) else "network_error"
        return None, None, reason
    except Exception:
        return None, None, "network_error"


def check_for_updates(silent=True, timeout=5):
    """Check for updates. Returns True if an update is available.

    If silent=True, only prints a message if an update is found.
    If silent=False, always prints the result.
    """
    global LAST_UPDATE_RESULT
    tag, url, reason = _fetch_latest_release(timeout=timeout)

    if tag is None:
        LAST_UPDATE_RESULT = reason or "network_error"
        if not silent:
            print_network_error_warning(LAST_UPDATE_RESULT)
        return False

    current = _parse_version(VERSION)
    latest = _parse_version(tag)

    if latest > current:
        LAST_UPDATE_RESULT = ("update_available", tag, url)
        if not silent:
            info(f"نسخهٔ جدید موجود است: {color(tag, COLOR_GREEN, COLOR_BOLD)} (نسخهٔ فعلی: {color(VERSION, COLOR_YELLOW)})")
            hint(f"دانلود: {color(url, COLOR_CYAN)}")
        return True

    LAST_UPDATE_RESULT = "up_to_date"
    if not silent:
        ok(f"پچر به‌روز است (v{VERSION})")
    return False


def open_releases_page():
    """Open the GitHub releases page in the default browser."""
    webbrowser.open(RELEASES_URL)
    ok(f"در حال باز کردن: {color(RELEASES_URL, COLOR_CYAN)}")


def open_issues_page():
    """Open the GitHub issues page in the default browser."""
    webbrowser.open(ISSUES_URL)
    ok(f"در حال باز کردن: {color(ISSUES_URL, COLOR_CYAN)}")


def handle_patch_failure():
    """Handle patch failure or signature not found.

    Checks for updates:
    - If an update is available, offers to open the releases page to install it.
    - If using the latest version (or no update available), offers to create an issue on GitHub.
    """
    from patcher.cli import confirmed

    emit()
    info("در حال بررسی به‌روزرسانی پچر...")
    has_update = check_for_updates(silent=True)

    if has_update and isinstance(LAST_UPDATE_RESULT, tuple) and LAST_UPDATE_RESULT[0] == "update_available":
        _, tag, url = LAST_UPDATE_RESULT
        info(f"به‌روزرسانی برای Antigravity Patcher موجود است: {color(tag, COLOR_GREEN, COLOR_BOLD)} (نسخهٔ فعلی: {color(VERSION, COLOR_YELLOW)})")
        hint(f"دانلود: {color(url, COLOR_CYAN)}")
        if confirmed("به‌روزرسانی پچر موجود است. می‌خواهید صفحهٔ نسخه‌ها را برای نصب آن باز کنید؟"):
            webbrowser.open(url or RELEASES_URL)
            ok(f"در حال باز کردن: {color(url or RELEASES_URL, COLOR_CYAN)}")
    else:
        if LAST_UPDATE_RESULT == "up_to_date":
            ok(f"شما از آخرین نسخهٔ Antigravity Patcher (v{VERSION}) استفاده می‌کنید.")

        hint(f"پیگیری مشکلات: {color(ISSUES_URL, COLOR_CYAN)}")
        if confirmed("می‌خواهید GitHub را برای ثبت مشکل باز کنید؟"):
            webbrowser.open(ISSUES_URL)
            ok(f"در حال باز کردن: {color(ISSUES_URL, COLOR_CYAN)}")

