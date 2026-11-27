"""Trilingual UI strings (English, Persian, Russian) for the GUI patcher.

The module is deliberately dependency-free: it imports from the Python
standard library only and never imports another :mod:`patcher` module, so the
GUI layer can use it without risking import cycles.

Public API
----------
* :data:`LANGUAGES` / :func:`available_languages` -- supported languages.
* :func:`set_language` / :func:`get_language` -- process-wide active language.
* :func:`is_rtl` -- whether the active language is right-to-left (Persian).
* :func:`tr` -- translate a key for the active language, falling back to
  English and then to the key itself.  Formatting is best-effort: a missing
  format argument or a malformed template never raises.

Importing this module has no side effects; the active language always starts
as :data:`DEFAULT_LANGUAGE`.
"""

from __future__ import annotations

import string
from typing import Any

__all__ = [
    "DEFAULT_LANGUAGE",
    "EN",
    "FA",
    "LANGUAGES",
    "RU",
    "available_languages",
    "get_language",
    "is_rtl",
    "set_language",
    "tr",
]

#: Supported language codes and their display labels, in display order.
LANGUAGES: dict[str, str] = {
    "en": "English",
    "fa": "فارسی",
    "ru": "Русский",
}

#: Language used on import and as the translation fallback.
DEFAULT_LANGUAGE: str = "en"

EN: dict[str, str] = {
    "app_brand": "Antigravity Patcher FA",
    "app_tagline": "Region-lock bypass for Antigravity products — Persian edition",
    "language": "Language",
    "refresh": "Refresh",
    "browse": "Browse...",
    "cancel": "Cancel",
    "close": "Close",
    "clear": "Clear",
    "status_title": "Detected installations",
    "status_scanning": "Scanning for installations...",
    "found": "Found",
    "not_found": "Not found",
    "patched": "Patched",
    "not_patched": "Not patched",
    "unknown": "Unknown",
    "version": "Version",
    "path": "Path",
    "size": "Size",
    "backup_available": "Backup available",
    "sec_targets": "Targets",
    "sec_log": "Activity log",
    "sec_tools": "Tools",
    "sec_about": "About",
    "target_ide": "Antigravity IDE",
    "target_manager": "Antigravity 2.0 (language_server)",
    "target_cli": "Antigravity CLI (agy)",
    "target_vscode": "VS Code extension (extension.js)",
    "target_vscode_binary": "VS Code binary (agy)",
    "patch": "Patch",
    "restore": "Restore",
    "patch_all": "Patch all",
    "restore_all": "Restore all",
    "pick_path": "Pick path",
    "detected_auto": "auto-detected",
    "confirm_title": "Confirm",
    "confirm_patch_msg": "Patch {target}?",
    "confirm_restore_msg": "Restore {target} from backup?",
    "running_patch": "Patching {target}...",
    "running_restore": "Restoring {target}...",
    "done_ok": "Operation finished successfully.",
    "done_fail": "Operation failed — see the log.",
    "already_patched_note": "Already patched.",
    "no_backup_note": "No backup found.",
    "need_admin_note": "Administrator rights are required to modify files.",
    "busy_title": "Please wait",
    "busy_msg": "Another operation is still running.",
    "open_releases": "Open releases page",
    "open_issues": "Open issues page",
    "star_repo": "Star on GitHub",
    "check_updates": "Check for updates",
    "updates_latest": "You are on the latest version (v{version}).",
    "updates_available": "New version available: {tag} (current v{version}).",
    "telegram": "Telegram",
    "repo": "GitHub repository",
    "license": "License",
    "about_body": (
        "Open-source patcher for Antigravity IDE, 2.0, CLI and the VS Code "
        "extension. Local files only — no keys, no tokens, no telemetry."
    ),
    "log_empty_hint": "Run an action to see its output here.",
    "lang_changed_hint": "Language changed.",
    "dlg_success_title": "Success",
    "dlg_error_title": "Error",
}

