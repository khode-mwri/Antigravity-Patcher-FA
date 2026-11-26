import os
import sys
import re
import time
import shutil

from patcher.constants import (
    MIN_AG_VERSION,
)
from patcher.utils.console import (
    emit,
    info,
    hint,
    ok,
    warn,
    err,
    step,
    print_panel,
)
from patcher.utils.update import handle_patch_failure
from patcher.utils.admin import terminate_processes
from patcher.utils.file import (
    file_hash,
    file_size,
    format_bytes,
    fix_posix_permissions,
    resign_macos_bundle,
    remove_macos_immutable_flags,
    remove_macos_quarantine,
    find_app_bundle,
)
from patcher.ide.discovery import (
    check_ag_version,
    parse_version_safe,
    VersionStatus,
)

IDE_RE = re.compile(r"(resetIsTierGCPTos\(\),)this\.[A-Za-z_$0-9]+\.isGoogleInternal")
IDE_DONE = "resetIsTierGCPTos(),true"


def _ide_cache_dirs():
    """VS Code CachedData / Code Cache dirs to drop after patching main.js, so the IDE
    recompiles the patched bytes instead of replaying a stale compile cache. The user-data
    folder is the product nameLong ('Antigravity IDE') under each OS's app-data root."""
    home = os.path.expanduser("~")
    if os.name == "nt":
        bases = [os.path.expandvars(p) for p in
                 (r"%USERPROFILE%\scoop\persist\antigravity-ide\data\user-data",
                  r"%APPDATA%\Antigravity IDE")]
    elif sys.platform == "darwin":
        bases = [os.path.join(home, "Library", "Application Support", "Antigravity IDE")]
    else:                                                  # Linux (respect XDG_CONFIG_HOME)
        cfg = os.environ.get("XDG_CONFIG_HOME") or os.path.join(home, ".config")
        bases = [os.path.join(cfg, "Antigravity IDE")]
    dirs = []
    for base in bases:
        dirs += [os.path.join(base, "CachedData"),
                 os.path.join(base, "Code Cache", "js")]
    return dirs


def apply_patches(content, ag_version=None):
    """Применяет патч isGoogleInternal для IDE из manager.py."""
    results = []
    already = is_already_patched(content)
    matches = [m.group(0) for m in IDE_RE.finditer(content)]
    new_content = IDE_RE.sub(r"\1true", content)
    applied = new_content != content

    if applied:
        detail = f"{len(matches)} مورد جایگزین شد"
    elif already:
        detail = "قبلاً پچ شده"
    else:
        detail = "الگو پیدا نشد"

    results.append({
        "Name": "isGoogleInternal -> true (احراز هویت)",
        "Applied": True if (applied or already) else False,
        "Detail": detail,
    })
    return new_content, results


def is_already_patched(content):
    return IDE_DONE in content and not IDE_RE.search(content)


