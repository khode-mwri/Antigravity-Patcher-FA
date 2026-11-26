import os
import re
import shutil
import filecmp

from patcher.constants import COLOR_CYAN, COLOR_GREEN, COLOR_YELLOW
from patcher.utils.console import (
    color,
    info,
    hint,
    ok,
    warn,
    err,
    step,
    print_panel,
)
from patcher.utils.file import (
    file_hash,
    file_size,
    format_bytes,
    fix_posix_permissions,
)
from patcher.utils.update import handle_patch_failure
from patcher.utils.console import emit

BAK_EXT = ".vscodebak"

# ---------------------------------------------------------------------------
# PART 1 — маркер и оригинальная строка в extension.js
PART1_ANCHOR = "outputChannel.appendLine('[INSTALL] Checking Antigravity releases...');"

# Гибкий regex для PART 1: допускает разные кавычки и пробелы, но требует
# ПОЛНЫЙ вызов appendLine — вместе с закрывающей скобкой и опциональной ';'.
# Это гарантирует, что вставка попадёт ПОСЛЕ вызова, а не внутри него.
# Группа 1 — весь вызов целиком (точка вставки = m.end(1)).
PART1_ANCHOR_RE = re.compile(
    r"(outputChannel\s*\.\s*appendLine\s*\(\s*"            # outputChannel.appendLine(
    r"(['\"])\[INSTALL\]\s*Checking Antigravity releases[^'\"]*\2"  # 'строка-маркер'
    r"\s*\)\s*;?)"                                         # ) или );
)

# Инъекция: если бинарь уже скачан (targetPathOverride или ~/.gemini/bin),
# пропускаем проверку версии и повторное скачивание.
PART1_INJECT = (
    "{const __primary=options.targetPathOverride||getInstalledTargetPath();"
    "const __candidates=[__primary,"
    "(0,path_1.join)((0,path_1.dirname)(__primary),'antigravity'+((0,path_1.extname)(__primary)||''))];"
    "for(const __p of __candidates){if(__p&&await pathExists(__p)){"
    "outputChannel.appendLine('[INSTALL] Existing binary found at '+__p+'. "
    "Skipping version check and re-download.');return __p;}}}"
)

# PART 2 — строка проверки смены канала заменяется на константу false,
# чтобы расширение не считало канал изменённым и не перекачивало бинарь.
# Строгий regex: ровно три идентификатора (manifestFetched, lastInstalledUrl,
# releaseBaseUrl) в известном порядке — не цепляет посторонние выражения вида
# `const X = a && b !== c;`.
PART2_RE = re.compile(
    r"const\s+isChannelChanged\s*=\s*"
    r"manifestFetched\s*&&\s*lastInstalledUrl\s*!==\s*releaseBaseUrl\s*;"
)
PART2_DONE_RE = re.compile(r"const\s+isChannelChanged\s*=\s*false\s*;")
PART2_REPLACEMENT = "const isChannelChanged = false;"


def is_already_patched(content):
    """True, если обе части патча уже применены к extension.js."""
    return (PART1_INJECT in content) and ("const isChannelChanged = false;" in content)


def _apply_part1(content):
    """Возвращает (новый_контент, статус). Статус: 'applied'|'already'|'not-found'."""
    if PART1_INJECT in content:
        return content, "already"
    m = PART1_ANCHOR_RE.search(content)
    if m:
        insert_at = m.end(1)
        new_content = content[:insert_at] + PART1_INJECT + content[insert_at:]
        return new_content, "applied"
    # Фолбэк: точный поиск по маркеру (на случай экзотического форматирования)
    idx = content.find(PART1_ANCHOR)
    if idx == -1:
        return content, "not-found"
    insert_at = idx + len(PART1_ANCHOR)
    new_content = content[:insert_at] + PART1_INJECT + content[insert_at:]
    return new_content, "applied"