FA: dict[str, str] = {
    "app_brand": "پچر آنتی‌گراویتی",
    "app_tagline": "دور زدن قفل منطقه‌ای محصولات آنتی‌گراویتی — نسخه فارسی",
    "language": "زبان",
    "refresh": "تازه‌سازی",
    "browse": "مرور…",
    "cancel": "انصراف",
    "close": "بستن",
    "clear": "پاک کردن",
    "status_title": "نصب‌های شناسایی‌شده",
    "status_scanning": "در حال جستجوی نصب‌ها…",
    "found": "یافت شد",
    "not_found": "یافت نشد",
    "patched": "پچ‌شده",
    "not_patched": "پچ‌نشده",
    "unknown": "نامشخص",
    "version": "نسخه",
    "path": "مسیر",
    "size": "حجم",
    "backup_available": "پشتیبان موجود است",
    "sec_targets": "هدف‌ها",
    "sec_log": "گزارش فعالیت",
    "sec_tools": "ابزارها",
    "sec_about": "درباره",
    "target_ide": "Antigravity IDE",
    "target_manager": "Antigravity 2.0 (language_server)",
    "target_cli": "Antigravity CLI (agy)",
    "target_vscode": "افزونه VS Code (extension.js)",
    "target_vscode_binary": "فایل اجرایی VS Code (agy)",
    "patch": "پچ",
    "restore": "بازیابی",
    "patch_all": "پچ همه",
    "restore_all": "بازیابی همه",
    "pick_path": "انتخاب مسیر",
    "detected_auto": "شناسایی خودکار",
    "confirm_title": "تأیید",
    "confirm_patch_msg": "پچ {target}؟",
    "confirm_restore_msg": "بازیابی {target} از نسخه پشتیبان؟",
    "running_patch": "در حال پچ {target}…",
    "running_restore": "در حال بازیابی {target}…",
    "done_ok": "عملیات با موفقیت انجام شد.",
    "done_fail": "عملیات ناموفق بود — گزارش را ببینید.",
    "already_patched_note": "از قبل پچ شده است.",
    "no_backup_note": "نسخه پشتیبان یافت نشد.",
    "need_admin_note": "برای تغییر فایل‌ها به دسترسی مدیر نیاز است.",
    "busy_title": "لطفاً صبر کنید",
    "busy_msg": "عملیات دیگری هنوز در حال اجراست.",
    "open_releases": "باز کردن صفحه انتشارها",
    "open_issues": "باز کردن صفحه مشکلات",
    "star_repo": "ستاره دادن در GitHub",
    "check_updates": "بررسی به‌روزرسانی‌ها",
    "updates_latest": "شما از آخرین نسخه (v{version}) استفاده می‌کنید.",
    "updates_available": "نسخه جدید موجود است: {tag} (نسخه فعلی v{version}).",
    "telegram": "تلگرام",
    "repo": "مخزن GitHub",
    "license": "مجوز",
    "about_body": (
        "پچر متن‌باز برای Antigravity IDE، Antigravity 2.0، CLI و "
        "افزونه VS Code. فقط فایل‌های محلی — بدون کلید، بدون توکن، "
        "بدون تلمتری."
    ),
    "log_empty_hint": "برای دیدن خروجی، یک عملیات اجرا کنید.",
    "lang_changed_hint": "زبان تغییر کرد.",
    "dlg_success_title": "موفقیت",
    "dlg_error_title": "خطا",
}

RU: dict[str, str] = {
    "app_brand": "Antigravity Patcher FA (перс.)",
    "app_tagline": "Обход региональной блокировки продуктов Antigravity — персидская версия",
    "language": "Язык",
    "refresh": "Обновить",
    "browse": "Обзор...",
    "cancel": "Отмена",
    "close": "Закрыть",
    "clear": "Очистить",
    "status_title": "Обнаруженные установки",
    "status_scanning": "Поиск установок...",
    "found": "Найдено",
    "not_found": "Не найдено",
    "patched": "Пропатчено",
    "not_patched": "Не пропатчено",
    "unknown": "Неизвестно",
    "version": "Версия",
    "path": "Путь",
    "size": "Размер",
    "backup_available": "Есть резервная копия",
    "sec_targets": "Цели",
    "sec_log": "Журнал действий",
    "sec_tools": "Инструменты",
    "sec_about": "О программе",
    "target_ide": "Antigravity IDE",
    "target_manager": "Antigravity 2.0 (language_server)",
    "target_cli": "Antigravity CLI (agy)",
    "target_vscode": "Расширение VS Code (extension.js)",
    "target_vscode_binary": "Бинарный файл VS Code (agy)",
    "patch": "Пропатчить",
    "restore": "Восстановить",
    "patch_all": "Пропатчить всё",
    "restore_all": "Восстановить всё",
    "pick_path": "Указать путь",
    "detected_auto": "определено автоматически",
    "confirm_title": "Подтверждение",
    "confirm_patch_msg": "Пропатчить {target}?",
    "confirm_restore_msg": "Восстановить {target} из резервной копии?",
    "running_patch": "Патчинг {target}...",
    "running_restore": "Восстановление {target}...",
    "done_ok": "Операция успешно завершена.",
    "done_fail": "Операция не удалась — см. журнал.",
    "already_patched_note": "Уже пропатчено.",
    "no_backup_note": "Резервная копия не найдена.",
    "need_admin_note": "Для изменения файлов требуются права администратора.",
    "busy_title": "Подождите",
    "busy_msg": "Другая операция всё ещё выполняется.",
    "open_releases": "Открыть страницу релизов",
    "open_issues": "Открыть страницу проблем",
    "star_repo": "Поставить звезду на GitHub",
    "check_updates": "Проверить обновления",
    "updates_latest": "У вас последняя версия (v{version}).",
    "updates_available": "Доступна новая версия: {tag} (текущая v{version}).",
    "telegram": "Telegram",
    "repo": "Репозиторий GitHub",
    "license": "Лицензия",
    "about_body": (
        "Открытый патчер для Antigravity IDE, 2.0, CLI и расширения VS Code. "
        "Только локальные файлы — без ключей, без токенов, без телеметрии."
    ),
    "log_empty_hint": "Запустите действие, чтобы увидеть его вывод здесь.",
    "lang_changed_hint": "Язык изменён.",
    "dlg_success_title": "Успех",
    "dlg_error_title": "Ошибка",
}

