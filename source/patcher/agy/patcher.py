import os
import re
import sys
import errno
import mmap
import shutil
import contextlib
import filecmp

from patcher.constants import COLOR_CYAN
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
    resign_macos_bundle,
    resign_macos_binary,
    ensure_macos_writable,
)
from patcher.utils.update import handle_patch_failure
from patcher.utils.admin import terminate_processes
from patcher.utils.atomic import atomic_replace_posix, apply_patches_to_data
from patcher.utils.console import emit

BAK_EXT = ".agybak"


# ----------------------------------------------------------------------- Gate --
# Байт-сигнатурный патчинг машинного кода Go-бинаря agy/agy.exe.
# Сигнатуры используют re.S, чтобы '.' захватывала также displacement-байт 0x0a.
class Gate:
    def __init__(self, sig, patched, fix, offset=0, desc=""):
        self.sig = re.compile(sig, re.S)
        self.patched = re.compile(patched, re.S)
        self.fix = fix
        self.offset = offset
        self.desc = desc

    def find(self, data):
        """('patched'|'unpatched', [file offsets to write at]).
        LookupError, если сигнатура отсутствует (неизвестный билд).
        Несколько unpatched-вхождений допустимы — патчим все (Go может
        компилировать одну функцию в нескольких экземплярах)."""
        patched_offsets = [m.start() + self.offset for m in self.patched.finditer(data)]
        if patched_offsets:
            return ("patched", patched_offsets)
        unpatched_offsets = [m.start() + self.offset for m in self.sig.finditer(data)]
        if not unpatched_offsets:
            raise LookupError("امضای دروازه پیدا نشد (نسخه پشتیبانی‌نشده؟)")
        return ("unpatched", unpatched_offsets)


    def resolve(self, data):
        """(kind, [write-offsets], concrete-gate). The concrete gate carries the fix bytes
        and label to apply — so a MultiGate can hand back the arch-matching sub-gate."""
        kind, offsets = self.find(data)
        return kind, offsets, self

    def resolve_all(self, data):
        """[(kind, [write-offsets], concrete-gate)] — из одного элемента для Gate."""
        return [self.resolve(data)]


class MultiGate:
    """One logical gate whose machine code differs per CPU arch and per build
    (the CLI eligibility check compiles to distinct instructions on amd64 vs
    arm64, and Apple reshaped it again in 1.2.7), so it declares one Gate
    signature per variant. Architectures never overlap, but one binary CAN
    match several same-arch gates at once (arm64 1.2.7 has both the inline w2
    check in the screen function and the w4 check inside the check helper) —
    every unpatched match must be patched, otherwise the screen survives."""

    def __init__(self, *gates, desc=""):
        self.gates = gates
        self.desc = desc

    def resolve_all(self, data):
        """All matching sub-gates as [(kind, [write-offsets], concrete-gate)].
        LookupError, если ни одна сигнатура не подошла (неизвестный билд)."""
        matches = []
        err = None
        for g in self.gates:
            try:
                matches.append(g.resolve(data))
            except LookupError as e:
                err = e
        if not matches:
            raise err or LookupError("هیچ امضای دروازه‌ای مطابقت نداشت")
        return matches


