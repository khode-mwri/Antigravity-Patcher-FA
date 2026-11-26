# 🔑 پچر آنتی‌گراویتی — نسخهٔ فارسی | Google Antigravity Patcher (FA)

<p align="center">
  <a href="README.md">English</a> · <b>فارسی</b> · <a href="README.ru.md">Русский</a>
</p>

<p align="center">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-GPL--3.0-blue?style=for-the-badge" alt="GPL-3.0"></a>
  <a href="https://github.com/khode-mwri/Antigravity-Patcher-FA/stargazers"><img src="https://img.shields.io/github/stars/khode-mwri/Antigravity-Patcher-FA?style=for-the-badge&logo=github&color=yellow" alt="Stars"></a>
  <img src="https://img.shields.io/badge/زبان-فارسی-success?style=for-the-badge" alt="فارسی">
</p>

> **این مخزن، نسخهٔ فارسی‌شدهٔ پروژهٔ متن‌باز [DrAmir0240/Antigravity-Patcher](https://github.com/DrAmir0240/Antigravity-Patcher) است.**
> تمام متن‌های رابط کاربری (بنر، منوها، پیام‌های وضعیت، خطاها و راهنماها) به فارسی روان برگردانده شده‌اند و **راست‌به‌چپ** در ترمینال رندر می‌شوند.
> تاریخچهٔ کامل توسعه، نویسندگی و مجوز اصلی حفظ شده است و فهرست تغییرات در [`NOTICE.md`](NOTICE.md) آمده است.

پچر متن‌باز برای رفع **قفل منطقه‌ای و تحریم** در محصولات هوش مصنوعی گوگل:

- **Antigravity IDE** (فایل `main.js`)
- **Antigravity 2.0** (باینری `language_server`)
- **Antigravity CLI** (ابزار `agy`)
- **افزونهٔ Google Antigravity** در VS Code

این ابزار خطاهای `User location is not supported for the API use` و `Unable to verify account eligibility` را **بدون نیاز به VPN و بدون تغییر ریجن اکانت گوگل** در ویندوز، مک و لینوکس دور می‌زند.

> این پچر فقط فایل‌های **محلی** را تغییر می‌دهد و هیچ ارتباطی با سرورهای گوگل برقرار نمی‌کند؛ نه کلید، نه توکن، نه ردگیری. هر تغییر با بکاپ خودکار (`.bak` / `.agybak` / `.vscodebak`) قابل بازگردانی است و نسخهٔ بازگردانی‌شده بایت‌به‌بایت با فایل اصلی یکسان است.

---

## 📋 فهرست

1. [نمای برنامه](#-نمای-برنامه)
2. [پیش‌نیاز و آماده‌سازی](#-پیشنیاز-و-آمادهسازی)
3. [نصب و اجرا](#-نصب-و-اجرا)
4. [گزینه‌های منو](#-گزینههای-منو)
5. [اجرا با مسیر دستی](#-اجرا-با-مسیر-دستی)
6. [بکاپ و مدیریت داده‌ها](#-بکاپ-و-مدیریت-دادهها)
7. [خطاهای متداول](#-خطاهای-متداول)
8. [جزئیات فنی پچ](#-جزئیات-فنی-پچ)
9. [ساخت نسخهٔ اجرایی](#-ساخت-نسخهٔ-اجرایی)
10. [ساختار پروژه](#-ساختار-پروژه)
11. [مجوز و انتساب](#-مجوز-و-انتساب)

---

## 🖥 نمای برنامه

```text
  ╔═══════════════════════════════════════════════╗
  ║  Antigravity Patcher                   v1.4.2 ║
  ║  رفع تحریم و قفل منطقه‌ای آنتی‌گراویتی          ║
  ║  تمیز • بدون کلید • بدون ردگیری               ║
  ╟───────────────────────────────────────────────╢
  ║  GitHub    DrAmir0240/Antigravity-Patcher     ║
  ║  Telegram  @AmirOmidi_Dev                     ║
  ╚═══════════════════════════════════════════════╝

  ─ پچ ────────────────────────────────────────────
  [1]  پچ Antigravity IDE       دور زدن قفل منطقه
  [2]  پچ Antigravity 2.0       پچ language_server
  [3]  پچ Antigravity CLI       رفع قفل ابزار agy
  [4]  پچ افزونهٔ VS Code       extension.js و باینری agy
  ─ بازگردانی ─────────────────────────────────────
  [5]  Antigravity IDE                      از بکاپ
  ...
```

---

## ✅ پیش‌نیاز و آماده‌سازی

1. **نصب نسخهٔ رسمی محصول:** بستهٔ Antigravity مورد نظر را از [سایت رسمی گوگل](https://antigravity.google/download) دانلود و نصب کنید. اگر نصب نباشد، خود پچر هنگام اجرا لینک دانلود را نشان می‌دهد.
2. **بستن کامل برنامه:** پیش از پچ، Antigravity / Antigravity IDE / VS Code را کامل ببندید تا فایل‌ها قفل نباشند.
3. **دسترسی مدیر:** پچ فایل‌های نصب‌شده در مسیرهای سیستمی را تغییر می‌دهد؛ روی ویندوز به تأیید UAC و روی لینوکس و مک به `sudo` نیاز دارید.

---

## 🚀 نصب و اجرا

### روش اول (پیشنهادی): اجرا از سورس‌کد

پیش‌نیاز: **پایتون ۳.۱۰ یا بالاتر** و **Git**.

> کتابخانه‌های `arabic-reshaper` و `python-bidi` برای رندر راست‌به‌چپ فارسی در ترمینال لازم‌اند و با `pip install -r requirements.txt` نصب می‌شوند. اگر نصب نباشند، ابزار کار می‌کند ولی متن فارسی ناخوانا (برعکس) نمایش داده می‌شود.
> در **اجرای اول** برنامه یک کالیبراسیون یک‌باره انجام می‌دهد تا مشخص شود ترمینال شما به حالت `visual` نیاز دارد یا `raw`؛ پاسخ شما ذخیره می‌شود و دیگر پرسیده نمی‌شود.

```bash
# ۱) دریافت پروژه
git clone https://github.com/khode-mwri/Antigravity-Patcher-FA.git
cd Antigravity-Patcher-FA/source

# ۲) محیط مجازی و نصب وابستگی‌ها
python -m venv .venv
# ویندوز:
.venv\Scripts\activate
# لینوکس و مک:
source .venv/bin/activate

pip install -r requirements.txt
```

```bash
# ۳) اجرا
# ویندوز:
python main.py
# لینوکس و مک:
sudo python3 main.py
```

> روی ویندوز اسکریپت خودش درخواست دسترسی مدیر (UAC) می‌دهد.

### روش دوم: نسخهٔ اجرایی آماده (`.exe` / `.deb` / `.run` / `.pkg` / `.dmg`)

نسخه‌های بیلدشده پس از انتشار تگ در بخش [**Releases همین مخزن**](https://github.com/khode-mwri/Antigravity-Patcher-FA/releases) قرار می‌گیرند. تا آن زمان می‌توانید با [دستورهای بیلد](#-ساخت-نسخهٔ-اجرایی) خودتان فایل اجرایی بسازید.

---

## 🧭 گزینه‌های منو

| کلید | دسته | عملیات | توضیح |
|:---:|:---:|:---|:---|
| **`1`** | **پچ** | پچ Antigravity IDE | پچ `main.js` و دور زدن قفل منطقه‌ای (`isGoogleInternal`) |
| **`2`** | **پچ** | پچ Antigravity 2.0 | پچ باینری `language_server` (فلگ `hasValidAuth`) |
| **`3`** | **پچ** | پچ Antigravity CLI | رفع قفل ابزار `agy` و بررسی واجد شرایط بودن حساب |
| **`4`** | **پچ** | پچ افزونهٔ VS Code | پچ `extension.js` و باینری `~/.gemini/bin/antigravity` |
| **`5`** | **بازگردانی** | Antigravity IDE | بازگردانی `main.js` از بکاپ |
| **`6`** | **بازگردانی** | Antigravity 2.0 | بازگردانی `language_server` از بکاپ |
| **`7`** | **بازگردانی** | Antigravity CLI | بازگردانی باینری `agy` از بکاپ |
| **`8`** | **بازگردانی** | افزونهٔ Antigravity VS Code | بازگردانی `extension.js` و باینری از بکاپ |
| **`9`** | **ابزارها** | بررسی به‌روزرسانی | بررسی نسخه‌های جدید در GitHub |
| **`10`** | **ابزارها** | ستاره در GitHub | باز کردن مخزن پروژه و حمایت از آن |
| **`11`** | **ابزارها** | انتخاب مسیر دستی | بازنویسی هدف شناسایی‌شده به‌صورت خودکار |
| **`12`** | **ابزارها** | درباره برنامه | اطلاعات نسخه، نویسنده و لینک‌ها |
| **`0`** | **خروج** | خروج | خروج از پچر |

---

## 📌 اجرا با مسیر دستی

اگر برنامه در مسیر غیرمعمولی نصب شده است، مسیر را مستقیم به اسکریپت بدهید:

```bash
# ویندوز
python main.py "C:\Users\<username>\AppData\Local\Programs\Antigravity IDE"
python main.py "C:\Users\<username>\AppData\Local\Programs\Antigravity\resources\bin\language_server.exe"

# لینوکس
sudo python3 main.py /usr/share/antigravity-ide
sudo python3 main.py /opt/Antigravity/resources/bin/language_server

# مک
sudo python3 main.py "/Applications/Antigravity IDE.app"
sudo python3 main.py "/Applications/Antigravity.app"
```

برای بازگردانی از بکاپ هم می‌توانید `--rollback` (یا `-r`) را به همان مسیر اضافه کنید.

---

## 💾 بکاپ و مدیریت داده‌ها

در مواردی مثل خطای **۴۲۹** (اتمام سهمیهٔ نشست)، توکن منقضی یا کَش خراب، تنها راه بازنشانی کامل محیط، ریست داده‌ها و ورود مجدد است. پچر پیش از هر تغییر خودش بکاپ می‌سازد، اما ریست دستی داده‌ها گاهی لازم است.

> نام پوشه: برای **Antigravity 2.0** پوشهٔ `Antigravity` و برای **Antigravity IDE** پوشهٔ `Antigravity IDE` است.

### ویندوز

```powershell
# ۱) بستن کامل برنامه، سپس بکاپ پوشهٔ داده
Move-Item "$env:APPDATA\Antigravity" "$env:USERPROFILE\Desktop\Antigravity-backup"

# ۲) اجرای برنامه، ورود مجدد و ارسال یک پیام آزمایشی، سپس بستن برنامه

# ۳) بازگردانی فقط تاریخچهٔ گفتگوها
Remove-Item -Recurse -Force "$env:APPDATA\Antigravity\User\globalStorage"
Remove-Item -Recurse -Force "$env:APPDATA\Antigravity\User\workspaceStorage"
Copy-Item -Recurse "$env:USERPROFILE\Desktop\Antigravity-backup\User\globalStorage" "$env:APPDATA\Antigravity\User\"
Copy-Item -Recurse "$env:USERPROFILE\Desktop\Antigravity-backup\User\workspaceStorage" "$env:APPDATA\Antigravity\User\"

# ۴) حذف بکاپ موقت
Remove-Item -Recurse -Force "$env:USERPROFILE\Desktop\Antigravity-backup"
```

> ⚠️ فایل `settings.json` را از بکاپ برنگردانید؛ تنظیمات و توکن‌های خراب قبلی را دوباره بارگذاری می‌کند.

### مک

```bash
mv ~/Library/Application\ Support/Antigravity ~/Desktop/Antigravity-backup

# پس از اجرا، ورود مجدد، یک پیام آزمایشی و بستن برنامه:
rm -rf ~/Library/Application\ Support/Antigravity/User/globalStorage
rm -rf ~/Library/Application\ Support/Antigravity/User/workspaceStorage
cp -a ~/Desktop/Antigravity-backup/User/globalStorage ~/Library/Application\ Support/Antigravity/User/
cp -a ~/Desktop/Antigravity-backup/User/workspaceStorage ~/Library/Application\ Support/Antigravity/User/

rm -rf ~/Desktop/Antigravity-backup
```

### لینوکس

```bash
pkill -f -i antigravity; sleep 2
mv ~/.config/Antigravity ~/Antigravity-backup

# پس از اجرا، ورود مجدد، یک پیام آزمایشی و بستن برنامه:
rm -rf ~/.config/Antigravity/User/globalStorage
rm -rf ~/.config/Antigravity/User/workspaceStorage
cp -a ~/Antigravity-backup/User/globalStorage ~/.config/Antigravity/User/
cp -a ~/Antigravity-backup/User/workspaceStorage ~/.config/Antigravity/User/

rm -rf ~/Antigravity-backup
```

---

## ⚠️ خطاهای متداول

### ۱. خطای HTTP 400 — `User location is not supported`

```json
{ "error": { "code": 400, "message": "User location is not supported for the API use.", "status": "FAILED_PRECONDITION" } }
```

- **علت:** گوگل موقعیت جغرافیایی، IP مسدود یا اثر انگشت تحریم‌شده را تشخیص داده است.
- **راه‌حل:** پچ را اعمال کنید (**گزینهٔ `1`**). اگر مشکل باقی ماند، از DNSهای عبور از تحریم روی سیستم یا روتر استفاده کنید و با اکانتی وارد شوید که سابقهٔ کشور مجاز دارد.

### ۲. خطای HTTP 403 — `SUBSCRIPTION_REQUIRED` (#3501)

- **علت:** این خطا به لایسنس و اعتبارسنجی **سمت سرور گوگل** مربوط است. پچر فقط فایل‌های محلی را تغییر می‌دهد و نمی‌تواند اشتراک اختصاص دهد.
- **راه‌حل:** ریجن اکانت را تغییر دهید یا از اکانت مجاز استفاده کنید؛ برای استفادهٔ پایدار پلن رسمی Google AI را تهیه کنید.

### ۳. خطای HTTP 429 — `RESOURCE_EXHAUSTED`

- **علت:** سهمیهٔ توکن تمام شده یا نشست نامعتبر است.
- **راه‌حل:** داده‌ها را طبق بخش [بکاپ و مدیریت داده‌ها](#-بکاپ-و-مدیریت-دادهها) ریست کنید.

### ۴. خطای HTTP 500

- **علت:** خطای داخلی سرورهای گوگل. پچر دخالتی در زیرساخت گوگل ندارد؛ چند دقیقه صبر کنید یا اکانت را عوض کنید.

### ۵. `pattern not found` هنگام پچ

- **علت:** نسخهٔ نصب‌شدهٔ Antigravity با امضاهای شناخته‌شدهٔ این نسخه از پچر نمی‌خواند (نسخهٔ جدیدتر یا فایل اشتباه).
- **راه‌حل:** از **گزینهٔ `11` (انتخاب مسیر دستی)** مسیر دقیق را بدهید، یا نسخهٔ به‌روز پچر / نسخهٔ سازگار Antigravity را نصب کنید.

### ۶. `Operation not permitted` در مک

1. در `System Settings → Privacy & Security → Full Disk Access` به Terminal دسترسی کامل بدهید.
2. برچسب قرنطینه را بردارید:
   ```bash
   sudo xattr -rd com.apple.quarantine "/Applications/Antigravity.app"
   sudo xattr -rd com.apple.quarantine "/Applications/Antigravity IDE.app"
   ```
3. پچر خودش امضای موقت (ad-hoc) را تمدید می‌کند:
   ```bash
   codesign --force --deep --sign - "/Applications/Antigravity IDE.app"
   ```

### ۷. بررسی به‌روزرسانی ناموفق

- **محدودیت GitHub:** GitHub برای درخواست‌های بدون توکن سهمیهٔ ساعتی دارد. پیام «بررسی به‌روزرسانی ناموفق — محدودیت GitHub» دقیقاً همین است؛ چند دقیقه بعد دوباره تلاش کنید.
- **خطای شبکه:** اتصال اینترنت یا VPN خود را برای دسترسی به `api.github.com` بررسی کنید.

### ۸. متن فارسی برعکس / آینه‌ای است

ترمینال‌ها دو دسته‌اند: بیشترشان الگوریتم دوجهتهٔ یونیکد (bidi) ندارند و باید متن را **از قبل شکل‌دهی‌شده** دریافت کنند؛ بعضی ترمینال‌ها خودشان bidi دارند و همان متن را دوباره برعکس می‌کنند. برای همین برنامه در **اجرای اول** یک کالیبراسیون یک‌باره انجام می‌دهد: یک خط نمونه نشان می‌دهد و می‌پرسد خوانا است یا نه؛ اگر «برعکس» بگویید حالت دیگر را امتحان می‌کند و انتخاب شما را ذخیره می‌کند.

اگر بعداً خواستید دستی تعیین کنید:

```bash
# حالت پیش‌فرض (تبدیل به ترتیب بصری — مناسب CMD/PowerShell/Windows Terminal)
python main.py --rtl visual

# حالت خام (برای ترمینال‌هایی که خودشان bidi دارند)
python main.py --rtl raw

> اگر در **کنسول قدیمی (conhost)** اجرا می‌کنید، ممکن است ویندوز گلیف‌های متن شکل‌دهی‌شده را نداشته باشد و
> مربع خالی نشان دهد. در این حالت برنامه به‌صورت خودکار خودش را در **Windows Terminal** باز می‌کند (مگر اینکه
> از قبل با دسترسی مدیر اجرا شده باشد یا ورودی استاندارد ریدایرکت شده باشد)؛ در غیر این صورت از **Windows Terminal**
> استفاده کنید.

یا متغیر محیطی `AG_PATCHER_RTL=visual` / `AG_PATCHER_RTL=raw` را ست کنید. برای پرسیدن دوبارهٔ کالیبراسیون، فایل تنظیمات را پاک کنید:

```bash
# ویندوز
Remove-Item "$env:APPDATA\Antigravity-Patcher\ui.json"
# لینوکس / مک
rm -f ~/.config/Antigravity-Patcher/ui.json
```

---

## 🔬 جزئیات فنی پچ

### ۱. پچ Antigravity IDE

یک عبارت شرطی در `main.js` پیدا و مقدارش ثابت `true` می‌شود؛ سپس کَش‌های کامپایل‌شده (`CachedData` و `Code Cache/js`) پاک می‌شوند تا کد اصلاح‌شده دوباره اجرا شود.

```javascript
// قبل از پچ
resetIsTierGCPTos(), this.XXX.isGoogleInternal
// پس از پچ
resetIsTierGCPTos(), true
```

### ۲. پچ باینری Antigravity 2.0 (`language_server`)

این سرویس با Go کامپایل شده است؛ پچر با شناسایی امضای بایت‌های اسمبلی، مقدار `hasValidAuth` را همیشه `true` می‌کند:

- **x86-64:** `cmp byte ptr [rax + 8], 0` به `mov byte ptr [rax + 8], 1` به‌همراه `nop`ها.
- **ARM64:** خواندن فلگ با `mov w3, #1` و نوشتن آن بازنویسی می‌شود.

### ۳. پچ Antigravity CLI (`agy`)

- **x86-64:** شاخهٔ تولید خطای عدم واجد شرایط بودن (`failure_builder`) غیرقابل دسترس می‌شود.
- **ARM64:** رجیسترهای پرچم با معادل‌های `mov w1, #1` (و در نسخه‌های جدیدتر `w2` و `w4`) پر می‌شوند.

### ۴. پچ افزونهٔ VS Code

1. **جلوگیری از دانلود مجدد:** پس از خط لاگ دانلود باینری در `extension.js`، کدی تزریق می‌شود که اگر باینری محلی در `~/.gemini/bin` باشد، مسیر همان را برگرداند.
2. **ثابت کردن کانال:** `const isChannelChanged = ...` به `const isChannelChanged = false;` تغییر می‌یابد.

> همهٔ پچ‌ها با بررسی **یگانگی امضا** اعمال می‌شوند؛ اگر امضا یکتا نباشد، پچر عمداً از حدس زدن خودداری می‌کند تا فایل سالم بماند.

---

## 🛠 ساخت نسخهٔ اجرایی

```bash
cd source
pip install pyinstaller packaging
```

```bash
# ویندوز
pyinstaller --onefile --uac-admin --icon=icon.ico --name="Antigravity_Patcher_Windows" --noupx --clean --version-file=version.txt --hidden-import=packaging --hidden-import=packaging.version --hidden-import=packaging.specifiers --hidden-import=packaging.requirements main.py

# لینوکس
pyinstaller --onefile --icon=icon.ico --name="Antigravity_Patcher_Linux" --hidden-import=packaging --hidden-import=packaging.version --hidden-import=packaging.specifiers --hidden-import=packaging.requirements main.py

# مک (Universal2)
pyinstaller --onefile --name="Antigravity_Patcher_macOS" --target-arch universal2 --hidden-import=packaging --hidden-import=packaging.version --hidden-import=packaging.specifiers --hidden-import=packaging.requirements main.py
```

---

## 📁 ساختار پروژه

```text
Antigravity-Patcher-FA/
├── README.md                  # همین راهنما (فارسی)
├── NOTICE.md                  # انتساب و فهرست تغییرات نسخهٔ فارسی
├── LICENSE                    # مجوز GPL-3.0
├── test-agy/                  # تست‌های خودکار تطابق امضای باینری‌ها
│   ├── AGENTS.md
│   └── test_cli_releases.py
└── source/                    # سورس‌کد پایتون
    ├── main.py                # نقطهٔ ورود برنامه
    ├── requirements.txt       # وابستگی‌ها
    ├── version.txt            # متادیتای فایل اجرایی
    └── patcher/
        ├── constants.py       # نسخه‌ها، رنگ‌ها و لینک‌ها
        ├── cli.py             # منوی تعاملی و جریان‌های کاربری (فارسی)
        ├── utils/             # رنگ کنسول، جایگزینی اتمیک، بکاپ، به‌روزرسانی
        ├── ide/               # پچ Antigravity IDE (main.js)
        ├── agy/               # پچ Antigravity CLI
        ├── manager/           # پچ Antigravity 2.0 (language_server)
        └── vscode/            # پچ افزونهٔ VS Code
```

---

## 📜 مجوز و انتساب

این پروژه تحت مجوز **GPL-3.0** منتشر شده است؛ متن کامل در [`LICENSE`](LICENSE). این نسخهٔ فارسی نیز **ذیل همان مجوز** توزیع می‌شود و متن مجوز، اعلان کپی‌رایت نویسندگان اصلی و فهرست تغییرات حفظ شده است.

- پروژهٔ اصلی و نویسنده: **[DrAmir0240/Antigravity-Patcher](https://github.com/DrAmir0240/Antigravity-Patcher)** — تمام اعتبار منطق پچ و طراحی اصلی از آن ایشان است.
- پایهٔ اولیه: [trustybird/AvenCores-open-antigravity-patcher](https://github.com/trustybird/AvenCores-open-antigravity-patcher)
- بخشی از راه‌حل‌ها به‌همراه [QNIX-Dev/eligibility-antigravity-patcher](https://github.com/QNIX-Dev/eligibility-antigravity-patcher) (MIT)

نسخهٔ فارسی و تغییرات آن: [khode-mwri](https://github.com/khode-mwri) — فهرست کامل تغییرات در [`NOTICE.md`](NOTICE.md).

---

## 💬 پشتیبانی

- **این فورک فارسی:** [Issues در همین مخزن](https://github.com/khode-mwri/Antigravity-Patcher-FA/issues)
- **پروژهٔ اصلی:** [DrAmir0240/Antigravity-Patcher](https://github.com/DrAmir0240/Antigravity-Patcher) — تلگرام: [@AmirOmidi_Dev](https://t.me/AmirOmidi_Dev)

---

<details>
<summary><b>🔎 کلیدواژه‌ها</b></summary>

`Antigravity Patcher` • `پچ آنتی‌گراویتی` • `رفع تحریم Antigravity` • `دور زدن قفل منطقه‌ای گوگل` • `Google Antigravity region lock bypass` • `User location is not supported` • `FAILED_PRECONDITION 400` • `Unable to verify account eligibility` • `Eligibility check failed agy` • `isGoogleInternal bypass` • `language_server patch` • `Antigravity CLI agy` • `google.google-antigravity` • `نسخهٔ فارسی Antigravity Patcher`

</details>