_CATALOGS: dict[str, dict[str, str]] = {"en": EN, "fa": FA, "ru": RU}

#: Accepted spellings (besides the codes themselves) for :func:`set_language`.
_ALIASES: dict[str, str] = {
    "en": "en",
    "fa": "fa",
    "persian": "fa",
    "farsi": "fa",
    "ru": "ru",
    "russian": "ru",
}

_current_language: str = DEFAULT_LANGUAGE


class _Placeholder(str):
    """A missing format argument that survives ``str.format`` unchanged."""

    def __format__(self, format_spec: str) -> str:
        return str(self)


class _SafeFormatter(string.Formatter):
    """``string.Formatter`` variant that tolerates missing format arguments."""

    def get_value(
        self, key: int | str, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> Any:
        try:
            return super().get_value(key, args, kwargs)
        except (KeyError, IndexError):
            if isinstance(key, int):
                return _Placeholder("{%d}" % key)
            return _Placeholder("{%s}" % key)


_FORMATTER = _SafeFormatter()


def _normalize_language(code: object) -> str | None:
    """Map *code* (a language code or alias, any case) to a supported code."""
    if not isinstance(code, str):
        return None
    return _ALIASES.get(code.strip().casefold())


def _lookup(key: object, language: str) -> str | None:
    """Return the catalog entry for *key*, or ``None`` when it is absent."""
    catalog = _CATALOGS.get(language)
    if catalog is None or not isinstance(key, str):
        return None
    return catalog.get(key)


def set_language(code: str) -> bool:
    """Activate *code* and return ``True``; unknown values are ignored.

    ``code`` is matched case-insensitively and may also be one of the aliases
    ``persian``/``farsi`` (for ``fa``) or ``russian`` (for ``ru``).  When the
    value is not recognised the current language is left unchanged and
    ``False`` is returned.
    """
    global _current_language
    normalized = _normalize_language(code)
    if normalized is None:
        return False
    _current_language = normalized
    return True


def get_language() -> str:
    """Return the active language code (``"en"`` until changed)."""
    return _current_language


def is_rtl() -> bool:
    """Return ``True`` only when the active language is Persian (``fa``)."""
    return _current_language == "fa"


def available_languages() -> list[tuple[str, str]]:
    """Return the supported ``(code, label)`` pairs in display order."""
    return list(LANGUAGES.items())


def tr(key: str, **kwargs: Any) -> str:
    """Translate *key* for the active language.

    Lookup order: active language, then English, then *key* itself.  When
    keyword arguments are supplied the result is formatted with
    ``str.format``; a missing argument (or a malformed template) never
    raises -- the affected placeholder is returned verbatim instead.
    """
    template = _lookup(key, _current_language)
    if template is None:
        template = _lookup(key, DEFAULT_LANGUAGE)
    if template is None:
        template = key if isinstance(key, str) else str(key)
    if not kwargs:
        return template
    try:
        return _FORMATTER.vformat(template, (), kwargs)
    except (KeyError, IndexError, TypeError, ValueError, AttributeError):
        return template