# ---------------------------------------------------------------------------
# Gate 1: CLI eligibility screen (единственный гейт начальной проверки).
# x64:
#   test rax,rax ; je eligible ; cmp byte[rax+8],0 ; jne eligible ; call failure_builder
# Repeating the non-null test keeps ZF=0, so jne always selects eligible.
# Сигнатура ограничена 16-байтным ядром проверки: хвост (call + register spills)
# варьируется между сборками, поэтому в паттерн не включается.
CLI_GATE_X64 = Gate(
    rb"\x48\x85\xc0\x0f\x84....\x80\x78\x08\x00\x0f\x85....",
    rb"\x48\x85\xc0\x0f\x84....\x48\x85\xc0\x90\x0f\x85....",
    b"\x48\x85\xc0\x90",
    offset=9,
    desc="غیرفعال‌سازی صفحهٔ بررسی واجد شرایط (x64)",
)
# arm64:
#   cbnz x1,error ; cbz x0,eligible ; ldrb w1,[x0,#8] ; tbnz w1,#0,eligible
#   bl failure_builder + spills.
# Loading 1 instead makes tbnz always select eligible.
# Единый строгий гейт покрывает оба известных хвоста:
#   - классика: x0/x1/x2 -> [sp,#0x90]/[sp,#0x60]/[sp,#0x80]
#   - macOS-билд: x0/x1/x2/x3 -> [sp,#0x98]/[sp,#0x60]/[sp,#0x88]/[sp,#0x58]
CLI_GATE_ARM64 = Gate(
    rb"...\xb5...\xb4\x01\x20\x40\x39[\x01\x21\x41\x61\x81\xa1\xc1\xe1].[\x00-\x07]\x37"
    rb"...[\x94-\x97](?:\xe0\x4b\x00\xf9\xe1\x33\x00\xf9\xe2\x43\x00\xf9"
    rb"|\xe0\x4f\x00\xf9\xe1\x33\x00\xf9\xe2\x47\x00\xf9\xe3\x2f\x00\xf9)",
    rb"...\xb5...\xb4\x21\x00\x80\x52[\x01\x21\x41\x61\x81\xa1\xc1\xe1].[\x00-\x07]\x37"
    rb"...[\x94-\x97](?:\xe0\x4b\x00\xf9\xe1\x33\x00\xf9\xe2\x43\x00\xf9"
    rb"|\xe0\x4f\x00\xf9\xe1\x33\x00\xf9\xe2\x47\x00\xf9\xe3\x2f\x00\xf9)",
    b"\x21\x00\x80\x52",
    offset=8,
    desc="غیرفعال‌سازی صفحهٔ بررسی واجد شرایط (arm64)",
)
# arm64 (CLI 1.2.7+): проверка перекомпилирована — внешний cbnz исчез,
# флаг читается в w4, а за tbnz идёт ldp вместо bl+spills:
#   cbz x0,eligible ; ldrb w4,[x0,#8] ; tbnz w4,#0,eligible
#   ldp x4,x5,[x0,#0x48] ...
# mov w4,#1 заставляет существующий tbnz всегда выбирать ветку eligible.
# Отдельный гейт: фикс зависит от регистра (w4, не w1), в один паттерн
# со старым не объединяется. Сигнатура строгая: ровно одно вхождение
# в linux/mac/windows arm64-билдрах 1.2.7 (проверено тестом test_cli_releases).
CLI_GATE_ARM64_W4 = Gate(
    rb"[\x00\x20\x40\x60\x80\xa0\xc0\xe0]..\xb4\x04\x20\x40\x39"
    rb"[\x04\x24\x44\x64\x84\xa4\xc4\xe4].[\x00-\x07]\x37\x04\x94\x44\xa9",
    rb"[\x00\x20\x40\x60\x80\xa0\xc0\xe0]..\xb4\x24\x00\x80\x52"
    rb"[\x04\x24\x44\x64\x84\xa4\xc4\xe4].[\x00-\x07]\x37\x04\x94\x44\xa9",
    b"\x24\x00\x80\x52",
    offset=4,
    desc="غیرفعال‌سازی صفحهٔ بررسی واجد شرایط (arm64, w4)",
)
# arm64 (CLI 1.2.7+, инлайн-проверка в функции экрана) — главный гейт экрана,
# без него экран "Eligibility check failed:" выживает даже с пропатченным w4:
#   cbnz x1,? ; cbz x0,eligible ; ldrb w2,[x0,#8] ; tbnz w2,#0,eligible
#   bl check_helper ...
# mov w2,#1 заставляет tbnz сразу уходить в eligible, не вызывая хелпер.
# Сигнатура строгая: ровно одно вхождение в linux/mac/windows arm64 1.2.7.
CLI_GATE_ARM64_W2 = Gate(
    rb"[\x01\x21\x41\x61\x81\xa1\xc1\xe1]..\xb5[\x00\x20\x40\x60\x80\xa0\xc0\xe0]..\xb4"
    rb"\x02\x20\x40\x39[\x02\x22\x42\x62\x82\xa2\xc2\xe2].[\x00-\x07]\x37...[\x94-\x97]",
    rb"[\x01\x21\x41\x61\x81\xa1\xc1\xe1]..\xb5[\x00\x20\x40\x60\x80\xa0\xc0\xe0]..\xb4"
    rb"\x22\x00\x80\x52[\x02\x22\x42\x62\x82\xa2\xc2\xe2].[\x00-\x07]\x37...[\x94-\x97]",
    b"\x22\x00\x80\x52",
    offset=8,
    desc="غیرفعال‌سازی صفحهٔ بررسی واجد شرایط (arm64, w2)",
)

