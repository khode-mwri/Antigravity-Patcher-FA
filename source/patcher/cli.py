import os
import sys
import webbrowser
import locale

from patcher.constants import (
    COLOR_CYAN,
    COLOR_GREEN,
    COLOR_YELLOW,
    COLOR_RED,
    COLOR_BOLD,
    COLOR_DIM,
    COLOR_WHITE,
    COLOR_UNDERLINE,
    DOWNLOAD_URL,
    VERSION,
    GITHUB_URL,
    GITHUB_REPO,
    TELEGRAM_URL,
    TELEGRAM_HANDLE,
)
from patcher.utils.console import (
    color,
    link,
    clear_screen,
    print_banner,
    print_menu_section,
    print_menu_row,
    print_menu_divider,
    print_menu_footer,
    info,
    hint,
    ok,
    warn,
    err,
    cancel,
)

from patcher.utils.file import file_size, format_bytes
from patcher.utils.update import check_for_updates, open_releases_page, print_update_status_notice

from patcher.ide.discovery import (
    find_install_root,
    find_main_js,
    get_ag_version,
    resolve_target_path,
)
from patcher.ide.patcher import is_already_patched, do_patch, do_restore
from patcher.agy.discovery import find_agy_binary, resolve_agy_path
from patcher.agy.patcher import is_already_patched as is_agy_patched, do_patch_agy, do_restore_agy

from patcher.manager.discovery import find_manager_binary, resolve_manager_path, get_antigravity_version
from patcher.manager.patcher import is_already_patched as is_mgr_patched, do_patch_manager, do_restore_manager

from patcher.vscode.discovery import (
    find_extension_js,
    resolve_extension_path,
    find_gemini_antigravity_binary,
    describe_gemini_binary_path,
)
from patcher.vscode.patcher import (
    is_already_patched as is_vscode_patched,
    do_patch_vscode,
    do_restore_vscode,
)


def pause(prompt="  برای بازگشت به منو Enter را بزنید..."):
    print(color(prompt, COLOR_DIM), end="", flush=True)
    if os.name == "nt":
        import msvcrt
        try:
            while msvcrt.kbhit():
                msvcrt.getch()
            while True:
                ch = msvcrt.getch()
                if ch in (b"\r", b"\n"):
                    break
        except Exception:
            input()
    else:
        try:
            import tty
            import termios
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                while True:
                    ch = sys.stdin.read(1)
                    if ch in ("\r", "\n"):
                        break
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except Exception:
            input()
    print()



def print_launch_examples():
    script_name = os.path.basename(sys.argv[0]) or "main.py"
    cmd = script_name if getattr(sys, "frozen", False) else f"python {script_name}"
    windows_example = f'{cmd} "C:\\Path\\To\\Antigravity IDE"'
    macos_example = f'{cmd} "/Applications/Antigravity IDE.app"'
    linux_example = f'{cmd} "/usr/share/antigravity-ide"'

    hint("نمونهٔ اجرا با مسیر دستی:")
    print(f"      Windows: {color(windows_example, COLOR_YELLOW)}")
    print(f"      macOS:   {color(macos_example, COLOR_YELLOW)}")
    print(f"      Linux:   {color(linux_example, COLOR_YELLOW)}")


def print_path_examples():
    windows_path = r"C:\Users\Name\AppData\Local\Programs\Antigravity IDE"
    macos_path = "/Applications/Antigravity IDE.app"
    linux_path = "/usr/share/antigravity-ide"

    hint("نمونهٔ مسیرها:")
    print(f"      Windows: {color(windows_path, COLOR_YELLOW)}")
    print(f"      macOS:   {color(macos_path, COLOR_YELLOW)}")
    print(f"      Linux:   {color(linux_path, COLOR_YELLOW)}")


def _read_console_line(prompt):
    print(prompt, end="", flush=True)

    stdin_buffer = getattr(sys.stdin, "buffer", None)
    if stdin_buffer is None:
        return sys.stdin.readline().rstrip("\r\n")

    raw = stdin_buffer.readline()
    if not raw:
        return ""

    encodings = [
        sys.stdin.encoding,
        locale.getpreferredencoding(False),
        "utf-8",
        "cp1251",
        "latin-1",
    ]
    for encoding in [e for e in encodings if e]:
        try:
            return raw.decode(encoding).rstrip("\r\n")
        except UnicodeDecodeError:
            pass

    return raw.decode("utf-8", errors="replace").rstrip("\r\n")