def warn_about_unsafe_backup(main_js_path, installed_version_str=None, current_content=None):
    backup_path = main_js_path + ".bak"
    if not os.path.exists(backup_path):
        return True, False

    backup_size = file_size(backup_path)
    current_size = file_size(main_js_path)
    warnings = []

    if backup_size <= 2048:
        try:
            with open(backup_path, "r", encoding="utf-8") as f:
                backup_content = f.read()
            if len(backup_content.strip()) <= 512:
                warnings.append(
                    f"حجم بکاپ فقط {format_bytes(backup_size)} است و تقریباً خالی به نظر می‌رسد"
                )
        except Exception as e:
            warn(f"خطای بررسی بکاپ: {e}")
            return False, False
    elif backup_size < 4096 or (current_size > 0 and backup_size < current_size // 10):
        warnings.append(
            f"حجم بکاپ بسیار کمتر از حد انتظار است "
            f"({format_bytes(backup_size)} در برابر {format_bytes(current_size)})"
        )

    if not warnings:
        return True, False

    for warning in warnings:
        warn(f"هشدار بکاپ: {warning}")
    warn("بازگردانی این بکاپ ممکن است Antigravity IDE را خراب کند.")
    warn(f"بکاپ نگه داشته شد: {os.path.basename(backup_path)}")
    return True, True


def do_patch(main_js_path, show_search_line=False):
    from patcher.cli import confirmed
    from patcher.utils.captcha import confirm_with_captcha

    if not main_js_path or not os.path.isfile(main_js_path):
        from patcher.cli import offer_download_and_block
        offer_download_and_block("آنتی‌گراویتی IDE", target_type="ide")
        return

    ver_status, ver_str = check_ag_version(main_js_path)
    parsed_version = parse_version_safe(ver_str)

    if ver_status == VersionStatus.TOO_OLD:
        err(f"نسخه پشتیبانی‌نشده: {ver_str}")
        err(f"حداقل نسخه لازم: {MIN_AG_VERSION}")
        hint("لطفاً Antigravity IDE را به‌روزرسانی کنید و دوباره تلاش کنید.")
        if not confirmed("به هر حال ادامه می‌دهید؟"):
            return
    elif ver_status == VersionStatus.NOT_FOUND:
        warn("نسخه Antigravity IDE تشخیص داده نشد (کلید رجیستری پیدا نشد).")
        if not confirmed("بدون بررسی نسخه ادامه می‌دهید؟"):
            return
    elif ver_status == VersionStatus.PARSE_ERROR:
        warn(f"رشته نسخه تجزیه نشد: {ver_str}")
        if not confirmed("به هر حال ادامه می‌دهید؟"):
            return
    # VersionStatus.OK — продолжаем без вопросов

    try:
        with open(main_js_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        err(f"خطای خواندن: {e}")
        return

    current_is_patched = is_already_patched(content)

    if current_is_patched:
        hint("به نظر می‌رسد فایل قبلاً پچ شده است.")
        if not confirm_with_captcha("به هر حال پچ‌های main.js اعمال شود؟"):
            return

    # --- БЭКАП ---
    backup_path = main_js_path + ".bak"

    if not os.path.exists(backup_path) and not current_is_patched:
        info("در حال ایجاد بکاپ...")
        if sys.platform == "darwin":
            app_path = find_app_bundle(main_js_path)
            if app_path:
                remove_macos_immutable_flags(app_path)
                remove_macos_quarantine(app_path)
        try:
            shutil.copy2(main_js_path, backup_path)
            fix_posix_permissions(backup_path)
            ok(f"بکاپ: {os.path.basename(backup_path)} "
               f"({format_bytes(file_size(backup_path))})")
        except PermissionError as e:
            if sys.platform == "darwin":
                warn(f"دسترسی رد شد، پس از حذف فلگ‌ها دوباره تلاش می‌شود...")
                app_path = find_app_bundle(main_js_path)
                if app_path:
                    remove_macos_immutable_flags(app_path)
                    remove_macos_quarantine(app_path)
                try:
                    shutil.copy2(main_js_path, backup_path)
                    fix_posix_permissions(backup_path)
                    ok(f"بکاپ: {os.path.basename(backup_path)} "
                       f"({format_bytes(file_size(backup_path))})")
                except Exception as e2:
                    err(f"خطای بکاپ: {e2}")
                    return
            else:
                err(f"خطای بکاپ: {e}")
                return
        except Exception as e:
            err(f"خطای بکاپ: {e}")
            return
    elif os.path.exists(backup_path):
        hint("بکاپ از قبل وجود دارد — رد شد")
    elif current_is_patched:
        warn("main.js قبلاً پچ شده است — نیازی به بکاپ نیست")

    hash_before = file_hash(main_js_path)

    info("در حال اعمال پچ‌ها...")
    emit()

    new_content, results = apply_patches(content, ag_version=parsed_version)

    applied = 0
    for r in results:
        if r.get("Applied"):
            applied += 1
        step(r["Name"], r.get("Applied", False), r.get("Detail", ""))
    emit()

    if new_content == content and current_is_patched:
        ok("فایل قبلاً پچ شده است — تغییری لازم نیست.")
        return

    if applied == 0:
        err("هیچ پچی اعمال نشد.")
        handle_patch_failure()
        return

    write_success = False
    for attempt in range(2):
        try:
            with open(main_js_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            fix_posix_permissions(main_js_path)
            write_success = True
            break
        except PermissionError as e:
            if attempt == 0:
                if sys.platform == "darwin":
                    warn(f"دسترسی رد شد، پس از حذف فلگ‌ها دوباره تلاش می‌شود...")
                    app_path = find_app_bundle(main_js_path)
                    if app_path:
                        remove_macos_immutable_flags(app_path)
                        remove_macos_quarantine(app_path)
                    time.sleep(0.5)
                    continue
                warn(f"دسترسی رد شد (فایل قفل است): {e}")
                if confirmed("می‌خواهید فرایندهای در حال اجرای Antigravity را خودکار ببندم و دوباره تلاش کنم؟"):
                    terminate_processes(["Antigravity", "Antigravity IDE", "antigravity", "antigravity-ide"])
                    time.sleep(1.5)
                    continue
            err(f"خطای نوشتن (دسترسی رد شد): {e}")
            handle_patch_failure()
            return
        except Exception as e:
            err(f"خطای نوشتن: {e}")
            handle_patch_failure()
            return

    if not write_success:
        handle_patch_failure()
        return

    # Очистка кэша скомпилированных JS файлов VS Code (CachedData / Code Cache)
    info("در حال پاک کردن کش‌های کامپایل IDE...")
    for c in _ide_cache_dirs():
        try:
            if os.path.isdir(c):
                shutil.rmtree(c, ignore_errors=True)
        except Exception:
            pass

    hash_after = file_hash(main_js_path)
    resign_macos_bundle(main_js_path)

    panel_rows = [
        ("هدف", os.path.basename(main_js_path)),
        ("پچ‌ها", f"{applied}/{len(results)} اعمال شد"),
    ]
    if os.path.exists(backup_path):
        panel_rows.append(
            ("بکاپ", f"{os.path.basename(backup_path)} ({format_bytes(file_size(backup_path))})")
        )
    if hash_before and hash_after:
        panel_rows.append(("قبل", f"{hash_before[:8]}...{hash_before[56:]}"))
        panel_rows.append(("بعد", f"{hash_after[:8]}...{hash_after[56:]}"))
    panel_rows.append(("پایان", time.strftime('%H:%M:%S')))
    print_panel("پچ با موفقیت انجام شد", panel_rows, show_star=True)
    hint("Antigravity IDE را دوباره اجرا کنید و وارد حساب شوید.")


def do_restore(main_js_path, show_search_line=False):
    from patcher.cli import confirmed

    current_content = None
    try:
        with open(main_js_path, "r", encoding="utf-8") as f:
            current_content = f.read()
    except Exception:
        pass

    backup_ok, backup_has_warnings = warn_about_unsafe_backup(
        main_js_path, current_content=current_content
    )
    if not backup_ok:
        return

    backup_path = main_js_path + ".bak"

    if not os.path.exists(backup_path):
        err(f"فایل بکاپ پیدا نشد: {backup_path}")
        return
    try:
        with open(backup_path, "r", encoding="utf-8") as f:
            data = f.read()
    except Exception as e:
        err(f"بکاپ خوانده نشد: {e}")
        return

    backup_size = file_size(backup_path)
    if backup_size <= 2048:
        err("بکاپ بسیار کوچک است — ممکن است خراب باشد!")
        if not confirmed("به هر حال بازگردانی شود؟"):
            hint("بازگردانی لغو شد.")
            return

    if is_already_patched(data):
        warn("به نظر می‌رسد خود بکاپ هم پچ شده است!")
        if not confirmed("این بکاپ پچ‌شده بازگردانی شود؟"):
            hint("بازگردانی لغو شد.")
            return

    restore_question = "این بکاپ به هر حال بازگردانی شود؟" if backup_has_warnings else "بکاپ بازگردانی شود؟"
    if not confirmed(restore_question):
        hint("بازگردانی لغو شد.")
        return

    hash_before = file_hash(main_js_path)

    tmp_path = main_js_path + ".tmp"
    try:
        if sys.platform == "darwin":
            app_path = find_app_bundle(main_js_path)
            if app_path:
                remove_macos_immutable_flags(app_path)
                remove_macos_quarantine(app_path)
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(data)
        os.replace(tmp_path, main_js_path)
        fix_posix_permissions(main_js_path)
    except Exception as e:
        if sys.platform == "darwin":
            warn(f"بازگردانی ناموفق بود، پس از حذف فلگ‌ها دوباره تلاش می‌شود...")
            app_path = find_app_bundle(main_js_path)
            if app_path:
                remove_macos_immutable_flags(app_path)
                remove_macos_quarantine(app_path)
            try:
                if not os.path.exists(tmp_path):
                     with open(tmp_path, "w", encoding="utf-8") as f:
                         f.write(data)
                os.replace(tmp_path, main_js_path)
                fix_posix_permissions(main_js_path)
            except Exception as e2:
                err(f"خطای بازگردانی: {e2}")
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
                return
        else:
            err(f"خطای بازگردانی: {e}")
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            return

    hash_after = file_hash(main_js_path)
    resign_macos_bundle(main_js_path)

    panel_rows = [("هدف", os.path.basename(main_js_path))]
    if hash_before and hash_after and hash_before != hash_after:
        panel_rows.append(("قبل", f"{hash_before[:8]}...{hash_before[56:]}"))
        panel_rows.append(("بعد", f"{hash_after[:8]}...{hash_after[56:]}"))
    panel_rows.append(("پایان", time.strftime('%H:%M:%S')))
    print_panel("بازگردانی با موفقیت انجام شد", panel_rows)