CLI_GATE = MultiGate(
    CLI_GATE_X64,
    CLI_GATE_ARM64,
    CLI_GATE_ARM64_W2,
    CLI_GATE_ARM64_W4,
    desc="غیرفعال‌سازی صفحهٔ بررسی واجد شرایط",
)

ALL_GATES = [
    (CLI_GATE, "غیرفعال‌سازی صفحهٔ بررسی واجد شرایط"),
]


@contextlib.contextmanager
def _scan_data(f):
    # Reading a modified signed Mach-O through mmap can cause an uncatchable
    # CODESIGNING SIGKILL on macOS, including during post-write verification.
    if sys.platform == "darwin":
        f.seek(0)
        yield f.read()
        return
    if os.fstat(f.fileno()).st_size == 0:
        yield b""
        return
    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    try:
        yield mm
    finally:
        mm.close()


@contextlib.contextmanager
def _mapped(path):
    """Read-only bytes-view для сканирования сигнатур.

    На macOS не маппит страницы подписанного файла (SIGKILL-риск),
    а читает через _scan_data; на остальных ОС — zero-copy mmap."""
    with open(path, "rb") as f:
        with _scan_data(f) as data:
            yield data


def is_locked(path):
    """
    True, если файл занят (приложение запущено).

    На POSIX замена файла через os.replace возможна даже при работающем процессе,
    поэтому блокирующим считаем только Windows.

    Примечание: на POSIX это не гарантирует, что файл не используется.
    Если нужна проверка на занятость, требуется более сложная логика
    (например, проверка процессов или файловые блокировки).
    """
    if os.name != "nt":
        return False

    try:
        with open(path, "r+b"):
            return False
    except OSError:
        return True


def get_status(path):
    """('patched'|'unpatched'|'unknown', None) — без исключений наружу.
    'patched' только если ВСЕ гейты применены."""
    if not path or not os.path.isfile(path):
        return ("unknown", None)
    try:
        with _mapped(path) as d:
            states = []
            for gate, _ in ALL_GATES:
                try:
                    for state, _offsets, _g in gate.resolve_all(d):
                        states.append(state)
                except LookupError:
                    return ("unknown", None)
            if all(s == "patched" for s in states):
                return ("patched", None)
            if all(s == "unpatched" for s in states):
                return ("unpatched", None)
            return ("unpatched", None)  # частично применён — считаем unpatched
    except OSError:
        return ("unknown", None)


def is_already_patched(path):
    """Совместимый с IDE/asar интерфейс: True только если патч уже применён."""
    return get_status(path)[0] == "patched"


def _make_backup(path):
    """Снимок чистого файла как <path>.agybak.
    Вызывается только когда файл unpatched — живые байты это pristine-оригинал.
    Бэкап, не совпадающий с файлом, устарел (приложение автообновилось) —
    обновляем его, а не храним."""
    bak = path + BAK_EXT
    if os.path.exists(bak):
        if filecmp.cmp(path, bak, shallow=False):
            return  # бэкап уже соответствует этому билду
        info(f"بکاپ قدیمی است (برنامه به‌روزرسانی شده) — در حال تازه‌سازی {os.path.basename(path)}{BAK_EXT}")
    else:
        info(f"در حال ایجاد بکاپ: {os.path.basename(path)}{BAK_EXT}")
    if sys.platform == "darwin":
        ensure_macos_writable(path)
    try:
        shutil.copy2(path, bak)
    except (PermissionError, OSError) as e:
        need_retry = (
            sys.platform == "darwin"
            and isinstance(e, OSError)
            and e.errno in (errno.EPERM, errno.EACCES)
        )
        if need_retry:
            warn("بکاپ توسط فلگ‌های macOS مسدود شد، پس از حذف فلگ‌ها دوباره تلاش می‌شود...")
            ensure_macos_writable(path)
            shutil.copy2(path, bak)
        else:
            raise
    fix_posix_permissions(bak)
    ok(f"بکاپ: {os.path.basename(bak)} ({format_bytes(file_size(bak))})")