def prompt_yn(question):
    question = question.rstrip()
    prompt = f"  [?] {question} ({color('y', COLOR_GREEN)}/{color('n', COLOR_RED)}): "
    return _read_console_line(prompt).strip().lower()


def confirmed(question):
    """Возвращает True, если пользователь ответил 'y'."""
    return prompt_yn(question) in ("y", "yes", "\u0434", "\u0434\u0430", "ب", "بله")


def offer_download_and_block(software_name="Antigravity", target_type=None):
    err(f"مسیر {software_name} تنظیم نشده یا نرم‌افزار نصب نیست.")
    err("تلاش برای پچ کردن مسدود شد.")
    hint(f"لینک دانلود: {color(DOWNLOAD_URL, COLOR_CYAN)}")
    print()
    print_menu_row("1", "باز کردن صفحهٔ دانلود", "در مرورگر", COLOR_GREEN)
    print_menu_row("2", f"تعیین مسیر {software_name} نصب‌شده", "انتخاب دستی", COLOR_CYAN)
    print_menu_row("0", "بازگشت به منوی اصلی", "", COLOR_RED)
    print()

    action = input(color("  گزینه را انتخاب کنید > ", COLOR_CYAN, COLOR_BOLD)).strip()
    if action == "1":
        webbrowser.open(DOWNLOAD_URL)
        ok(f"در حال باز کردن: {color(DOWNLOAD_URL, COLOR_CYAN)}")
        return None
    elif action == "2":
        print()
        hint(f"مسیر {software_name} را وارد کنید.")
        print_path_examples()
        raw = input(color(f"\n  مسیر {software_name} > ", COLOR_CYAN, COLOR_BOLD)).strip()
        if raw:
            if target_type == "ide":
                new_path = resolve_target_path(raw)
                if new_path and os.path.isdir(new_path):
                    new_path = find_main_js(new_path)
                if new_path and os.path.isfile(new_path) and new_path.endswith("main.js"):
                    ok(f"مسیر {software_name} به‌روزرسانی شد!")
                    return new_path
                else:
                    err(f"هدف معتبری برای {software_name} پیدا نشد (main.js در آن نیست).")
            elif target_type == "manager":
                new_path = resolve_manager_path(raw)
                if new_path and os.path.isfile(new_path):
                    ok(f"مسیر {software_name} به‌روزرسانی شد!")
                    return new_path
                else:
                    err(f"هدف معتبری برای {software_name} پیدا نشد (language_server در آن نیست).")
            elif target_type == "agy":
                new_path = resolve_agy_path(raw)
                if new_path and os.path.isfile(new_path):
                    ok(f"مسیر {software_name} به‌روزرسانی شد!")
                    return new_path
                else:
                    err(f"هدف معتبری برای {software_name} پیدا نشد.")
            else:
                p = resolve_target_path(raw) or resolve_manager_path(raw) or resolve_agy_path(raw)
                if p and os.path.exists(p):
                    ok("مسیر به‌روزرسانی شد!")
                    return p
                else:
                    err("مسیر واردشده نامعتبر است.")
        return None
    else:
        cancel("لغو شد.")
        return None


def _kv(label, value_text, value_color):
    """Отформатированная пара ключ/значение с выравниванием меток."""
    print(f"      {label:<9}{color(value_text, value_color)}")


