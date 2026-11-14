# 🔑 Antigravity Patcher (پچر متن‌باز Antigravity)
<p align="center">
  <a href="https://github.com/DrAmir0240/Antigravity-Patcher"><img src="https://img.shields.io/badge/GitHub-DrAmir0240-181717?style=for-the-badge&logo=github" alt="GitHub"></a>
  <a href="https://t.me/AmirOmidi_Dev"><img src="https://img.shields.io/badge/Telegram-@AmirOmidi__Dev-2CA5E0?style=for-the-badge&logo=telegram" alt="Telegram"></a>
  <img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" alt="Python">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-GPL--3.0-blue?style=for-the-badge" alt="GPL-3.0 License"></a>
</p>

پچر متن‌باز برای **Antigravity 2.0**، **Antigravity IDE**، **Antigravity CLI (ابزار `agy`)** و **افزونه Google Antigravity در VS Code**: این ابزار محدودیت‌های منطقه‌ای و تحریم‌های جغرافیایی گوگل را **بدون نیاز به VPN و بدون نیاز به تغییر منطقه (Region) اکانت گوگل** دور می‌زند.

![نمای برنامه](https://i.ibb.co/s9Vh80CM/python-w-TPlox-Po-G4.png)

---

## ⚠️ خطای HTTP 500 Internal Server Error
اگر هنگام ارسال درخواست در Antigravity IDE با خطای `HTTP 500 Internal Server Error` مواجه شدید، این مشکل سمت سرورهای گوگل است و پچر راهی برای حل آن ندارد. در این صورت اکانت گوگل خود را تغییر دهید (ترجیحاً اکانتی متعلق به منطقه‌ای که سرویس در آن فعال است یا اشتراک رسمی دارد).

**نمونه خطا:**
```
Trajectory ID: 2669b09c-1d11-4620-9bfa-6ad1f0e26a88
Error: HTTP 500 Internal Server Error
Sherlog: 
TraceID: 0xd9ada64bcca3260c
Headers: {"Alt-Svc":["h3=\":443\"; ma=2592000,h3-29=\":443\"; ma=2592000"],"Content-Length":["109"],"Content-Type":["text/event-stream"],"Date":["Sat, 14 Mar 2026 13:51:24 GMT"],"Server":["ESF"],"Server-Timing":["gfet4t7; dur=423"],"Vary":["Origin","X-Origin","Referer"],"X-Cloudaicompanion-Trace-Id":["d9ada64bcca3260c"],"X-Content-Type-Options":["nosniff"],"X-Frame-Options":["SAMEORIGIN"],"X-Xss-Protection":["0"]}

{
  "error": {
    "code": 500,
    "message": "Internal error encountered.",
    "status": "INTERNAL"
  }
}
```

---

## ⚠️ خطای HTTP 403 Forbidden / SUBSCRIPTION_REQUIRED (#3501)
اگر در Antigravity IDE یا خط فرمان `agy` با خطای `HTTP 403 Forbidden` با دلیل `SUBSCRIPTION_REQUIRED` یا پیام‌های زیر مواجه شدید:
- `You do not have a valid license of this product`
- `Agent execution terminated due to error`

این خطا مشکلی در پچ محلی یا صفحه `Eligibility Check` نیست، بلکه مستقیماً به **API گوگل و وضعیت اشتراک یا مجوز اکانت کاربری** برمی‌گردد. پچر فقط فایل‌های محلی سیستم را اصلاح می‌کند و دسترسی به لایسنس‌های سرور گوگل ندارد، بنابراین این خطا با پچ حل نمی‌شود.

**راه‌حل:**
1. **ریجن اکانت گوگل خود را تغییر دهید** یا از اکانتی استفاده کنید که در کشوری پشتیبانی‌شده ثبت شده باشد.
2. **در صورت برطرف نشدن**، باید اشتراک رسمی تهیه شود.

**پلن‌های رسمی هوش مصنوعی گوگل (Google AI Plans):**
* **Google AI Plus**: فضای ۴۰۰ گیگابایت، دسترسی ۲ برابری به سهمیه جمینای
* **Google AI Pro**: فضای ۵ ترابایت، دسترسی ۴ برابری به سهمیه جمینای
* **Google AI Ultra**: فضای ۲۰+ ترابایت، دسترسی ۲۰ برابری به سهمیه جمینای

**نمونه خطا:**
```json
{
  "error": {
    "code": 403,
    "details": [
      {
        "@type": "type.googleapis.com/google.rpc.ErrorInfo",
        "domain": "cloudaicompanion.googleapis.com",
        "metadata": {
          "error_number": "1001",
          "uiMessage": "true"
        },
        "reason": "SUBSCRIPTION_REQUIRED"
      }
    ],
    "message": "You do not have a valid license of this product. Please contact your administrator to request a license. If you are not an enterprise user and believe you are receiving this message as an error, please try using the latest version and logging in again. (#3501)",
    "status": "PERMISSION_DENIED"
  }
}
```

---

## ⚠️ خطای HTTP 400 Bad Request
اگر با خطای `HTTP 400 Bad Request` و پیام `User location is not supported for the API use` مواجه شدید، به این معنی است که گوگل موقعیت مکانی شما را تشخیص داده و مسدود کرده است.

> **نکته:** استفاده از VPN یا پروکسی‌های نامناسب ممکن است توسط سیستم تشخیص گوگل شناسایی شود و باعث این خطا گردد.

**راه‌حل:**
1. پچ را اعمال کنید (**گزینه `1` در منو: Antigravity IDE patch**). پچر بررسی `isGoogleInternal` را در کد برنامه دور می‌زند.
2. اگر پچ قبلاً اعمال شده، اکانت گوگل خود را تغییر دهید یا از سرور/VPN دیگری استفاده نمایید.
3. استفاده از DNSهای گذر از تحریم (مانند **[Xbox DNS](https://xbox-dns.ru/)**، **[dns.malw.link](https://info.dns.malw.link/)**، **[GeoHide](https://dns.geohide.ru:8443/)** یا DNSهای ضدتحریم فعال روی سیستم و مودم).

**نمونه خطا:**
```json
{
  "error": {
    "code": 400,
    "message": "User location is not supported for the API use.",
    "status": "FAILED_PRECONDITION"
  }
}
```

---

## ⚠️ خطای HTTP 429 Too Many Requests / RESOURCE_EXHAUSTED
هنگام ارسال دستور، با خطای اتمام سهمیه (Quota) مواجه می‌شوید:

```
Error: HTTP 429 Too Many Requests
{
  "error": {
    "code": 429,
    "message": "Resource has been exhausted (e.g. check quota).",
    "status": "RESOURCE_EXHAUSTED"
  }
}
```

**راه‌حل:** پاکسازی و ریست پوشه داده‌های Antigravity (کانفیگ تمیز و توکن‌های تازه) و سپس در صورت تمایل، بازگرداندن تاریخچه گفتگوها از نسخه بک‌آپ.

> **تفاوت Antigravity با Antigravity IDE:** پوشه داده‌ها برای نسخه Antigravity 2.0 نامش `Antigravity` و برای Antigravity IDE نامش `Antigravity IDE` است. در دستورات زیر نام مناسب را جایگزین کنید.

### ویندوز (راهنمای کامل)
1. برنامه Antigravity را کاملاً ببندید (از Task Manager مطمئن شوید پردازشی باز نمانده است).
2. پوشه `%appdata%` را باز کرده و پوشه داده‌ها را به مکانی موقت منتقل کنید:
   ```powershell
   Move-Item "$env:APPDATA\Antigravity" "$env:USERPROFILE\Desktop\Antigravity-backup"
   ```
3. برنامه Antigravity را اجرا کرده، وارد اکانت شوید و یک پیام آزمایشی بفرستید (خطای ۴۲۹ باید برطرف شده باشد).
4. برنامه را مجدداً ببندید.
5. *(اختیاری - بازگردانی چت‌ها)* برای حفظ پیام‌های قبلی، فقط این دو پوشه را برگردانید:
   ```powershell
   Remove-Item -Recurse -Force "$env:APPDATA\Antigravity\User\globalStorage"
   Remove-Item -Recurse -Force "$env:APPDATA\Antigravity\User\workspaceStorage"

   Copy-Item -Recurse "$env:USERPROFILE\Desktop\Antigravity-backup\User\globalStorage" "$env:APPDATA\Antigravity\User\"
   Copy-Item -Recurse "$env:USERPROFILE\Desktop\Antigravity-backup\User\workspaceStorage" "$env:APPDATA\Antigravity\User\"
   ```
   > ⚠️ **توجه:** فایل `settings.json` را از بک‌آپ کپی نکنید، چون همان تنظیمات مشکل‌دار قبلی برمی‌گردد.
6. برنامه را باز کرده و سلامت چت‌ها را چک کنید. در پایان بک‌آپ را حذف نمایید:
   ```powershell
   Remove-Item -Recurse -Force "$env:USERPROFILE\Desktop\Antigravity-backup"
   ```

### مک (macOS)
1. برنامه را با `Cmd+Q` کامل ببندید.
2. پوشه داده‌ها را جابجا کنید:
   ```bash
   mv ~/Library/Application\ Support/Antigravity ~/Desktop/Antigravity-backup
   ```
3. برنامه را اجرا کنید، لاگین کرده و تست کنید.
4. برنامه را دوباره ببندید (`Cmd+Q`).
5. *(اختیاری - بازگردانی تاریخچه)*:
   ```bash
   rm -rf ~/Library/Application\ Support/Antigravity/User/globalStorage
   rm -rf ~/Library/Application\ Support/Antigravity/User/workspaceStorage

   cp -a ~/Desktop/Antigravity-backup/User/globalStorage ~/Library/Application\ Support/Antigravity/User/
   cp -a ~/Desktop/Antigravity-backup/User/workspaceStorage ~/Library/Application\ Support/Antigravity/User/
   ```
6. برنامه را تست کرده و بک‌آپ را حذف کنید:
   ```bash
   rm -rf ~/Desktop/Antigravity-backup
   ```

### لینوکس (Linux)
مسیر پیش‌فرض داده‌ها: `~/.config/Antigravity`
1. برنامه را کامل ببندید:
   ```bash
   pkill -f -i antigravity; sleep 2; pgrep -a -i antigravity || echo "بسته شد"
   ```
2. پوشه داده‌ها را جابجا کنید:
   ```bash
   mv ~/.config/Antigravity ~/Antigravity-backup
   ```
3. برنامه را باز کرده، وارد شوید و دستور تستی بفرستید.
4. پس از اطمینان، برنامه را ببندید.
5. *(اختیاری - بازگردانی تاریخچه)*:
   ```bash
   rm -rf ~/.config/Antigravity/User/globalStorage
   rm -rf ~/.config/Antigravity/User/workspaceStorage

   cp -a ~/Antigravity-backup/User/globalStorage ~/.config/Antigravity/User/
   cp -a ~/Antigravity-backup/User/workspaceStorage ~/.config/Antigravity/User/
   ```
6. برنامه را اجرا و چک کنید.

#### چرا این روش کار می‌کند؟
با حذف و ایجاد مجدد پوشه داده‌ها، توکن‌های موقت و اتصال به سهمیه مصرف‌شده قبلی ریست می‌شوند و سهمیه جدید فعال می‌شود.

> **نکته برای کاربران پچ‌شده:** فایل `main.js` پچ‌شده داخل پوشه نصب برنامه است و با حذف پوشه داده‌های کاربر تغییری نمی‌کند؛ بنابراین نیازی به پچ مجدد نیست.

---

## ⚠️ خطای پچ: "✗ isGoogleInternal -> true (auth) — pattern not found"
اگر هنگام پچ کردن Antigravity IDE (گزینه `1`) با این خطا روبرو شدید:
```text
✗ isGoogleInternal -> true (auth) — pattern not found
```
این پیام نشان می‌دهد که پچر نتوانسته الگوی مورد نظر را در فایل `main.js` پیدا کند.
**در تقریباً ۱۰۰٪ موارد، دلیل این است که پچر یک فایل `main.js` اشتباه (مربوط به یک برنامه الکترون دیگر یا فایل موجود در پوشه کاری جاری) را پیدا کرده است.**

### راه‌حل:
1. در منوی اصلی مسیر نمایش داده شده برای Antigravity IDE را بررسی کنید.
2. مطمئن شوید مسیر دقیقاً به فایل Antigravity IDE اشاره دارد، مانند:
   - **ویندوز:** `%LOCALAPPDATA%\Programs\Antigravity IDE\resources\app\out\main.js`
   - **لینوکس:** `/usr/share/antigravity-ide/resources/app/out/main.js`
   - **مک:** `/Applications/Antigravity IDE.app/Contents/Resources/app/out/main.js`
3. با انتخاب گزینه **TOOLS → `11` (Select custom path)** مسیر دقیق پوشه یا فایل برنامه را دستی وارد کنید.
4. یا مسیر را مستقیماً به دستور پایتون پاس بدهید:
   ```bash
   python main.py "/path/to/Antigravity IDE"
   ```

---

## 🌟 قابلیت‌ها و ویژگی‌های کلیدی
- **شناسایی خودکار:** جستجوی هوشمند برای پیدا کردن مسیرهای نصب Antigravity 2.0، Antigravity IDE، ابزار CLI (`agy`) و افزونه VS Code در رجیستری ویندوز و مسیرهای استاندارد لینوکس و مک.
- **بررسی خودکار آپدیت:** امکان بررسی انتشار نسخه‌های جدیدتر در گیت‌هاب (گزینه `9`).
- **پچ Antigravity CLI:** حذف کامل صفحه «Eligibility Check» و دور زدن خطای عدم دسترسی در باینری کامپایل‌شده Go (`agy`/`agy.exe`) بر اساس امضای بایت‌های ماشین کد برای پردازنده‌های x86-64 و ARM64.
- **پچ Antigravity Manager (`language_server`):** فعال‌سازی مقدار `hasValidAuth=true` در باینری اصلی بک‌اند.
- **پچ افزونه VS Code (`google.google-antigravity`):** تزریق کد محافظ به `extension.js` برای جلوگیری از دانلود مجدد فایل‌های اجرایی از سرور و غیرفعال کردن تغییر کانال (`isChannelChanged -> false`).
- **پشتیبانی کامل لینوکس و مک:**
  - پشتیبانی از سیستم‌های مدیریت بسته لینوکس (`dpkg`, `rpm`, `package.json`).
  - امضای مجدد خودکار در مک (Ad-hoc codesign با `codesign --force --deep --sign -`) تا سیستم‌عامل مک جلوی اجرای فایل دستکاری‌شده را نگیرد.
- **جایگزینی اتمیک (Atomic) در لینوکس/مک:** نوشتن فایل‌ها با فایل‌های موقت امن و `os.replace` تا حتی اگر برنامه در پس‌زمینه باز بود خطای `ETXTBSY` یا دسترسی رد نشود و مجوز اجرای فایل (`+x`) و مالکیت فایل حفظ گردد.
- **پشتیبان‌گیری خودکار (Backup):** گرفتن نسخه پشتیبان قبل از اعمال هر تغییر (`.bak`، `.agybak`، `.vscodebak`) با قابلیت بازگردانی ۱۰۰٪ با یک دکمه.

---

## 🚀 راهنمای استفاده

### مراحل سریع:
1. برنامه‌های Antigravity IDE یا Antigravity 2.0 را کاملاً ببندید.
2. پچر را با دسترسی ادمین (در ویندوز Run as administrator و در لینوکس/مک با `sudo`) اجرا کنید:
   ```bash
   python main.py
   ```
3. گزینه مورد نیاز را از منو انتخاب کنید:

| گزینه | دسته‌بندی | توضیحات |
|---|---|---|
| **`1`** | **PATCH** | پچ فایل `main.js` در Antigravity IDE (دور زدن تحریم منطقه‌ای) |
| **`2`** | **PATCH** | پچ فایل باینری `language_server` در Antigravity 2.0 |
| **`3`** | **PATCH** | پچ باینری ابزار ترمینال Antigravity CLI (`agy`) |
| **`4`** | **PATCH** | پچ افزونه VS Code و باینری داخل `~/.gemini/bin/antigravity` |
| **`5`** | **RESTORE** | بازگردانی فایل اصلی `main.js` نرم‌افزار IDE از بک‌آپ |
| **`6`** | **RESTORE** | بازگردانی فایل `language_server` از بک‌آپ |
| **`7`** | **RESTORE** | بازگردانی فایل `agy` از بک‌آپ |
| **`8`** | **RESTORE** | بازگردانی فایل `extension.js` و باینری VS Code از بک‌آپ |
| **`9`** | **TOOLS** | بررسی نسخه‌های جدید در گیت‌هاب |
| **`10`** | **TOOLS** | باز کردن مخزن گیت‌هاب در مرورگر |
| **`11`** | **TOOLS** | انتخاب دستی مسیر فایل‌ها و پوشه‌ها |
| **`12`** | **TOOLS** | درباره برنامه |
| **`0`** | **خروج** | خروج از پچر |

---

### اجرا با تعیین دستی مسیر برنامه:
اگر پچر مسیر برنامه‌ها را خودکار پیدا نکرد، مسیر را در آرگومان ورودی بدهید:

```bash
# ویندوز:
python main.py "C:\Users\<نام_کاربر>\AppData\Local\Programs\Antigravity IDE"
python main.py "C:\Users\<نام_کاربر>\AppData\Local\Programs\Antigravity\resources\bin\language_server.exe"
python main.py "C:\Users\<نام_کاربر>\AppData\Local\agy\bin\agy.exe"

# لینوکس:
python main.py /usr/share/antigravity-ide
python main.py /opt/Antigravity/resources/bin/language_server
python main.py /usr/local/bin/agy

# مک:
python3 main.py "/Applications/Antigravity IDE.app"
python3 main.py "/Applications/Antigravity.app"
python3 main.py /usr/local/bin/agy
```

---

## ❓ جزئیات فنی تغییرات

### ۱. پچ Antigravity IDE
عبارت زیر در `main.js` جستجو و تغییر می‌کند:
```javascript
// قبل:
resetIsTierGCPTos(),this.XXX.isGoogleInternal

// بعد از پچ:
resetIsTierGCPTos(),true
```
سپس حافظه کش VS Code (`CachedData` و `Code Cache/js`) پاکسازی می‌شود تا محیط IDE کدهای جدید را لود کند.

### ۲. پچ Antigravity Manager (`language_server`)
این فایل به زبان Go کامپایل شده است. پچر با شناسایی امضای بایت‌های اسمبلی تغییرات زیر را اعمال می‌کند:
- **در پردازنده‌های x86-64:** تغییر `cmp byte ptr [rax + 8], 0` به `mov byte ptr [rax + 8], 1` همراه با دستورهای `nop` (`\xc6\x40\x08\x01\x90\x90`).
- **در پردازنده‌های ARM64:** تغییر دستورات خواندن فلگ به مقدار ثابت ۱ (`\x23\x00\x80\x52\x03\x20\x00\x39`).
در نتیجه مقدار خروجی `hasValidAuth` همیشه `true` بازگردانده می‌شود.

### ۳. پچ Antigravity CLI (`agy`)
صفحه خطای اهلیت (Eligibility Check) در فایل باینری کامپایل‌شده دور زده می‌شود:
- **در x86-64:** دستور `cmp byte ptr [rax+8], 0` با `test rax, rax` و `NOP` جایگزین می‌شود تا شاخه ارور غیرقابل دسترس شود.
- **در ARM64:** دستور خواندن رجیستر فلگ `ldrb w1, [x0, #8]` به `mov w1, #1` تغییر می‌یابد تا اجرای برنامه همیشه در مسیر موفق قرار گیرد. در نسخه‌های جدیدتر ۱.۲.۷ گیت‌های `w2` و `w4` نیز پچ می‌شوند.

### ۴. پچ افزونه رسمی VS Code (`google.google-antigravity`)
> **نکته مهم:** قبل از پچ افزونه، ابتدا باید Antigravity 2.0 را با گزینه `2` پچ کرده باشید.

1. **جلوگیری از دانلود مجدد:** بلافاصله بعد از خط لاگ دانلود باینری‌ها، قطعه کدی تزریق می‌شود که بررسی می‌کند اگر باینری قبلاً دانلود شده (در `~/.gemini/bin`)، مستقیماً از همان استفاده کند و دانلود دوباره انجام نشود.
2. **غیرفعال‌سازی تغییر کانال:** خط `isChannelChanged = manifestFetched && ...` به `isChannelChanged = false;` تغییر می‌یابد تا از رونویسی فایل‌ها جلوگیری شود.

---

## 🛠️ ساخت نسخه اجرایی (Build)
برای کامپایل کردن پروژه به فایل اجرایی مستقل (بدون نیاز به پایتون در مقصد) با استفاده از PyInstaller:

1. **محیط مجازی و نصب وابستگی‌ها:**
   ```bash
   cd source
   python3 -m venv .venv
   source .venv/bin/activate  # در ویندوز: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **کامپایل با PyInstaller:**
   - **ویندوز:**
     ```bash
     pyinstaller --onefile --uac-admin --icon=icon.ico --name="Open_AG_Patcher_Windows" --noupx --clean --version-file=version.txt main.py
     ```
   - **لینوکس:**
     ```bash
     pyinstaller --onefile --icon=icon.ico --name="Open_AG_Patcher_Linux" --hidden-import=packaging --hidden-import=packaging.version --hidden-import=packaging.specifiers --hidden-import=packaging.requirements main.py
     ```
   - **مک (Universal2):**
     ```bash
     pyinstaller --onefile --name="Open_AG_Patcher_macOS" --target-arch universal2 --hidden-import=packaging --hidden-import=packaging.version --hidden-import=packaging.specifiers --hidden-import=packaging.requirements main.py
     ```

---

## 📁 ساختار پوشه‌های پروژه
- `source/main.py`: نقطه ورود اصلی برنامه، بررسی دسترسی ادمین/sudo و اجرای منو.
- `source/patcher/`: کدهای اصلی پچر:
  - `constants.py`: مقادیر ثابت، کدهای رنگی ترمینال و نسخه‌ها.
  - `cli.py`: رابط کاربری تعاملی کنسول، دریافت دستورات و رسم منوها.
  - `utils/`: ابزارهای کمکی سیستم، رنگ‌بندی، مجوزها و جایگزینی اتمیک فایل‌ها (`atomic.py`).
  - `ide/`: لاجیک کشف و پچ فایل‌های `main.js` در Antigravity IDE.
  - `agy/`: لاجیک پچ بایت‌های باینری ابزار ترمینال `agy`.
  - `manager/`: لاجیک پچ بایت‌های سرور داخلی Antigravity 2.0 (`language_server`).
  - `vscode/`: لاجیک پچ افزونه VS Code و باینری واقع در `~/.gemini/bin`.
- `test-agy/`: تست‌های خودکار تطابق امضاهای باینری برای نسخه‌های جدید.
- `source/requirements.txt`: نیازمندی‌های پایتون.
- `source/icon.ico`: آیکون برنامه.

---

# 📜 مجوز و کپی‌رایت
این پروژه تحت مجوز **GPL-3.0** منتشر شده است. متن کامل در فایل [`LICENSE`](LICENSE) موجود است.

بخشی از راه‌حل‌ها و تغییرات این پروژه بر اساس دستاوردهای مخزن [eligibility-antigravity-patcher](https://github.com/QNIX-Dev/eligibility-antigravity-patcher) تحت مجوز MIT پیاده‌سازی شده است.

---

## 💬 پشتیبانی و ارتباط
برای ارتباط، پشتیبانی و گزارش مشکلات می‌توانید از طریق راه‌های زیر اقدام کنید:
- **مخزن گیت‌هاب:** [DrAmir0240/Antigravity-Patcher](https://github.com/DrAmir0240/Antigravity-Patcher)
- **پشتیبانی تلگرام:** [@AmirOmidi_Dev](https://t.me/AmirOmidi_Dev)