def _copy_to_user_bin(path):
    from patcher.utils.file import get_posix_invoking_user_home
    user_home = get_posix_invoking_user_home()
    dest_dir = os.path.join(user_home, ".local", "bin") if user_home else os.path.expanduser("~/.local/bin")
    dest_path = os.path.join(dest_dir, "agy")
    if os.path.abspath(path) == os.path.abspath(dest_path):
        return
    info(f"کپی فایل به پوشهٔ کاربر: {dest_path}")
    try:
        os.makedirs(dest_dir, exist_ok=True)
        if os.path.exists(dest_path):
            try:
                os.remove(dest_path)
            except Exception:
                pass
        shutil.copy2(path, dest_path)
        os.chmod(dest_path, 0o755)
        ok(f"فایل با موفقیت در این مسیر کپی شد: {dest_path}")
    except Exception as e:
        warn(f"کپی فایل به {dest_path} ممکن نشد: {e}")


def do_patch_agy(path):
    from patcher.cli import confirmed
    from patcher.utils.captcha import confirm_with_captcha

    if not path or not os.path.isfile(path):
        from patcher.cli import offer_download_and_block
        offer_download_and_block("آنتی‌گراویتی CLI", target_type="agy")
        return

    hash_before = file_hash(path)
    info(f"هدف: {color(path, COLOR_CYAN)}")
    hint(f"حجم: {color(format_bytes(file_size(path)), COLOR_CYAN)}")
    emit()

    write_success = False
    patches = []  # [(offset, gate), ...] — гейты, требующие записи
    for attempt in range(2):
        if is_locked(path):
            if attempt == 0:
                warn("فایل اجرایی (باینری) قفل است (Antigravity CLI در حال اجراست).")
                if confirmed("می‌خواهید فرایندهای در حال اجرای agy را خودکار ببندم و دوباره تلاش کنم؟"):
                    terminate_processes(["agy"])
                    import time
                    time.sleep(1.5)
                    continue
            err("فایل قفل است — ابتدا Antigravity CLI را ببندید.")
            return

        # Сканируем в mmap, закрываем ДО записи (zero-copy scan)
        patches = []
        try:
            with _mapped(path) as d:
                all_patched = True
                for gate_obj, gate_label in ALL_GATES:
                    try:
                        matches = gate_obj.resolve_all(d)
                    except LookupError as e:
                        err(f"{gate_label}: {e}")
                        handle_patch_failure()
                        return
                    for kind, offsets, g in matches:
                        if kind == "unpatched":
                            all_patched = False
                            for off in offsets:
                                patches.append((off, g))
                if all_patched:
                    hint("agy قبلاً پچ شده است (همهٔ دروازه‌ها).")
                    if not confirm_with_captcha("به هر حال پچ اعمال شود؟"):
                        return
                    # re-patch: перезаписываем все гейты
                    patches = []
                    for gate_obj, _ in ALL_GATES:
                        for _kind, offsets, g in gate_obj.resolve_all(d):
                            for off in offsets:
                                patches.append((off, g))
        except OSError as e:
            err(f"خطای خواندن: {e}")
            return

        if not patches:
            return

        try:
            _make_backup(path)
        except (PermissionError, OSError) as e:
            err(f"خطای بکاپ: {e}")
            if sys.platform == "darwin":
                hint("macOS از نوشتن جلوگیری کرد (Errno 1: Operation not permitted).")
                hint("Antigravity را ببندید، سپس پچر را با sudo دوباره اجرا کنید:")
                hint("  sudo python3 main.py   (یا sudo ./Antigravity_Patcher_macOS)")
            else:
                hint("دسترسی نوشتن وجود ندارد — با دسترسی مدیر/root دوباره اجرا کنید و ابتدا agy را ببندید.")
            handle_patch_failure()
            return

        try:
            if os.name == "nt":
                # Windows: прямая запись с проверкой блокировки
                with open(path, "r+b") as f:
                    bdata = bytearray(f.read())
                    bdata = apply_patches_to_data(bdata, patches)
                    f.seek(0)
                    f.write(bdata)
                    f.flush()
                    os.fsync(f.fileno())
            else:
                # POSIX: атомарная замена через временный файл
                with open(path, "rb") as f:
                    bdata = bytearray(f.read())

                bdata = apply_patches_to_data(bdata, patches)

                # Атомарная замена с безопасным временным файлом
                if sys.platform == "darwin":
                    ensure_macos_writable(path)
                atomic_replace_posix(path, bytes(bdata))

            write_success = True
            break
        except PermissionError as e:
            if attempt == 0:
                if sys.platform == "darwin":
                    warn(f"نوشتن با macOS مسدود شد (فلگ‌ها/مالکیت): {e}")
                    ensure_macos_writable(path)
                    import time
                    time.sleep(0.5)
                    continue
                warn(f"دسترسی رد شد (فایل قفل است): {e}")
                if confirmed("می‌خواهید فرایندهای در حال اجرای agy را خودکار ببندم و دوباره تلاش کنم؟"):
                    terminate_processes(["agy"])
                    import time
                    time.sleep(1.5)
                    continue
            err(f"خطای نوشتن (دسترسی رد شد): {e}")
            if sys.platform == "darwin":
                hint("Antigravity را ببندید و با sudo دوباره اجرا کنید: sudo python main.py")
            handle_patch_failure()
            return
        except OSError as e:
            if e.errno in (errno.EPERM, errno.EACCES) and attempt == 0 and sys.platform == "darwin":
                warn(f"نوشتن با macOS مسدود شد (فلگ‌ها/مالکیت): {e}")
                ensure_macos_writable(path)
                import time
                time.sleep(0.5)
                continue
            err(f"خطای نوشتن: {e}")
            handle_patch_failure()
            return
        except Exception as e:
            err(f"خطای نوشتن: {e}")
            handle_patch_failure()
            return

    if not write_success:
        handle_patch_failure()
        return

    hash_after = file_hash(path)
    resign_macos_bundle(path)
    resign_macos_binary(path)
    if os.name == "posix":
        _copy_to_user_bin(path)
    emit()
    step("پچ فایل اجرایی (باینری) agy", True, f"{len(patches)} دروازه")
    emit()
    panel_rows = [
        ("هدف", os.path.basename(path)),
    ]
    for off, g in patches:
        panel_rows.append(("دروازه", f"{g.desc} @ 0x{off:x}"))
    if hash_before and hash_after:
        panel_rows.append(("قبل", f"{hash_before[:8]}...{hash_before[56:]}"))
        panel_rows.append(("بعد", f"{hash_after[:8]}...{hash_after[56:]}"))
    print_panel("پچ با موفقیت انجام شد", panel_rows, show_star=True)
    hint("برای اعمال تغییرات، Antigravity CLI را دوباره اجرا کنید.")