def print_target_info(main_js_path, manager_path="", agy_path="", vscode_path="", vscode_agy_path="", show_search_line=False):
    if show_search_line:
        info("در حال جست‌وجوی نصب‌ها...")

    # 1. Antigravity IDE Info
    print_menu_section("اطلاعات ANTIGRAVITY IDE")
    _kv("هدف:", main_js_path if main_js_path else "پیدا نشد", COLOR_CYAN)
    if main_js_path and os.path.exists(main_js_path):
        try:
            with open(main_js_path, "r", encoding="utf-8") as f:
                content = f.read()
            _kv("وضعیت:", "پیدا شد", COLOR_GREEN)
            patched = is_already_patched(content)
            _kv("پچ:", "قبلاً پچ شده" if patched else "پچ نشده",
                COLOR_YELLOW if patched else COLOR_GREEN)
        except Exception:
            _kv("وضعیت:", "غیرقابل‌خواندن", COLOR_RED)
            _kv("پچ:", "غیرقابل‌خواندن", COLOR_RED)

        ver_str, _ = get_ag_version(main_js_path)
        _kv("نسخه:", ver_str if ver_str else "تشخیص داده نشد",
            COLOR_GREEN if ver_str else COLOR_YELLOW)

        size = file_size(main_js_path)
        _kv("حجم:", format_bytes(size), COLOR_GREEN if size > 0 else COLOR_YELLOW)
    else:
        _kv("وضعیت:", "پیدا نشد", COLOR_RED)

    print()

    # 2. Antigravity 2.0 Info
    print_menu_section("اطلاعات ANTIGRAVITY 2.0")
    _kv("هدف:", manager_path if manager_path else "پیدا نشد", COLOR_CYAN)
    if manager_path and os.path.isfile(manager_path):
        _kv("وضعیت:", "پیدا شد", COLOR_GREEN)
        patched = is_mgr_patched(manager_path)
        _kv("پچ:", "قبلاً پچ شده" if patched else "پچ نشده",
            COLOR_YELLOW if patched else COLOR_GREEN)
        
        ver_str = get_antigravity_version(manager_path)
        _kv("نسخه:", ver_str if ver_str else "تشخیص داده نشد",
            COLOR_GREEN if ver_str else COLOR_YELLOW)

        size = file_size(manager_path)
        _kv("حجم:", format_bytes(size), COLOR_GREEN if size > 0 else COLOR_YELLOW)
    else:
        _kv("وضعیت:", "پیدا نشد", COLOR_YELLOW)

    print()

    # 3. Antigravity CLI Info
    print_menu_section("اطلاعات ANTIGRAVITY CLI")
    _kv("هدف:", agy_path if agy_path else "پیدا نشد", COLOR_CYAN)
    if agy_path and os.path.isfile(agy_path):
        _kv("وضعیت:", "پیدا شد", COLOR_GREEN)
        patched = is_agy_patched(agy_path)
        _kv("پچ:", "قبلاً پچ شده" if patched else "پچ نشده",
            COLOR_YELLOW if patched else COLOR_GREEN)
        size = file_size(agy_path)
        _kv("حجم:", format_bytes(size), COLOR_GREEN if size > 0 else COLOR_YELLOW)
    else:
        _kv("وضعیت:", "پیدا نشد", COLOR_YELLOW)

    print()

    # 4. Antigravity VS Code Extension Info (extension.js + бинарь agy)
    print_menu_section("اطلاعات افزونه ANTIGRAVITY VS CODE")
    _kv("هدف:", vscode_path if vscode_path else "پیدا نشد", COLOR_CYAN)
    if vscode_path and os.path.isfile(vscode_path):
        _kv("وضعیت:", "پیدا شد", COLOR_GREEN)
        try:
            with open(vscode_path, "r", encoding="utf-8") as f:
                content = f.read()
            patched = is_vscode_patched(content)
            _kv("پچ:", "قبلاً پچ شده" if patched else "پچ نشده",
                COLOR_YELLOW if patched else COLOR_GREEN)
        except Exception:
            _kv("پچ:", "غیرقابل‌خواندن", COLOR_RED)
        size = file_size(vscode_path)
        _kv("حجم:", format_bytes(size), COLOR_GREEN if size > 0 else COLOR_YELLOW)
    else:
        _kv("وضعیت:", "پیدا نشد", COLOR_YELLOW)

    print()

    _kv("باینری:", vscode_agy_path if vscode_agy_path else "پیدا نشد", COLOR_CYAN)
    if vscode_agy_path and os.path.isfile(vscode_agy_path):
        _kv("وضعیت:", "پیدا شد", COLOR_GREEN)
        patched = is_agy_patched(vscode_agy_path)
        _kv("پچ:", "قبلاً پچ شده" if patched else "پچ نشده",
            COLOR_YELLOW if patched else COLOR_GREEN)
        size = file_size(vscode_agy_path)
        _kv("حجم:", format_bytes(size), COLOR_GREEN if size > 0 else COLOR_YELLOW)
    else:
        _kv("وضعیت:", "پیدا نشد", COLOR_YELLOW)