def _apply_part2(content):
    """Возвращает (новый_контент, статус)."""
    if PART2_DONE_RE.search(content):
        # Уже пропатчено; но если рядом остался оригинальный вариант — это другой
        # экземпляр, обрабатываем его ниже.
        new_content, n = PART2_RE.subn(PART2_REPLACEMENT, content)
        if n:
            return new_content, "applied"
        return content, "already"
    new_content, n = PART2_RE.subn(PART2_REPLACEMENT, content)
    if not n:
        return content, "not-found"
    return new_content, "applied"


def _make_backup(path):
    bak = path + BAK_EXT
    if os.path.exists(bak):
        if filecmp.cmp(path, bak, shallow=False):
            return
        info(f"بکاپ قدیمی است (افزونه به‌روزرسانی شده) — در حال تازه‌سازی {os.path.basename(path)}{BAK_EXT}")
    else:
        info(f"در حال ایجاد بکاپ: {os.path.basename(path)}{BAK_EXT}")
    shutil.copy2(path, bak)
    fix_posix_permissions(bak)
    ok(f"بکاپ: {os.path.basename(bak)} ({format_bytes(file_size(bak))})")


def do_patch_vscode(extension_js_path):
    """Патчит extension.js расширения google.google-antigravity (PART 1 + PART 2)."""
    from patcher.cli import confirmed

    if not extension_js_path or not os.path.isfile(extension_js_path):
        err("extension.js افزونهٔ Antigravity VS Code پیدا نشد.")
        hint("افزونهٔ «Google Antigravity» را در VS Code نصب کنید و یک بار اجرا کنید.")
        return False

    path = extension_js_path
    info(f"هدف: {color(path, COLOR_CYAN)}")
    hint(f"حجم: {color(format_bytes(file_size(path)), COLOR_CYAN)}")
    emit()

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        err(f"خطای خواندن: {e}")
        handle_patch_failure()
        return False

    already = is_already_patched(content)

    new_content, s1 = _apply_part1(content)
    new_content, s2 = _apply_part2(new_content)

    statuses = [s1, s2]
    if all(s == "not-found" for s in statuses):
        err("الگوهای پچ در extension.js پیدا نشد (نسخهٔ افزونه پشتیبانی نمی‌شود؟).")
        handle_patch_failure()
        return False

    if all(s in ("already", "not-found") for s in statuses) and already:
        hint("extension.js قبلاً پچ شده است (هر دو بخش).")
        if not confirmed("به هر حال پچ اعمال شود؟"):
            return True
        # re-patch: пересобираем из бэкапа, если он есть, иначе просто продолжаем
        bak = path + BAK_EXT
        if os.path.isfile(bak):
            try:
                with open(bak, "r", encoding="utf-8") as f:
                    new_content = f.read()
            except Exception as e:
                warn(f"خواندن بکاپ برای پچ دوباره ممکن نشد: {e}")
        new_content, s1 = _apply_part1(new_content)
        new_content, s2 = _apply_part2(new_content)

    changed = new_content != content
    if changed:
        try:
            _make_backup(path)
        except (PermissionError, OSError) as e:
            err(f"خطای بکاپ: {e}")
            hint("پنجره‌های VS Code را ببندید و دوباره تلاش کنید. اگر با root نصب شده، با sudo دوباره اجرا کنید.")
            handle_patch_failure()
            return False
        try:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(new_content)
        except PermissionError as e:
            err(f"خطای نوشتن (فایل قفل است؟): {e}")
            hint("پنجره‌های VS Code را ببندید و دوباره تلاش کنید.")
            handle_patch_failure()
            return False
        except Exception as e:
            err(f"خطای نوشتن: {e}")
            handle_patch_failure()
            return False

    applied_parts = sum(1 for s in statuses if s in ("applied", "already"))
    emit()
    step("پچ افزونهٔ Antigravity VS Code", bool(changed or already),
         f"{applied_parts} از 2 بخش")
    emit()
    panel_rows = [
        ("هدف", os.path.basename(os.path.dirname(path))),
        ("فایل", os.path.basename(path)),
        ("بخش ۱", {"applied": "تزریق محافظ رد کردن دانلود",
                    "already": "قبلاً پچ شده",
                    "not-found": "الگو پیدا نشد"}[s1]),
        ("بخش ۲", {"applied": "isChannelChanged -> false",
                    "already": "قبلاً پچ شده",
                    "not-found": "الگو پیدا نشد"}[s2]),
    ]
    hash_before = file_hash(path)
    panel_rows.append(("هش", f"{hash_before[:8]}...{hash_before[56:]}" if hash_before else "n/a"))
    print_panel("پچ با موفقیت انجام شد" if (changed or already) else "پچ لازم نبود", panel_rows, show_star=bool(changed or already))
    if changed:
        hint("برای اعمال تغییر، پنجرهٔ VS Code را دوباره بارگذاری کنید (Developer: Reload Window).")
    return True