def do_restore_agy(path):
    from patcher.cli import confirmed

    if not os.path.isfile(path):
        err(f"هدف یک فایل نیست: {path}")
        return

    bak = path + BAK_EXT
    if not os.path.exists(bak):
        warn(f"بکاپی برای {os.path.basename(path)} وجود ندارد (چیزی برای بازگردانی نیست).")
        return

    status, _ = get_status(path)
    if status != "patched":
        warn("agy پچ نشده است — بازگردانی رد شد (ممکن است بکاپ مربوط به بیلد دیگری باشد).")
        if not confirmed("به هر حال از بکاپ بازگردانی شود؟"):
            hint("بازگردانی لغو شد.")
            return

    if is_locked(path):
        err("فایل اجرایی (باینری) قفل است — ابتدا Antigravity CLI را ببندید.")
        return

    if not confirmed("agy از بکاپ بازگردانی شود؟"):
        hint("بازگردانی لغو شد.")
        return

    hash_before = file_hash(path)
    try:
        if os.name == "nt":
            shutil.copy2(bak, path)
        else:
            # Читаем бэкап в память
            with open(bak, "rb") as f:
                bak_data = f.read()

            # Атомарная замена с метаданными из бэкапа
            atomic_replace_posix(path, bak_data, meta_source=bak)

        fix_posix_permissions(path)
    except Exception as e:
        err(f"خطای بازگردانی: {e}")
        return

    hash_after = file_hash(path)
    resign_macos_bundle(path)
    resign_macos_binary(path)
    if os.name == "posix":
        _copy_to_user_bin(path)
    emit()
    panel_rows = [("هدف", os.path.basename(path))]
    if hash_before and hash_after and hash_before != hash_after:
        panel_rows.append(("قبل", f"{hash_before[:8]}...{hash_before[56:]}"))
        panel_rows.append(("بعد", f"{hash_after[:8]}...{hash_after[56:]}"))
    print_panel("بازگردانی با موفقیت انجام شد", panel_rows)