def show_about():
    clear_screen()
    print_banner()
    print_menu_section("درباره برنامه")
    print()
    print(f"  {color('Antigravity Patcher', COLOR_BOLD, COLOR_CYAN)} v{VERSION}")
    print("  ابزار متن‌باز دور زدن قفل منطقه‌ای برای محصولات Antigravity:")
    print("  Antigravity IDE، Antigravity 2.0 (language_server) و Antigravity CLI (agy).")
    print("  امکان استفاده از Antigravity بدون VPN و بدون تغییر منطقه حساب Google را فراهم می‌کند.")
    print()
    hint("قابلیت‌ها:")
    print(f"   • {color('پچ Antigravity IDE', COLOR_GREEN)}        — دور زدن isGoogleInternal در main.js")
    print(f"   • {color('پچ Antigravity 2.0', COLOR_GREEN)}        — پچ باینری language_server")
    print(f"   • {color('پچ Antigravity CLI', COLOR_GREEN)}        — دور زدن بررسی واجد شرایط بودن حساب در agy")
    print(f"   • {color('پچ افزونهٔ VS Code', COLOR_GREEN)}        — دور زدن extension.js + ~/.gemini/bin/agy")
    print(f"   • {color('بکاپ و بازگردانی', COLOR_GREEN)}         — تغییرات ایمن و کاملاً قابل بازگشت")
    print()
    hint("مخزن و پشتیبانی:")
    repo_link = link(GITHUB_URL, GITHUB_REPO, COLOR_CYAN, COLOR_UNDERLINE)
    tg_link = link(TELEGRAM_URL, TELEGRAM_HANDLE, COLOR_CYAN, COLOR_UNDERLINE)
    print(f"   • GitHub:   {repo_link}  {color('(★ به ما ستاره بدهید!)', COLOR_YELLOW, COLOR_BOLD)}")
    print(f"   • Telegram: {tg_link}")
    print()
    hint("مجوز:")
    attr_link = link("https://github.com/QNIX-Dev/eligibility-antigravity-patcher", "eligibility-antigravity-patcher", COLOR_CYAN, COLOR_UNDERLINE)
    print(f"   • مجوز GPL-3.0 (ارجاع: {attr_link} / MIT)")



def redraw_main_screen(main_js_path, manager_path="", agy_path="", vscode_path="", vscode_agy_path="", show_search_line=False):

    clear_screen()
    print_banner()
    print_target_info(main_js_path, manager_path, agy_path, vscode_path=vscode_path,
                      vscode_agy_path=vscode_agy_path, show_search_line=show_search_line)
    print()
    print_update_status_notice()


def set_vscode_path(new_path):
    """Колбэк для do_patch_vscode_flow — обновляет локальную переменную vscode_path
    в кадре run_cli (через sys._getframe)."""
    frame = sys._getframe(2)
    if frame.f_code.co_name == "run_cli":
        frame.f_locals["vscode_path"] = new_path


def set_vscode_agy_path(new_path):
    """Колбэк для do_patch_vscode_flow — обновляет локальную переменную vscode_agy_path
    в кадре run_cli (через sys._getframe)."""
    frame = sys._getframe(2)
    if frame.f_code.co_name == "run_cli":
        frame.f_locals["vscode_agy_path"] = new_path


