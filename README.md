# 🔑 Antigravity Patcher (پچر متن‌باز Antigravity)
<p align="center">
  <a href="https://github.com/DrAmir0240/Antigravity-Patcher"><img src="https://img.shields.io/badge/GitHub-DrAmir0240-181717?style=for-the-badge&logo=github" alt="GitHub"></a>
  <a href="https://t.me/AmirOmidi_Dev"><img src="https://img.shields.io/badge/Telegram-@AmirOmidi__Dev-2CA5E0?style=for-the-badge&logo=telegram" alt="Telegram"></a>
  <img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" alt="Python">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-GPL--3.0-blue?style=for-the-badge" alt="GPL-3.0 License"></a>
</p>

پچر متن‌باز و قدرتمند برای اکوسیستم هوش مصنوعی گوگل: **Antigravity 2.0**، **Antigravity IDE**، **Antigravity CLI (ابزار `agy`)** و **افزونه Google Antigravity در VS Code**.

این ابزار محدودیت‌های منطقه‌ای، قفل جغرافیایی و تحریم‌های گوگل را **بدون نیاز به VPN و بدون نیاز به تغییر منطقه (Region) اکانت گوگل** دور می‌زند.

![نمای برنامه](https://i.ibb.co/s9Vh80CM/python-w-TPlox-Po-G4.png)

---

## 📑 فهرست مطالب
1. [💾 راهنمای بک‌آپ، پاک‌سازی و مدیریت داده‌ها](#-۱-راهنمای-بکآپ-پاکسازی-و-مدیریت-دادهها-در-پلتفرمهای-مختلف)
2. [🚀 آموزش نصب و اجرای پروژه (از صفر تا اجرا)](#-۲-آموزش-نصب-و-راهاندازی-پروژه-از-صفر-تا-اجرا)
3. [⚠️ خطاهای متداول و راه‌حل‌ها](#-۳-خطاهای-متداول-و-راهحلها-troubleshooting)
4. [❓ جزئیات فنی نحوه کارکرد پچ](#-۴-جزئیات-فنی-نحوه-کارکرد-پچ)
5. [🛠️ ساخت نسخه اجرایی (Build)](#-۵-ساخت-نسخه-اجرایی-مستقل-build)
6. [📁 ساختار فایل‌های پروژه](#-۶-ساختار-پوشهها-و-فایلهای-پروژه)
7. [📜 مجوز و کپی‌رایت](#-۷-مجوز-و-کپیرایت)
8. [💬 پشتیبانی و ارتباط](#-۸-پشتیبانی-و-ارتباط)

---

## 💾 ۱. راهنمای بک‌آپ، پاک‌سازی و مدیریت داده‌ها در پلتفرم‌های مختلف

مدیریت پوشه داده‌ها و بک‌آپ‌گیری یکی از مهم‌ترین مراحل کار با ابزارهای Antigravity است؛ زیرا در مواردی همچون خطای ۴۲۹ (اتمام سهمیه سشن)، توکن‌های منقضی‌شده یا کرش کردن کَش، تنها راه بازنشانی کامل محیط، ریست کردن داده‌ها و ورود مجدد است. علاوه بر این، خود پچر قبل از اعمال هر تغییری به‌صورت خودکار از فایل‌ها بک‌آپ با پسوندهای `.bak`، `.agybak` و `.vscodebak` تهیه می‌کند.

> **تفاوت نام پوشه در نسخه‌ها:**
> - برای **Antigravity 2.0**: نام پوشه `Antigravity` است.
> - برای **Antigravity IDE**: نام پوشه `Antigravity IDE` است.
> *(در دستورات زیر پوشه پیش‌فرض `Antigravity` در نظر گرفته شده است؛ در صورت استفاده از IDE نام آن را تنظیم کنید).*

---

### 💻 ویندوز (Windows)

#### مرحله ۱: بستن کامل برنامه
ابتدا نرم‌افزار را ببندید و در Task Manager مطمئن شوید پردازشی از Antigravity باز نمانده باشد.

#### مرحله ۲: جابجایی و بک‌آپ پوشه داده‌ها
کلیدهای `Win + X` را زده و **PowerShell** یا **Terminal** را باز کنید:
```powershell
Move-Item "$env:APPDATA\Antigravity" "$env:USERPROFILE\Desktop\Antigravity-backup"
```

#### مرحله ۳: باز کردن برنامه و بررسی
برنامه Antigravity را اجرا کرده، وارد اکانت گوگل خود شوید و یک پیام آزمایشی ارسال کنید تا توکن‌ها و کانفیگ جدید ساخته شوند. سپس برنامه را مجدداً ببندید.

#### مرحله ۴: بازگردانی تاریخچه گفتگوها (چت‌ها)
برای اینکه تاریخچه پیام‌های قبلی را بدون بازگرداندن فایل‌های مشکل‌دار بازیابی کنید، فقط پوشه‌های ذخیره‌سازی چت را برگردانید:
```powershell
# حذف پوشه‌های خام فعلی
Remove-Item -Recurse -Force "$env:APPDATA\Antigravity\User\globalStorage"
Remove-Item -Recurse -Force "$env:APPDATA\Antigravity\User\workspaceStorage"

# کپی تاریخچه پیام‌ها از بک‌آپ
Copy-Item -Recurse "$env:USERPROFILE\Desktop\Antigravity-backup\User\globalStorage" "$env:APPDATA\Antigravity\User\"
Copy-Item -Recurse "$env:USERPROFILE\Desktop\Antigravity-backup\User\workspaceStorage" "$env:APPDATA\Antigravity\User\"
```
> ⚠️ **توجه:** به هیچ عنوان فایل `settings.json` را از بک‌آپ برنگردانید؛ چرا که تنظیمات و توکن‌های خراب قبلی را مجدداً بارگذاری خواهد کرد.

#### مرحله ۵: حذف بک‌آپ موقت
پس از باز کردن برنامه و اطمینان از سلامت چت‌ها، بک‌آپ موقت روی دسکتاپ را حذف کنید:
```powershell
Remove-Item -Recurse -Force "$env:USERPROFILE\Desktop\Antigravity-backup"
```

---

### 🍏 مک (macOS)

#### مرحله ۱: بستن کامل برنامه
برنامه را با کلیدهای میانبر `Cmd + Q` به‌طور کامل ببندید (مطمئن شوید نقطه زیر آیکون در Dock محو شده باشد).

#### مرحله ۲: بک‌آپ و انتقال پوشه داده‌ها
ترمینال مک را باز کرده و دستور زیر را اجرا کنید:
```bash
mv ~/Library/Application\ Support/Antigravity ~/Desktop/Antigravity-backup
```

#### مرحله ۳: اجرای موقت و ورود مجدد
برنامه را باز کرده، مجدداً لاگین کنید و یک درخواست تستی ارسال نمایید. سپس برنامه را با `Cmd + Q` ببندید.

#### مرحله ۴: بازگردانی چت‌ها از بک‌آپ
```bash
rm -rf ~/Library/Application\ Support/Antigravity/User/globalStorage
rm -rf ~/Library/Application\ Support/Antigravity/User/workspaceStorage

cp -a ~/Desktop/Antigravity-backup/User/globalStorage ~/Library/Application\ Support/Antigravity/User/
cp -a ~/Desktop/Antigravity-backup/User/workspaceStorage ~/Library/Application\ Support/Antigravity/User/
```

#### مرحله ۵: حذف بک‌آپ
پس از اطمینان از دسترسی به چت‌ها:
```bash
rm -rf ~/Desktop/Antigravity-backup
```

---

### 🐧 لینوکس (Linux)

مسیر داده‌ها در لینوکس معمولاً `~/.config/Antigravity` (یا متغیر `$XDG_CONFIG_HOME`) است.

#### مرحله ۱: بستن کامل پردازش‌ها
```bash
pkill -f -i antigravity; sleep 2; pgrep -a -i antigravity || echo "برنامه با موفقیت بسته شد"
```

#### مرحله ۲: انتقال به بک‌آپ
```bash
mv ~/.config/Antigravity ~/Antigravity-backup
```

#### مرحله ۳: لاگین و تست
نرم‌افزار را باز کرده، وارد شوید، یک پرامپت تستی بفرستید و مجدداً با دستور مرحله ۱ آن را ببندید.

#### مرحله ۴: بازگردانی تاریخچه چت‌ها
```bash
rm -rf ~/.config/Antigravity/User/globalStorage
rm -rf ~/.config/Antigravity/User/workspaceStorage

cp -a ~/Antigravity-backup/User/globalStorage ~/.config/Antigravity/User/
cp -a ~/Antigravity-backup/User/workspaceStorage ~/.config/Antigravity/User/
```

#### مرحله ۵: حذف بک‌آپ
```bash
rm -rf ~/Antigravity-backup
```

---

## 🚀 ۲. آموزش نصب و راه‌اندازی پروژه (از صفر تا اجرا)

شما می‌توانید از **نصاب‌ها و برنامه‌های آماده یک‌کلیکی** (بدون نیاز به نصب پایتون یا پیش‌نیاز) از بخش [**Releases گیت‌هاب**](https://github.com/DrAmir0240/Antigravity-Patcher/releases/latest) استفاده کنید، و یا پروژه را از طریق سورس‌کد پایتون اجرا نمایید.

> ⚠️ **نکته مهم قبل از اجرا:** حتماً نرم‌افزارهای Antigravity، Antigravity IDE و VS Code را کاملاً ببندید تا فایل‌ها هنگام پچ شدن درگیر نباشند.

---

### ✨ روش اول (پیشنهادی): نصب و اجرای یک‌کلیکی با اپ اختصاصی هر پلتفرم

ابتدا وارد صفحه [**آخرین نسخه در بخش Releases**](https://github.com/DrAmir0240/Antigravity-Patcher/releases/latest) شوید و فایل متناسب با سیستم‌عامل خود را دانلود کنید:

| سیستم‌عامل | فرمت فایل | نام فایل در بخش Releases | توضیح |
|:---|:---:|:---|:---|
| **Windows (x64)** | `.exe` | `Antigravity_Patcher_Windows.exe` | فایل اجرایی مستقل ویندوز با دسترسی خودکار Administrator |
| **Ubuntu / Debian** | `.deb` | `Antigravity_Patcher_Ubuntu.deb` | پکیج نصبی استاندارد اوبونتو، دبیان و مینت همراه با آیکون در منوی برنامه‌ها |
| **Linux (Portable)** | `.run` | `Antigravity_Patcher_Linux.run` | نسخه پرتابل و بدون نیاز به نصب برای تمامی توزیع‌های لینوکس |
| **macOS (Installer)** | `.pkg` | `Antigravity_Patcher_macOS.pkg` | نصاب یک‌کلیکی مک (سازگار با تراشه‌های Intel و Apple Silicon M1/M2/M3/M4) |
| **macOS (Disk Image)** | `.dmg` | `Antigravity_Patcher_macOS.dmg` | ایمیج استاندارد مک حاوی برنامه گرافیکی `Antigravity Patcher.app` |

---

#### 💻 ۱. آموزش اجرا با اپ ویندوز (`.exe`)
1. فایل **`Antigravity_Patcher_Windows.exe`** را از بخش Releases دانلود کنید.
2. روی فایل **دو بار کلیک (Double-Click)** کنید.
3. در پنجره UAC ویندوز گزینه **Yes** را بزنید تا برنامه با دسترسی Administrator باز شود.
4. شماره گزینه مورد نظر (مثلاً `1` برای IDE یا `2` برای Antigravity 2.0) را وارد کرده و کلید `Enter` را بزنید.

---

#### 🐧 ۲. آموزش نصب و اجرا با اپ اوبونتو و لینوکس (`.deb` و `.run`)

##### الف) نصب یک‌کلیکی در اوبونتو، دبیان و لینوکس مینت (`Antigravity_Patcher_Ubuntu.deb`):
1. فایل **`Antigravity_Patcher_Ubuntu.deb`** را دانلود کنید.
2. **روش گرافیکی:** روی فایل `.deb` دو بار کلیک کنید تا در **App Center / Software Install** باز شود و دکمه **Install** را بزنید.  
   *(یا در ترمینال دستور زیر را در پوشه دانلود اجرا کنید)*:
   ```bash
   sudo apt install ./Antigravity_Patcher_Ubuntu.deb
   ```
3. پس از نصب، وارد منوی برنامه‌های اوبونتو (**Show Apps**) شوید و روی آیکون **Antigravity Patcher** کلیک کنید (یا در ترمینال دستور `sudo antigravity-patcher` را بزنید).

##### ب) اجرای نسخه پرتابل در کلیه توزیع‌های لینوکس (`Antigravity_Patcher_Linux.run`):
1. فایل **`Antigravity_Patcher_Linux.run`** را دانلود کنید.
2. روی فایل راست‌کلیک کرده، وارد **Properties → Permissions** شوید و تیک **Allow executing file as program** را فعال کنید، سپس روی فایل دو بار کلیک کنید.  
   *(یا با یک دستور در ترمینال اجرا نمایید)*:
   ```bash
   chmod +x Antigravity_Patcher_Linux.run && sudo ./Antigravity_Patcher_Linux.run
   ```

---

#### 🍏 ۳. آموزش نصب و اجرا با اپ مک (`.pkg` و `.dmg`)

##### الف) نصب یک‌کلیکی با پکیج نصاب مک (`Antigravity_Patcher_macOS.pkg` - پیشنهادی):
1. فایل **`Antigravity_Patcher_macOS.pkg`** را دانلود کرده و روی آن دو بار کلیک کنید.
2. مراحل نصب (**Continue → Install**) را طی کرده و رمز مک خود را وارد نمایید (این نصاب به‌طور خودکار برنامه را در پوشه `Applications` نصب کرده و محدودیت قرنطینه Gatekeeper اپل را نیز برمی‌دارد).
3. از داخل **Launchpad** یا پوشه **Applications** روی برنامه **Antigravity Patcher** کلیک کنید؛ برنامه به‌صورت خودکار پنجره Terminal را باز کرده و منوی پچر را اجرا می‌کند.

##### ب) استفاده از دیسک ایمیج مک (`Antigravity_Patcher_macOS.dmg`):
1. فایل **`Antigravity_Patcher_macOS.dmg`** را باز کنید.
2. برنامه **Antigravity Patcher** را به داخل پوشه **Applications** بکشید (Drag & Drop) و سپس آن را اجرا کنید.
   > 💡 *نکته:* اگر هنگام باز کردن فایل `.pkg` یا `.dmg` پیام امنیتی اپل (`unidentified developer`) نمایش داده شد، روی فایل **راست‌کلیک (Control + Click)** کرده و گزینه **Open** را بزنید، یا در `System Settings → Privacy & Security` روی **Open Anyway** کلیک کنید.

---

### 🐍 روش دوم: نصب و اجرا از طریق سورس‌کد پایتون

اگر تمایل دارید اسکریپت را مستقیماً با پایتون از روی سورس‌کد اجرا کنید، مراحل زیر را دنبال نمایید:

### گام ۱: نصب پایتون و گیت

#### در ویندوز (Windows):
1. **دانلود پایتون:** پایتون نسخه 3.10 یا بالاتر را از سایت رسمی [python.org](https://www.python.org/downloads/) دانلود کنید.
2. **نکته بسیار مهم هنگام نصب:** در اولین پنجره نصاب پایتون، حتماً تیک گزینه **`Add python.exe to PATH`** را در پایین پنجره فعال کنید و سپس روی `Install Now` بزنید.
3. **نصب Git:** برنامه گیت را از [git-scm.com](https://git-scm.com/) دانلود و با تنظیمات پیش‌فرض نصب نمایید.

#### در لینوکس (Ubuntu / Debian / Linux Mint):
ترمینال را باز کرده و پکیج‌های پایتون و ابزارهای مرتبط را نصب کنید:
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git -y
```

*(در توزیع‌های مبتنی بر Arch: `sudo pacman -S python python-pip git` | در Fedora: `sudo dnf install python3 python3-pip git`)*

#### در مک (macOS):
ابزارهای خط فرمان اپل و Homebrew را نصب کرده و سپس پایتون را نصب کنید:
```bash
xcode-select --install
brew install python git
```

---

### گام ۲: دانلود و کلون کردن ریپازیتوری

ترمینال (یا PowerShell) را باز کرده و پروژه را کلون کنید:

```bash
# از طریق HTTPS
git clone https://github.com/DrAmir0240/Antigravity-Patcher.git

# یا از طریق SSH
git clone git@github.com:DrAmir0240/Antigravity-Patcher.git

# ورود به پوشه پروژه
cd Antigravity-Patcher
```

---

### گام ۳: راه‌اندازی محیط مجازی و نصب وابستگی‌ها

توصیه می‌شود وابستگی‌ها در محیط ایزوله مجازی پایتون (`venv`) نصب شوند:

#### ویندوز:
```powershell
cd source
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

#### لینوکس و مک:
```bash
cd source
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

### گام ۴: اجرای پچر (Run)

> ⚠️ **قبل از اجرا:** حتماً نرم‌افزار Antigravity یا Antigravity IDE را کاملاً ببندید تا فایل‌ها توسط سیستم قفل نباشند.

#### نحوه اجرا:
* **در ویندوز:**
  ```powershell
  python main.py
  ```
  *(اسکریپت در صورت نیاز به‌طور خودکار درخواست دسترسی ادمین UAC را نمایش می‌دهد).*
* **در لینوکس:**
  ```bash
  sudo python3 main.py
  ```
  *(استفاده از sudo به دلیل دسترسی به دایرکتوری‌های سیستمی مانند `/usr/share/antigravity-ide` الزامی است).*
* **در مک:**
  ```bash
  sudo python3 main.py
  ```

---

### جدول گزینه‌های منوی برنامه

پس از اجرا، منوی تعاملی زیر را مشاهده خواهید کرد:

| کلید | دسته‌بندی | عملیات | توضیحات |
|:---:|:---:|:---|:---|
| **`1`** | **PATCH** | **Antigravity IDE patch** | پچ فایل `main.js` در Antigravity IDE (دور زدن تحریم و قفل ریجن) |
| **`2`** | **PATCH** | **Antigravity 2.0 patch** | پچ باینری `language_server` برای Antigravity 2.0 |
| **`3`** | **PATCH** | **Antigravity CLI (agy) patch** | پچ باینری ترمینال `agy` (حذف صفحه Eligibility Check) |
| **`4`** | **PATCH** | **Antigravity VS Code Patch** | پچ افزونه VS Code و باینری داخل `~/.gemini/bin/antigravity` |
| **`5`** | **RESTORE** | **Antigravity IDE** | بازگردانی فایل اصلی `main.js` نرم‌افزار IDE از بک‌آپ |
| **`6`** | **RESTORE** | **Antigravity 2.0** | بازگردانی باینری اصلی `language_server` از بک‌آپ |
| **`7`** | **RESTORE** | **Antigravity CLI** | بازگردانی باینری `agy` از بک‌آپ |
| **`8`** | **RESTORE** | **Antigravity VS Code** | بازگردانی `extension.js` و باینری VS Code از بک‌آپ |
| **`9`** | **TOOLS** | **Check for updates** | بررسی وجود نسخه‌های جدیدتر در گیت‌هاب |
| **`10`** | **TOOLS** | **Open GitHub repository** | باز کردن مخزن رسمی پروژه در مرورگر |
| **`11`** | **TOOLS** | **Select custom path** | تعیین دستی مسیر فایل‌ها در صورت عدم شناسایی خودکار |
| **`12`** | **TOOLS** | **About program** | اطلاعات برنامه، گیت‌هاب و راه ارتباطی |
| **`0`** | **EXIT** | **Exit** | خروج ایمن از پچر |

---

### اجرا با تعیین مسیر دستی (Custom Path Arguments)
اگر برنامه در مسیری غیرمعمول نصب شده باشد، می‌توانید مسیر را مستقیماً در دستور پاس دهید:

```bash
# ویندوز:
python main.py "C:\Users\<username>\AppData\Local\Programs\Antigravity IDE"
python main.py "C:\Users\<username>\AppData\Local\Programs\Antigravity\resources\bin\language_server.exe"

# لینوکس:
sudo python3 main.py /usr/share/antigravity-ide
sudo python3 main.py /opt/Antigravity/resources/bin/language_server

# مک:
sudo python3 main.py "/Applications/Antigravity IDE.app"
sudo python3 main.py "/Applications/Antigravity.app"
```

---

## ⚠️ ۳. خطاهای متداول و راه‌حل‌ها (Troubleshooting)

در این بخش رایج‌ترین خطاهای شبکه، سرور، مجوزها و شیوه برطرف کردن آنها توضیح داده شده است:

---

### ۱. خطای HTTP 400 Bad Request (`User location is not supported`)
```json
{
  "error": {
    "code": 400,
    "message": "User location is not supported for the API use.",
    "status": "FAILED_PRECONDITION"
  }
}
```
* **علت:** گوگل متوجه موقعیت جغرافیایی نامعتبر، IP مسدود یا اثر انگشت تحریم‌شده در نشست کاربری شما شده است.
* **راه‌حل:**
  1. پچ را اعمال کنید (**گزینه `1` در منو**). این پچ بررسی‌های داخلی موقعیت را خنثی می‌کند.
  2. در صورت باقی ماندن مشکل، از DNSهای گذر از تحریم مانند **[Xbox DNS](https://xbox-dns.ru/)**، **[dns.malw.link](https://info.dns.malw.link/)** یا **[GeoHide](https://dns.geohide.ru:8443/)** روی سیستم یا روتر خود استفاده کنید.
  3. از یک اکانت گوگل با سابقه در کشور مجاز استفاده کنید.

---

### ۲. خطای HTTP 403 Forbidden / SUBSCRIPTION_REQUIRED (#3501)
```json
{
  "error": {
    "code": 403,
    "message": "You do not have a valid license of this product. Please contact your administrator to request a license. (#3501)",
    "status": "PERMISSION_DENIED"
  }
}
```
* **علت:** این خطا مستقیماً به **لایسنس و اعتبارسنجی سمت سرورهای ابری گوگل** مربوط است. پچر فقط فایل‌های لوکال را دستکاری می‌کند و نمی‌تواند به اکانت شما اشتراک اختصاص دهد.
* **راه‌حل:**
  1. ریجن اکانت گوگل خود را به کشوری که دسترسی آزاد دارد تغییر دهید یا با یک اکانت خارجی وارد شوید.
  2. در صورت نیاز به استفاده پایدار، یکی از پلن‌های رسمی Google AI (پلاس، پرو یا اولترا) را تهیه فرمایید.

---

### ۳. خطای HTTP 429 Too Many Requests / RESOURCE_EXHAUSTED
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
* **علت:** سهمیه توکن‌ها تمام شده یا نشست کاری در وضعیت نامعتبر قرار گرفته است.
* **راه‌حل:**
  پوشه داده‌ها را طبق دستورالعمل کامل [بخش ۱ (راهنمای بک‌آپ و پاک‌سازی داده‌ها)](#-۱-راهنمای-بکآپ-پاکسازی-و-مدیریت-دادهها-در-پلتفرمهای-مختلف) ریست کنید تا سهمیه تازه و توکن‌های نو تولید شوند.

---

### ۴. خطای HTTP 500 Internal Server Error
```
Error: HTTP 500 Internal Server Error
{
  "error": {
    "code": 500,
    "message": "Internal error encountered.",
    "status": "INTERNAL"
  }
}
```
* **علت:** خطای داخلی سرورهای پردازشی گوگل.
* **راه‌حل:** پچر دخالتی در زیرساخت گوگل ندارد؛ دقایقی صبر کرده و در صورت تداوم، اکانت گوگل خود را تغییر دهید.

---

### ۵. خطای پچ: `✗ isGoogleInternal -> true (auth) — pattern not found`
* **علت:** پچر فایل `main.js` مربوط به برنامه دیگری از الکترون را پیدا کرده است یا در پوشه فعلی فایل اشتباهی وجود دارد.
* **راه‌حل:**
  1. در منوی اصلی گزینه **`11` (Select custom path)** را انتخاب کنید.
  2. مسیر دقیق فایل `main.js` داخل پوشه `resources/app/out/main.js` نرم‌افزار را دستی وارد کنید.

---

### ۶. خطای مجوز `Operation not permitted` و اجرای مک (macOS)
اگر در مک با خطای `[Errno 1] Operation not permitted` مواجه شدید یا برنامه پس از پچ باز نشد:
1. در تنظیمات مک به مسیر زیر بروید و به نرم‌افزار Terminal دسترسی کامل به دیسک بدهید:
   `System Settings → Privacy & Security → Full Disk Access`
2. برچسب قرنطینه اپل را با دستور زیر از روی برنامه بردارید:
   ```bash
   sudo xattr -rd com.apple.quarantine "/Applications/Antigravity.app"
   sudo xattr -rd com.apple.quarantine "/Applications/Antigravity IDE.app"
   ```
3. پچر به‌صورت خودکار امضای امنیتی برنامه را با فرمان زیر تمدید (Ad-hoc re-sign) می‌کند:
   ```bash
   codesign --force --deep --sign - "/Applications/Antigravity IDE.app"
   ```

---

## ❓ ۴. جزئیات فنی نحوه کارکرد پچ

این پچر از تکنیک‌های پیشرفته دستکاری حافظه و بایت‌های فایل کامپایل‌شده استفاده می‌کند:

### ۱. پچ Antigravity IDE
عبارت زیر در فایل `main.js` جستجو شده و شرط احراز صلاحیت داخلی گوگل همیشه برقرار می‌شود:
```javascript
// قبل از پچ:
resetIsTierGCPTos(),this.XXX.isGoogleInternal

// پس از پچ:
resetIsTierGCPTos(),true
```
همچنین کَش‌های کامپایل‌شده جاوااسکریپت (`CachedData` و `Code Cache/js`) پاک می‌شوند تا IDE مجبور به اجرای کد اصلاح‌شده گردد.

### ۲. پچ باینری Antigravity 2.0 (`language_server`)
این سرویس به زبان Go کامپایل شده است. پچر با شناسایی امضای بایت‌های اسمبلی تغییرات زیر را ایجاد می‌کند:
* **در x86-64:** دستور `cmp byte ptr [rax + 8], 0` به `mov byte ptr [rax + 8], 1` همراه با دستورهای `nop` تغییر می‌یابد.
* **در ARM64:** دستور خواندن فلگ به مقدار ثابت ۱ (`mov w3, #1`) بازنویسی می‌شود.
در نتیجه خروجی متد تایید صلاحیت (`hasValidAuth`) همواره مقدار `true` خواهد داشت.

### ۳. پچ ابزار ترمینال Antigravity CLI (`agy`)
* **در x86-64:** با تغییر دستور شرطی، شاخه تولید خطای عدم صلاحیت (`failure_builder`) غیرقابل دسترس می‌شود.
* **در ARM64:** رجیسترهای پرچم وضعیت با دستورات معادل مقدار ۱ پر می‌شوند (`mov w1, #1` و در نسخه‌های جدیدتر گیت‌های `w2` و `w4`).

### ۴. پچ افزونه رسمی VS Code
1. **جلوگیری از دانلود مجدد:** بعد از خط لاگ دانلود باینری‌ها در `extension.js`، کدی تزریق می‌شود که در صورت وجود باینری محلی در `~/.gemini/bin`، فوراً مسیر همان را برگردانده و مانع از دانلود مجدد فایل از گوگل شود.
2. **ثابت کردن وضعیت کانال:** دستور `const isChannelChanged = ...` به `const isChannelChanged = false;` تغییر می‌یابد.

---

## 🛠️ ۵. ساخت نسخه اجرایی مستقل (Build)

اگر مایلید پروژه را به یک فایل مستقل اجرایی بدون نیاز به نصب پایتون تبدیل کنید:

```bash
cd source
pip install pyinstaller packaging
```

* **ویندوز (Windows):**
  ```bash
  pyinstaller --onefile --uac-admin --icon=icon.ico --name="Antigravity_Patcher_Windows" --noupx --clean --version-file=version.txt main.py
  ```
* **لینوکس (Linux):**
  ```bash
  pyinstaller --onefile --icon=icon.ico --name="Antigravity_Patcher_Linux" --hidden-import=packaging --hidden-import=packaging.version --hidden-import=packaging.specifiers --hidden-import=packaging.requirements main.py
  ```
* **مک (macOS Universal2):**
  ```bash
  pyinstaller --onefile --name="Antigravity_Patcher_macOS" --target-arch universal2 --hidden-import=packaging --hidden-import=packaging.version --hidden-import=packaging.specifiers --hidden-import=packaging.requirements main.py
  ```

---

## 📁 ۶. ساختار پوشه‌ها و فایل‌های پروژه
```text
Antigravity-Patcher/
├── README.md               # راهنمای کامل و مستندات پروژه به زبان فارسی
├── LICENSE                 # مجوز انتشار نرم‌افزار (GPL-3.0)
├── test-agy/               # تست‌های خودکار بررسی امضای باینری‌ها
│   ├── AGENTS.md           # راهنمای فنی تست‌های اسمبلی برای ایجنت‌ها
│   └── test_cli_releases.py# تست تطابق کدهای ماشین با آخرین ریلیزهای رسمی
└── source/                 # سورس‌کد اصلی به زبان پایتون
    ├── main.py             # نقطه ورود برنامه و اعتبارسنجی مجوزهای سیستم
    ├── requirements.txt    # کتابخانه‌های مورد نیاز پایتون
    ├── version.txt         # متادیتا و مشخصات فایل کامپایل‌شده
    └── patcher/
        ├── constants.py    # تنظیمات مرکزی، نسخه‌ها و آدرس‌های پشتیبانی
        ├── cli.py          # منوی تعاملی کنسول، گزینه‌ها و ورودی‌ها
        ├── utils/          # توابع کمکی (جایگزینی اتمیک فایل‌ها، رنگ، کنسول)
        ├── ide/            # ماژول پچ Antigravity IDE (فایل main.js)
        ├── agy/            # ماژول پچ بایت‌های Antigravity CLI
        ├── manager/        # ماژول پچ بایت‌های Antigravity 2.0 (language_server)
        └── vscode/         # ماژول پچ افزونه و باینری VS Code
```

---

## 📜 ۷. مجوز و کپی‌رایت
این پروژه تحت مجوز آزاد **GPL-3.0** منتشر شده است. متن کامل مجوز در فایل [`LICENSE`](LICENSE) قابل مشاهده است.

بخشی از راه‌حل‌ها و منطق فنی پروژه بر اساس دستاوردهای مخزن [eligibility-antigravity-patcher](https://github.com/QNIX-Dev/eligibility-antigravity-patcher) تحت مجوز MIT پیاده‌سازی شده است.

---

## 💬 ۸. پشتیبانی و ارتباط
برای ارتباط، دریافت آخرین اخبار، گزارش باگ یا درخواست راهنمایی:
* **مخزن رسمی گیت‌هاب:** [DrAmir0240/Antigravity-Patcher](https://github.com/DrAmir0240/Antigravity-Patcher)
* **پشتیبانی تلگرام:** [@AmirOmidi_Dev](https://t.me/AmirOmidi_Dev)
