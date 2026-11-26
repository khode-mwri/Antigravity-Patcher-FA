# 🔑 Antigravity Patcher — Persian Edition | Google Antigravity (IDE, 2.0, CLI `agy` & VS Code)

<p align="center">
  <b>English</b> · <a href="README.fa.md">فارسی</a> · <a href="README.ru.md">Русский</a>
</p>

<p align="center">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-GPL--3.0-blue?style=for-the-badge" alt="GPL-3.0"></a>
  <a href="https://github.com/khode-mwri/Antigravity-Patcher-FA/stargazers"><img src="https://img.shields.io/github/stars/khode-mwri/Antigravity-Patcher-FA?style=for-the-badge&logo=github&color=yellow" alt="Stars"></a>
  <img src="https://img.shields.io/badge/UI-Persian%20(RTL)-success?style=for-the-badge" alt="Persian UI">
</p>

> **This repository is a Persian-localized derivative of the open-source project [DrAmir0240/Antigravity-Patcher](https://github.com/DrAmir0240/Antigravity-Patcher).**
> The whole terminal UI (banner, menus, status/warning/error messages, prompts) is translated to Persian and
> rendered **right-to-left** in the terminal. Full upstream git history, authorship and the GPL-3.0 license are
> preserved; the exact list of changes is in [`NOTICE.md`](NOTICE.md).

An open-source patcher that removes the **region lock / geoblocking** from Google's Antigravity products:

- **Antigravity IDE** (`main.js`)
- **Antigravity 2.0** (`language_server` binary)
- **Antigravity CLI** (`agy` tool)
- **Google Antigravity** extension for VS Code

It works around the `User location is not supported for the API use` and `Unable to verify account eligibility`
errors **without a VPN and without changing your Google account region** on Windows, macOS and Linux.

> The patcher only touches **local files**. It never talks to Google servers — no keys, no tokens, no telemetry.
> Every change is backed up automatically (`.bak` / `.agybak` / `.vscodebak`) and can be reverted; the restored
> binary is byte-identical to the original.

---

## 📋 Contents

1. [Screenshot](#-screenshot)
2. [Requirements](#-requirements)
3. [Install & run](#-install--run)
4. [Menu reference](#-menu-reference)
5. [Custom path](#-custom-path)
6. [Backup & data management](#-backup--data-management)
7. [Troubleshooting](#-troubleshooting)
8. [Technical details](#-technical-details)
9. [Building binaries](#-building-binaries)
10. [Project layout](#-project-layout)
11. [License & attribution](#-license--attribution)

---

## 🖥 Screenshot

```text
  ╔═══════════════════════════════════════════════╗
  ║  Antigravity Patcher                   v1.4.0 ║
  ║  رفع تحریم و قفل منطقه‌ای آنتی‌گراویتی          ║
  ║  تمیز • بدون کلید • بدون ردگیری               ║
  ╟───────────────────────────────────────────────╢
  ║  GitHub    DrAmir0240/Antigravity-Patcher     ║
  ║  Telegram  @AmirOmidi_Dev                     ║
  ╚═══════════════════════════════════════════════╝

  ───────────────────────────────────────────── پچ
  [1]  پچ Antigravity IDE        دور زدن قفل منطقه
  [2]  پچ Antigravity 2.0        پچ language_server
  ...
```

---

## ✅ Requirements

1. **Install the official product** from [antigravity.google/download](https://antigravity.google/download).
   If it is missing, the patcher offers the download link when it starts.
2. **Close the app** (Antigravity / Antigravity IDE / VS Code) before patching so files are not locked.
3. **Administrator rights** — the patcher modifies files under system paths (UAC on Windows, `sudo` on Linux/macOS).

---

## 🚀 Install & run

### Option 1 (recommended): run from source

Requires **Python 3.10+** and **Git**.

> The Persian UI needs `arabic-reshaper` and `python-bidi` (installed with `requirements.txt`). Without them the
> tool still works, but Persian text is shown unreadable (reversed) in the terminal.
> On the first run the app calibrates once: it shows a sample line and asks whether it is readable, then stores
> the right mode (`visual` or `raw`) for your terminal.

```bash
# 1) clone
git clone https://github.com/khode-mwri/Antigravity-Patcher-FA.git
cd Antigravity-Patcher-FA/source

# 2) virtualenv + dependencies
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

```bash
# 3) run
# Windows:
python main.py
# Linux / macOS:
sudo python3 main.py
```

> On Windows the script re-launches itself elevated (UAC prompt).

### Option 2: prebuilt binaries (`.exe` / `.deb` / `.run` / `.pkg` / `.dmg`)

Built artifacts are published in [**Releases**](https://github.com/khode-mwri/Antigravity-Patcher-FA/releases)
after every release tag, or you can [build them yourself](#-building-binaries).

---

## 🧭 Menu reference

| Key | Group | Action | Description |
|:---:|:---:|:---|:---|
| **`1`** | **Patch** | Patch Antigravity IDE | Patches `main.js` (bypasses `isGoogleInternal` region check) |
| **`2`** | **Patch** | Patch Antigravity 2.0 | Patches the `language_server` binary (`hasValidAuth`) |
| **`3`** | **Patch** | Patch Antigravity CLI | Unlocks `agy` and skips the account-eligibility check |
| **`4`** | **Patch** | Patch VS Code extension | Patches `extension.js` and the `~/.gemini/bin/antigravity` binary |
| **`5`** | **Restore** | Antigravity IDE | Restores `main.js` from backup |
| **`6`** | **Restore** | Antigravity 2.0 | Restores `language_server` from backup |
| **`7`** | **Restore** | Antigravity CLI | Restores the `agy` binary from backup |
| **`8`** | **Restore** | VS Code extension | Restores `extension.js` and the binary from backup |
| **`9`** | **Tools** | Check for updates | Checks GitHub releases |
| **`10`** | **Tools** | Star on GitHub | Opens the project repository |
| **`11`** | **Tools** | Select custom path | Overrides auto-detected targets |
| **`12`** | **Tools** | About | Version, author and links |
| **`0`** | **Exit** | Exit | Quits the patcher |

---

## 📌 Custom path

If the product is installed in an unusual location, pass the path directly:

```bash
# Windows
python main.py "C:\Users\<username>\AppData\Local\Programs\Antigravity IDE"
python main.py "C:\Users\<username>\AppData\Local\Programs\Antigravity\resources\bin\language_server.exe"

# Linux
sudo python3 main.py /usr/share/antigravity-ide
sudo python3 main.py /opt/Antigravity/resources/bin/language_server

# macOS
sudo python3 main.py "/Applications/Antigravity IDE.app"
sudo python3 main.py "/Applications/Antigravity.app"
```

Add `--rollback` (or `-r`) to restore from backup instead of patching.

---

## 💾 Backup & data management

On errors such as **HTTP 429** (quota exhausted), expired tokens or a corrupted cache, resetting the data
directory and signing in again is often the only fix. The patcher always creates a backup before modifying
files, but a manual reset is sometimes needed.

> Directory names: `Antigravity` for **Antigravity 2.0**, `Antigravity IDE` for **Antigravity IDE**.

### Windows

```powershell
# 1) close the app, then back up the data folder
Move-Item "$env:APPDATA\Antigravity" "$env:USERPROFILE\Desktop\Antigravity-backup"

# 2) start the app, sign in, send one test message, close it again

# 3) restore only the chat history
Remove-Item -Recurse -Force "$env:APPDATA\Antigravity\User\globalStorage"
Remove-Item -Recurse -Force "$env:APPDATA\Antigravity\User\workspaceStorage"
Copy-Item -Recurse "$env:USERPROFILE\Desktop\Antigravity-backup\User\globalStorage" "$env:APPDATA\Antigravity\User\"
Copy-Item -Recurse "$env:USERPROFILE\Desktop\Antigravity-backup\User\workspaceStorage" "$env:APPDATA\Antigravity\User\"

# 4) remove the temporary backup
Remove-Item -Recurse -Force "$env:USERPROFILE\Desktop\Antigravity-backup"
```

> ⚠️ Do not restore `settings.json`; it brings back the broken settings and tokens.

### macOS

```bash
mv ~/Library/Application\ Support/Antigravity ~/Desktop/Antigravity-backup

# after a fresh launch, sign-in and one test message:
rm -rf ~/Library/Application\ Support/Antigravity/User/globalStorage
rm -rf ~/Library/Application\ Support/Antigravity/User/workspaceStorage
cp -a ~/Desktop/Antigravity-backup/User/globalStorage ~/Library/Application\ Support/Antigravity/User/
cp -a ~/Desktop/Antigravity-backup/User/workspaceStorage ~/Library/Application\ Support/Antigravity/User/

rm -rf ~/Desktop/Antigravity-backup
```

### Linux

```bash
pkill -f -i antigravity; sleep 2
mv ~/.config/Antigravity ~/Antigravity-backup

# after a fresh launch, sign-in and one test message:
rm -rf ~/.config/Antigravity/User/globalStorage
rm -rf ~/.config/Antigravity/User/workspaceStorage
cp -a ~/Antigravity-backup/User/globalStorage ~/.config/Antigravity/User/
cp -a ~/Antigravity-backup/User/workspaceStorage ~/.config/Antigravity/User/

rm -rf ~/Antigravity-backup
```

---

## ⚠️ Troubleshooting

### 1. HTTP 400 — `User location is not supported`

```json
{ "error": { "code": 400, "message": "User location is not supported for the API use.", "status": "FAILED_PRECONDITION" } }
```

- **Cause:** Google detected a restricted location, blocked IP or a flagged session fingerprint.
- **Fix:** apply the patch (**menu option `1`**). If it persists, use an anti-sanction DNS on the machine or
  router and sign in with an account that has a supported-country history.

### 2. HTTP 403 — `SUBSCRIPTION_REQUIRED` (#3501)

- **Cause:** license validation on **Google's servers**. The patcher only changes local files and cannot grant
  a subscription.
- **Fix:** change the account region or use an eligible account; for stable use, buy an official Google AI plan.

### 3. HTTP 429 — `RESOURCE_EXHAUSTED`

- **Cause:** token quota exhausted or invalid session.
- **Fix:** reset the data directory (see [Backup & data management](#-backup--data-management)).

### 4. HTTP 500

- **Cause:** internal Google server error. The patcher is not involved; wait a few minutes or switch accounts.

### 5. `pattern not found` while patching

- **Cause:** the installed Antigravity build does not match the signatures known to this patcher version.
- **Fix:** use **option `11` (custom path)** to point at the exact file, or update the patcher / install a
  compatible Antigravity build.

### 6. `Operation not permitted` on macOS

1. Grant Terminal **Full Disk Access** in `System Settings → Privacy & Security`.
2. Remove the quarantine flag:
   ```bash
   sudo xattr -rd com.apple.quarantine "/Applications/Antigravity.app"
   sudo xattr -rd com.apple.quarantine "/Applications/Antigravity IDE.app"
   ```
3. The patcher re-signs the app ad-hoc automatically:
   ```bash
   codesign --force --deep --sign - "/Applications/Antigravity IDE.app"
   ```

### 7. Update check failed

- **GitHub rate limit:** unauthenticated GitHub API requests are limited per hour. The message
  “update check failed — GitHub rate limit” means exactly that; retry in a few minutes.
- **Network error:** check your connection or VPN access to `api.github.com`.

### 8. Persian text looks mirrored / reversed

Terminals differ: most do not apply the Unicode bidi algorithm and therefore need the **pre-shaped** text; a few
terminals already apply bidi and would re-reverse it. That is why the app runs a **one-time calibration** on the
first launch: it displays a sample line and asks whether it reads correctly, then remembers your answer.

You can also pick the mode manually:

```bash
# default — pre-shaped visual order (CMD / PowerShell / Windows Terminal)
python main.py --rtl visual

# raw — for terminals that already apply bidi themselves
python main.py --rtl raw
```

Or set `AG_PATCHER_RTL=visual` / `AG_PATCHER_RTL=raw`. To re-run the calibration, delete the settings file:

```bash
# Windows
Remove-Item "$env:APPDATA\Antigravity-Patcher\ui.json"
# Linux / macOS
rm -f ~/.config/Antigravity-Patcher/ui.json
```

---

## 🔬 Technical details

### 1. Antigravity IDE patch

A conditional expression in `main.js` is located and its value is pinned to `true`; the compiled caches
(`CachedData` and `Code Cache/js`) are then cleared so the modified code is executed again.

```javascript
// before
resetIsTierGCPTos(), this.XXX.isGoogleInternal
// after
resetIsTierGCPTos(), true
```

### 2. Antigravity 2.0 binary patch (`language_server`)

The service is written in Go. The patcher matches the assembly byte signature and forces `hasValidAuth` to
`true`:

- **x86-64:** `cmp byte ptr [rax + 8], 0` → `mov byte ptr [rax + 8], 1` plus `nop`s.
- **ARM64:** the flag load/store pair is rewritten with `mov w3, #1`.

### 3. Antigravity CLI patch (`agy`)

- **x86-64:** the failure branch (`failure_builder`) that emits the eligibility error becomes unreachable.
- **ARM64:** the flag registers are set with `mov w1, #1` (and `w2` / `w4` on newer builds).

### 4. VS Code extension patch

1. **Prevent re-download:** after the binary download log line in `extension.js`, code is injected so the
   local binary in `~/.gemini/bin` is reused.
2. **Pin the channel:** `const isChannelChanged = ...` becomes `const isChannelChanged = false;`.

> Every patch verifies signature **uniqueness**; when a signature is ambiguous or missing the patcher refuses
> to guess instead of corrupting the file.

---

## 🛠 Building binaries

```bash
cd source
pip install pyinstaller packaging
```

```bash
# Windows
pyinstaller --onefile --uac-admin --icon=icon.ico --name="Antigravity_Patcher_Windows" --noupx --clean --version-file=version.txt --hidden-import=packaging --hidden-import=packaging.version --hidden-import=packaging.specifiers --hidden-import=packaging.requirements main.py

# Linux
pyinstaller --onefile --icon=icon.ico --name="Antigravity_Patcher_Linux" --hidden-import=packaging --hidden-import=packaging.version --hidden-import=packaging.specifiers --hidden-import=packaging.requirements main.py

# macOS (Universal2)
pyinstaller --onefile --name="Antigravity_Patcher_macOS" --target-arch universal2 --hidden-import=packaging --hidden-import=packaging.version --hidden-import=packaging.specifiers --hidden-import=packaging.requirements main.py
```

---

## 📁 Project layout

```text
Antigravity-Patcher-FA/
├── README.md                  # English (this file)
├── README.fa.md               # Persian
├── README.ru.md               # Russian
├── NOTICE.md                  # attribution and list of changes
├── LICENSE                    # GPL-3.0
├── test-agy/                  # automated binary-signature tests
│   ├── AGENTS.md
│   └── test_cli_releases.py
└── source/                    # Python source
    ├── main.py                # entry point
    ├── requirements.txt       # dependencies
    ├── version.txt            # executable metadata
    └── patcher/
        ├── constants.py       # versions, colors, links
        ├── cli.py             # interactive menu and flows
        ├── utils/             # console/rtl rendering, atomic replace, backup, updates
        ├── ide/               # Antigravity IDE patch (main.js)
        ├── agy/               # Antigravity CLI patch
        ├── manager/           # Antigravity 2.0 patch (language_server)
        └── vscode/            # VS Code extension patch
```

---

## 📜 License & attribution

Licensed under **GPL-3.0**; the full text is in [`LICENSE`](LICENSE). This Persian edition is distributed under
the same license, keeping the license text, the upstream copyright notices and the list of changes.

- Original project & author: **[DrAmir0240/Antigravity-Patcher](https://github.com/DrAmir0240/Antigravity-Patcher)** —
  all credit for the patch logic and the original design is theirs.
- Initial base: [trustybird/AvenCores-open-antigravity-patcher](https://github.com/trustybird/AvenCores-open-antigravity-patcher)
- Parts of the approach follow [QNIX-Dev/eligibility-antigravity-patcher](https://github.com/QNIX-Dev/eligibility-antigravity-patcher) (MIT)

Persian edition and its changes: [khode-mwri](https://github.com/khode-mwri) — see [`NOTICE.md`](NOTICE.md).

---

## 💬 Support

- **This fork:** [Issues](https://github.com/khode-mwri/Antigravity-Patcher-FA/issues)
- **Upstream project:** [DrAmir0240/Antigravity-Patcher](https://github.com/DrAmir0240/Antigravity-Patcher) — Telegram: [@AmirOmidi_Dev](https://t.me/AmirOmidi_Dev)

---

<details>
<summary><b>🔎 Keywords</b></summary>

`Antigravity Patcher` · `Google Antigravity region lock bypass` · `User location is not supported` ·
`FAILED_PRECONDITION 400` · `Unable to verify account eligibility` · `Eligibility check failed agy` ·
`isGoogleInternal bypass` · `language_server patch` · `Antigravity CLI agy` · `google.google-antigravity` ·
`Persian Antigravity Patcher` · `پچ آنتی‌گراویتی` · `رفع تحریم Antigravity` · `Russian Antigravity Patcher`

</details>