def do_patch_vscode_flow(vscode_path, vscode_agy_path, set_js_cb=None, set_agy_cb=None):
    """Патчит расширение google.google-antigravity (extension.js) и бинарь
    ~/.gemini/bin/antigravity (agy) через agy-патчер.

    Патч блокируется, пока не найдены ОБА файла: extension.js и бинарь agy."""
    from patcher.agy.patcher import do_patch_agy

    # --- 0. Предварительный поиск: оба файла должны существовать ---
    if not vscode_path or not os.path.isfile(vscode_path):
        vscode_path = find_extension_js()
        if vscode_path and set_js_cb:
            set_js_cb(vscode_path)

    if not vscode_agy_path or not os.path.isfile(vscode_agy_path):
        vscode_agy_path = find_gemini_antigravity_binary()
        if vscode_agy_path and set_agy_cb:
            set_agy_cb(vscode_agy_path)

    missing = []
    if not vscode_path or not os.path.isfile(vscode_path):
        missing.append("extension.js (افزونهٔ VS Code با شناسهٔ «google.google-antigravity»)")
    if not vscode_agy_path or not os.path.isfile(vscode_agy_path):
        missing.append(f"باینری agy ({describe_gemini_binary_path()})")

    if missing:
        err("پچ افزونهٔ Antigravity VS Code مسدود شد — فایل‌های لازم پیدا نشد:")
        for m in missing:
            err(f"  - {m}")
        hint("ابتدا افزونهٔ «Google Antigravity» را در VS Code نصب کنید")
        hint("(از نمای Extensions، «Antigravity» را جست‌وجو و Install کنید)،")
        hint("یک‌بار آن را اجرا کنید — باینری به‌طور خودکار در ~/.gemini/bin دانلود می‌شود.")
        return False

    # --- 1. Патчим extension.js ---
    do_patch_vscode(vscode_path)

    # --- 2. Патчим бинарь ~/.gemini/bin/antigravity (agy-патчем) ---
    print()
    info(f"باینری دانلودشده پیدا شد: {color(vscode_agy_path, COLOR_CYAN)}")
    do_patch_agy(vscode_agy_path)
    return True