def do_restore_vscode(extension_js_path):
    """Восстанавливает extension.js из бэкапа .vscodebak, а также бинарь
    в ~/.gemini/bin (antigravity/agy) из его .agybak, если тот был пропатчен
    пунктом 'Antigravity VS Code Patch'."""
    from patcher.cli import confirmed

    if not extension_js_path or not os.path.isfile(extension_js_path):
        err("extension.js افزونهٔ Antigravity VS Code پیدا نشد.")
        return

    path = extension_js_path
    bak = path + BAK_EXT
    if not os.path.exists(bak):
        warn(f"بکاپی برای {os.path.basename(path)} وجود ندارد (چیزی برای بازگردانی نیست).")
        return

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        err(f"خطای خواندن: {e}")
        return

    if not is_already_patched(content):
        warn("extension.js پچ نشده است — بازگردانی رد شد (ممکن است بکاپ مربوط به بیلد دیگری باشد).")
        if not confirmed("به هر حال از بکاپ بازگردانی شود؟"):
            hint("بازگردانی لغو شد.")
            return

    if not confirmed("extension.js افزونهٔ Antigravity VS Code از بکاپ بازگردانی شود؟"):
        hint("بازگردانی لغو شد.")
        return

    hash_before = file_hash(path)
    try:
        shutil.copy2(bak, path)
        fix_posix_permissions(path)
    except PermissionError as e:
        err(f"خطای بازگردانی (فایل قفل است؟): {e}")
        hint("پنجره‌های VS Code را ببندید و دوباره تلاش کنید.")
        return
    except Exception as e:
        err(f"خطای بازگردانی: {e}")
        return

    hash_after = file_hash(path)
    emit()
    panel_rows = [("هدف", os.path.basename(path))]
    if hash_before and hash_after and hash_before != hash_after:
        panel_rows.append(("قبل", f"{hash_before[:8]}...{hash_before[56:]}"))
        panel_rows.append(("بعد", f"{hash_after[:8]}...{hash_after[56:]}"))
    print_panel("بازگردانی با موفقیت انجام شد", panel_rows)
    hint("برای اعمال تغییر، پنجرهٔ VS Code را دوباره بارگذاری کنید (Developer: Reload Window).")

    # --- Восстановление бинаря в ~/.gemini/bin (пропатчен agy-патчером) ---
    from patcher.vscode.discovery import find_gemini_antigravity_binary
    from patcher.agy.patcher import do_restore_agy

    gemini_bin = find_gemini_antigravity_binary()
    if gemini_bin and os.path.exists(gemini_bin + ".agybak"):
        emit()
        info(f"بکاپ فایل اجرایی (باینری) پچ‌شده پیدا شد: {color(gemini_bin, COLOR_CYAN)}")
        do_restore_agy(gemini_bin)
    elif gemini_bin:
        hint(f"فایل اجرایی (باینری) {os.path.basename(gemini_bin)} در ~/.gemini/bin بکاپ ندارد — چیزی برای بازگردانی نیست.")