def run_cli():
    main_js_path = ""
    manager_path = ""
    agy_path = ""
    vscode_path = ""
    vscode_agy_path = ""
    searched = False

    # 1. Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        args = [a for a in sys.argv[1:] if a not in ("--rollback", "-r")]
        if args:
            arg = " ".join(args)
            # Пытаемся определить тип цели
            ide_path = resolve_target_path(arg)
            if ide_path and os.path.isdir(ide_path):
                ide_path = find_main_js(ide_path)
            
            if ide_path and os.path.isfile(ide_path) and ide_path.endswith("main.js"):
                main_js_path = ide_path
            else:
                # Пробуем как Antigravity 2.0 (Manager / language_server)
                mgr_path = resolve_manager_path(arg)
                if mgr_path and os.path.isfile(mgr_path):
                    manager_path = mgr_path
                else:
                    # Пробуем как CLI (agy)
                    agy_p = resolve_agy_path(arg)
                    if agy_p and os.path.isfile(agy_p):
                        agy_path = agy_p
                    else:
                        err(f"مسیر داده‌شده وجود ندارد یا نامعتبر است: {arg}")

    # 2. Проверяем текущую директорию (для Antigravity IDE)
    if not main_js_path and not manager_path and not agy_path:
        local = os.path.join(os.getcwd(), "main.js")
        if os.path.exists(local):
            main_js_path = local
            info("main.js در پوشهٔ فعلی پیدا شد")

    # 3. Авто-поиск в системе
    if not main_js_path and not manager_path and not agy_path:
        info("در حال جست‌وجوی نصب‌ها...")
        searched = True

        ide_root = find_install_root()
        if ide_root:
            main_js_path = find_main_js(ide_root)

        manager_path = find_manager_binary()
        agy_path = find_agy_binary()

    # VS Code extension и его бинарь agy ищем всегда — независимо от того,
    # найдены ли остальные цели (это отдельный продукт со своей директорией).
    if not vscode_path or not vscode_agy_path:
        if not searched:
            info("در حال جست‌وجوی نصب‌ها...")
        if not vscode_path:
            vscode_path = find_extension_js()
        if not vscode_agy_path:
            vscode_agy_path = find_gemini_antigravity_binary()

    # Если ничего не нашли вообще, даем выбор между открытием страницы загрузки и вводом пути
    if not main_js_path and not manager_path and not agy_path:
        warn("هیچ نصبی به‌طور خودکار پیدا نشد.")
        hint(f"لینک دانلود: {color(DOWNLOAD_URL, COLOR_CYAN)}")
        print()
        print_menu_row("1", "باز کردن صفحهٔ دانلود", "در مرورگر", COLOR_GREEN)
        print_menu_row("2", "تعیین مسیر نرم‌افزار نصب‌شده", "انتخاب دستی", COLOR_CYAN)
        print_menu_row("0", "فعلاً رد شود (منوی اصلی)", "", COLOR_YELLOW)
        print()

        act = input(color("  گزینه را انتخاب کنید > ", COLOR_CYAN, COLOR_BOLD)).strip()
        if act == "1":
            webbrowser.open(DOWNLOAD_URL)
            ok(f"در حال باز کردن: {color(DOWNLOAD_URL, COLOR_CYAN)}")
            print()
        elif act == "2":
            print()
            hint("مسیر Antigravity IDE، Antigravity 2.0 یا agy را وارد کنید.")
            print_path_examples()
            raw = input(color("\n  مسیر > ", COLOR_CYAN, COLOR_BOLD)).strip()
            if raw:
                ide_path = resolve_target_path(raw)
                if ide_path and os.path.isdir(ide_path):
                    ide_path = find_main_js(ide_path)
                
                if ide_path and os.path.isfile(ide_path) and ide_path.endswith("main.js"):
                    main_js_path = ide_path
                else:
                    mgr_path = resolve_manager_path(raw)
                    if mgr_path and os.path.isfile(mgr_path):
                        manager_path = mgr_path
                    else:
                        agy_p = resolve_agy_path(raw)
                        if agy_p and os.path.isfile(agy_p):
                            agy_path = agy_p

    # Auto-check for updates on startup
    check_for_updates(silent=True)

    redraw_main_screen(main_js_path, manager_path, agy_path, vscode_path=vscode_path,
                       vscode_agy_path=vscode_agy_path, show_search_line=searched)

    while True:
        print_menu_section("پچ")
        print_menu_row("1", "پچ Antigravity IDE", "دور زدن قفل منطقه", COLOR_GREEN)
        print_menu_row("2", "پچ Antigravity 2.0", "پچ language_server", COLOR_GREEN)
        print_menu_row("3", "پچ Antigravity CLI", "رفع قفل ابزار agy", COLOR_GREEN)
        print_menu_row("4", "پچ افزونهٔ VS Code", "extension.js و باینری agy", COLOR_GREEN)

        print_menu_section("بازگردانی")
        print_menu_row("5", "Antigravity IDE", "از بکاپ", COLOR_YELLOW)
        print_menu_row("6", "Antigravity 2.0", "از بکاپ", COLOR_YELLOW)
        print_menu_row("7", "Antigravity CLI", "از بکاپ", COLOR_YELLOW)
        print_menu_row("8", "افزونهٔ Antigravity VS Code", "از بکاپ", COLOR_YELLOW)

        print_menu_section("ابزارها")
        print_menu_row("9", "بررسی به‌روزرسانی", "نسخه‌های GitHub", COLOR_CYAN)
        print_menu_row("10", "ستاره در GitHub", "حمایت از پروژه", COLOR_YELLOW)
        print_menu_row("11", "انتخاب مسیر دستی", "بازنویسی هدف", COLOR_CYAN)
        print_menu_row("12", "درباره برنامه", "نسخه و نویسنده", COLOR_CYAN)

        print()
        print_menu_row("0", "خروج", "خروج از پچر", COLOR_RED)
        print_menu_footer("نکته: اگر این ابزار به کارتان آمد، لطفاً در GitHub به ما ★ بدهید (گزینه ۱۰)!")

        choice = input(color("\n  گزینه را انتخاب کنید > ", COLOR_CYAN, COLOR_BOLD)).strip()
        print()

        if choice == "0":
            return

        # Пустой ввод — не выходим, просто перерисовываем меню
        if choice == "":
            redraw_main_screen(main_js_path, manager_path, agy_path, vscode_path,
                               vscode_agy_path, show_search_line=searched)
            continue

        valid_choices = {str(i) for i in range(1, 13)}
        if choice not in valid_choices:
            err("گزینه نامعتبر")
            print()
            pause()
            redraw_main_screen(main_js_path, manager_path, agy_path, vscode_path,
                               vscode_agy_path, show_search_line=searched)
            continue

        handled = True
        clear_screen()
        print_banner()

        if choice == "1":
            if main_js_path and os.path.isfile(main_js_path):
                do_patch(main_js_path, show_search_line=searched)
            else:
                new_p = offer_download_and_block("آنتی‌گراویتی IDE", target_type="ide")
                if new_p:
                    main_js_path = new_p
                    searched = False
                    do_patch(main_js_path, show_search_line=searched)
        elif choice == "2":
            if manager_path and os.path.isfile(manager_path):
                do_patch_manager(manager_path)
            else:
                new_p = offer_download_and_block("آنتی‌گراویتی 2.0", target_type="manager")
                if new_p:
                    manager_path = new_p
                    searched = False
                    do_patch_manager(manager_path)
        elif choice == "3":
            if agy_path and os.path.isfile(agy_path):
                do_patch_agy(agy_path)
            else:
                new_p = offer_download_and_block("آنتی‌گراویتی CLI", target_type="agy")
                if new_p:
                    agy_path = new_p
                    searched = False
                    do_patch_agy(agy_path)
        elif choice == "4":
            do_patch_vscode_flow(vscode_path, vscode_agy_path,
                                 set_js_cb=set_vscode_path, set_agy_cb=set_vscode_agy_path)
        elif choice == "5":
            if main_js_path:
                do_restore(main_js_path, show_search_line=searched)
            else:
                err("مسیر Antigravity IDE تنظیم نشده است. ابتدا گزینه ۱۱ (انتخاب دستی مسیر) را انتخاب کنید.")
        elif choice == "6":
            if manager_path:
                do_restore_manager(manager_path)
            else:
                err("مسیر Antigravity 2.0 (language_server) تنظیم نشده است. ابتدا گزینه ۱۱ (انتخاب دستی مسیر) را انتخاب کنید.")
        elif choice == "7":
            if agy_path:
                do_restore_agy(agy_path)
            else:
                err("مسیر Antigravity CLI تنظیم نشده است. ابتدا گزینه ۱۱ (انتخاب دستی مسیر) را انتخاب کنید.")
        elif choice == "8":
            if vscode_path:
                do_restore_vscode(vscode_path)
            else:
                err("مسیر افزونهٔ Antigravity VS Code تنظیم نشده است. ابتدا گزینه ۱۱ (انتخاب دستی مسیر) را انتخاب کنید.")
        elif choice == "9":
            check_for_updates(silent=False)
        elif choice == "10":
            print_target_info(main_js_path, manager_path, agy_path, vscode_path=vscode_path,
                              vscode_agy_path=vscode_agy_path, show_search_line=searched)
            print()
            if confirmed("مخزن GitHub در مرورگر باز شود؟"):
                url = GITHUB_URL
                webbrowser.open(url)
                ok(f"در حال باز کردن: {color(url, COLOR_CYAN)}")
            else:
                cancel("لغو شد.")
        elif choice == "11":
            while True:
                redraw_main_screen(main_js_path, manager_path, agy_path, vscode_path,
                                   vscode_agy_path, show_search_line=searched)
                print_menu_section("انتخاب دستی مسیر")
                print_menu_row("1", "مسیر Antigravity IDE", "پوشه یا main.js", COLOR_GREEN)
                print_menu_row("2", "مسیر Antigravity 2.0", "پوشه یا language_server", COLOR_GREEN)
                print_menu_row("3", "مسیر Antigravity CLI", "agy.exe یا پوشه", COLOR_GREEN)
                print_menu_row("4", "مسیر افزونهٔ VS Code", "extension.js یا پوشه", COLOR_GREEN)
                print_menu_row("5", "مسیر باینری agy", "در ~/.gemini/bin", COLOR_GREEN)
                print()
                print_menu_row("0", "بازگشت", "بازگشت به منو", COLOR_RED)
                print_menu_footer("نتایج شناسایی خودکار سایر هدف‌ها دست‌نخورده می‌ماند.")

                sub_choice = input(color("\n  گزینه را انتخاب کنید > ", COLOR_CYAN, COLOR_BOLD)).strip()
                if sub_choice == "0":
                    handled = False
                    break

                if sub_choice == "1":
                     print()
                     hint("مسیر پوشهٔ Antigravity IDE یا فایل main.js را وارد کنید.")
                     print_path_examples()
                     raw = input(color("\n  مسیر IDE > ", COLOR_CYAN, COLOR_BOLD)).strip()
                     if raw:
                         new_path = resolve_target_path(raw)
                         if new_path and os.path.exists(new_path):
                             if os.path.isdir(new_path):
                                 new_path = find_main_js(new_path)
                             if new_path and os.path.isfile(new_path):
                                 main_js_path = new_path
                                 searched = False
                                 ok("مسیر Antigravity IDE به‌روزرسانی شد!")
                             else:
                                 err("هدف معتبری برای Antigravity IDE پیدا نشد (main.js پیدا نشد).")
                         else:
                             err("مسیر وجود ندارد.")
                     print()
                     pause()
                elif sub_choice == "2":
                     print()
                     hint("مسیر پوشهٔ برنامه Antigravity 2.0 یا باینری language_server را وارد کنید.")
                     print_path_examples()
                     raw = input(color("\n  مسیر Antigravity 2.0 > ", COLOR_CYAN, COLOR_BOLD)).strip()
                     if raw:
                         new_path = resolve_manager_path(raw)
                         if new_path and os.path.isfile(new_path):
                             manager_path = new_path
                             searched = False
                             ok("مسیر Antigravity 2.0 به‌روزرسانی شد!")
                         else:
                             err("هدف معتبری برای Antigravity 2.0 پیدا نشد (language_server پیدا نشد).")
                     print()
                     pause()
                elif sub_choice == "3":
                     print()
                     hint("مسیر باینری agy (agy.exe) یا پوشهٔ آن را وارد کنید.")
                     print_path_examples()
                     raw = input(color("\n  مسیر AGY > ", COLOR_CYAN, COLOR_BOLD)).strip()
                     if raw:
                         new_path = resolve_agy_path(raw)
                         if new_path and os.path.isfile(new_path):
                             agy_path = new_path
                             searched = False
                             ok("مسیر Antigravity CLI به‌روزرسانی شد!")
                         else:
                             err("هدف معتبری برای Antigravity CLI پیدا نشد.")
                     print()
                     pause()
                elif sub_choice == "4":
                     print()
                     hint("مسیر فایل extension.js، پوشهٔ افزونهٔ google.google-antigravity-*")
                     hint("یا ریشهٔ پوشهٔ .vscode/extensions را وارد کنید.")
                     raw = input(color("\n  مسیر افزونهٔ VS Code (JS) > ", COLOR_CYAN, COLOR_BOLD)).strip()
                     if raw:
                         new_path = resolve_extension_path(raw)
                         if new_path and os.path.isfile(new_path):
                             vscode_path = new_path
                             searched = False
                             ok("مسیر افزونهٔ Antigravity VS Code به‌روزرسانی شد!")
                         else:
                             err("هدف معتبری برای افزونهٔ VS Code پیدا نشد (extension.js پیدا نشد).")
                     print()
                     pause()
                elif sub_choice == "5":
                     print()
                     hint(f"مسیر باینری agy/antigravity دانلودشده")
                     hint(f"توسط افزونه ({describe_gemini_binary_path()}) یا هر فایلی به نام agy را وارد کنید.")
                     raw = input(color("\n  مسیر باینری VS Code (agy) > ", COLOR_CYAN, COLOR_BOLD)).strip()
                     if raw:
                         new_path = resolve_agy_path(raw)
                         if new_path and os.path.isfile(new_path):
                             vscode_agy_path = new_path
                             searched = False
                             ok("مسیر باینری agy در VS Code به‌روزرسانی شد!")
                         else:
                             err("هدف معتبری برای باینری agy در VS Code پیدا نشد.")
                     print()
                     pause()
            handled = True
        elif choice == "12":
            show_about()

        print()

        if handled:
            pause()
        redraw_main_screen(main_js_path, manager_path, agy_path, vscode_path,
                           vscode_agy_path, show_search_line=searched)
