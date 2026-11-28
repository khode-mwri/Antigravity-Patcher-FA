# 🔑 Antigravity Patcher — персидская версия | Google Antigravity (IDE, 2.0, CLI `agy` и VS Code)

<p align="center">
  <a href="README.md">English</a> · <a href="README.fa.md">فارسی</a> · <b>Русский</b>
</p>

<p align="center">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-GPL--3.0-blue?style=for-the-badge" alt="GPL-3.0"></a>
  <a href="https://github.com/khode-mwri/Antigravity-Patcher-FA/stargazers"><img src="https://img.shields.io/github/stars/khode-mwri/Antigravity-Patcher-FA?style=for-the-badge&logo=github&color=yellow" alt="Stars"></a>
  <img src="https://img.shields.io/badge/UI-Persian%20(RTL)-success?style=for-the-badge" alt="Persian UI">
</p>

> **Этот репозиторий — персидская локализация открытого проекта [DrAmir0240/Antigravity-Patcher](https://github.com/DrAmir0240/Antigravity-Patcher).**
> Весь интерфейс терминала (баннер, меню, сообщения о статусе, предупреждения, ошибки и подсказки) переведён
> на персидский язык и выводится **справа налево**. Полная история git, авторство и лицензия GPL-3.0 сохранены;
> список изменений — в [`NOTICE.md`](NOTICE.md).

Открытый патчер, снимающий **региональную блокировку (геоблок)** с продуктов Google Antigravity:

- **Antigravity IDE** (`main.js`)
- **Antigravity 2.0** (бинарник `language_server`)
- **Antigravity CLI** (инструмент `agy`)
- **Расширение Google Antigravity** для VS Code

Обходит ошибки `User location is not supported for the API use` и `Unable to verify account eligibility`
**без VPN и без смены региона аккаунта Google** на Windows, macOS и Linux.

> Патчер изменяет только **локальные файлы** и не обращается к серверам Google: без ключей, токенов и
> телеметрии. Перед каждым изменением создаётся резервная копия (`.bak` / `.agybak` / `.vscodebak`),
> восстановленный бинарник побайтово совпадает с оригиналом.

---

## 📋 Содержание

1. [Скриншот](#-скриншот)
2. [Требования](#-требования)
3. [Установка и запуск](#-установка-и-запуск)
4. [Пункты меню](#-пункты-меню)
5. [Запуск с указанием пути](#-запуск-с-указанием-пути)
6. [Резервные копии и данные](#-резервные-копии-и-данные)
7. [Частые ошибки](#-частые-ошибки)
8. [Технические детали](#-технические-детали)
9. [Сборка бинарников](#-сборка-бинарников)
10. [Структура проекта](#-структура-проекта)
11. [Лицензия и авторство](#-лицензия-и-авторство)

---

## 🖥 Скриншот

```text
  ╔═══════════════════════════════════════════════╗
  ║  Antigravity Patcher                   v1.4.2 ║
  ║  رفع تحریم و قفل منطقه‌ای آنتی‌گراویتی          ║
  ║  تمیز • بدون کلید • بدون ردگیری               ║
  ╟───────────────────────────────────────────────╢
  ║  GitHub    DrAmir0240/Antigravity-Patcher     ║
  ║  Telegram  @bxiqm                     ║
  ╚═══════════════════════════════════════════════╝

  ───────────────────────────────────────────── پچ
  [1]  پچ Antigravity IDE        دور زدن قفل منطقه
  [2]  پچ Antigravity 2.0        پچ language_server
  ...
```

---

## ✅ Требования

1. **Установите официальный продукт** с [antigravity.google/download](https://antigravity.google/download).
   Если он не найден, патчер сам предложит ссылку на скачивание.
2. **Закройте приложение** (Antigravity / Antigravity IDE / VS Code) перед патчингом, чтобы файлы не были
   заблокированы.
3. **Права администратора** — патчер изменяет файлы в системных каталогах (UAC в Windows, `sudo` в Linux/macOS).

---

## 🚀 Установка и запуск

### Вариант 1 (рекомендуется): запуск из исходников

Нужны **Python 3.10+** и **Git**.

> Персидскому интерфейсу нужны библиотеки `arabic-reshaper` и `python-bidi` (ставятся из `requirements.txt`).
> Без них инструмент работает, но персидский текст в терминале будет нечитаемым (перевёрнутым).
> При первом запуске программа один раз калибруется: показывает строку-образец и спрашивает, читается ли она,
> после чего запоминает подходящий режим (`visual` или `raw`) для вашего терминала.

```bash
# 1) клонирование
git clone https://github.com/khode-mwri/Antigravity-Patcher-FA.git
cd Antigravity-Patcher-FA/source

# 2) виртуальное окружение и зависимости
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

```bash
# 3) запуск
# Windows:
python main.py
# Linux / macOS:
sudo python3 main.py
```

> В Windows скрипт сам перезапускается с правами администратора (запрос UAC).

### Вариант 2: готовые сборки (`.exe` / `.deb` / `.run` / `.pkg` / `.dmg`)

Собранные файлы публикуются в разделе [**Releases**](https://github.com/khode-mwri/Antigravity-Patcher-FA/releases)
после каждого тега, либо соберите их самостоятельно — см. [Сборка бинарников](#-сборка-бинарников).

---

## 🧭 Пункты меню

| Клавиша | Раздел | Действие | Описание |
|:---:|:---:|:---|:---|
| **`1`** | **Патч** | Antigravity IDE | Патч `main.js` (обход `isGoogleInternal`) |
| **`2`** | **Патч** | Antigravity 2.0 | Патч бинарника `language_server` (`hasValidAuth`) |
| **`3`** | **Патч** | Antigravity CLI | Разблокировка `agy` и проверки допустимости аккаунта |
| **`4`** | **Патч** | Расширение VS Code | Патч `extension.js` и бинарника `~/.gemini/bin/antigravity` |
| **`5`** | **Восстановление** | Antigravity IDE | Восстановить `main.js` из резервной копии |
| **`6`** | **Восстановление** | Antigravity 2.0 | Восстановить `language_server` из копии |
| **`7`** | **Восстановление** | Antigravity CLI | Восстановить бинарник `agy` из копии |
| **`8`** | **Восстановление** | Расширение VS Code | Восстановить `extension.js` и бинарник |
| **`9`** | **Инструменты** | Проверить обновления | Проверка релизов на GitHub |
| **`10`** | **Инструменты** | Звезда на GitHub | Открыть репозиторий проекта |
| **`11`** | **Инструменты** | Указать путь вручную | Переопределить автоопределение |
| **`12`** | **Инструменты** | О программе | Версия, автор и ссылки |
| **`0`** | **Выход** | Выход | Завершить работу патчера |

---

## 📌 Запуск с указанием пути

Если продукт установлен в нестандартное место, передайте путь аргументом:

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

Добавьте `--rollback` (или `-r`), чтобы восстановить файлы из копии вместо патчинга.

---

## 💾 Резервные копии и данные

При ошибках **HTTP 429** (исчерпана квота), истёкших токенах или повреждённом кэше часто помогает полный
сброс каталога данных и повторный вход. Патчер всегда создаёт резервную копию перед изменениями, но иногда
нужен ручной сброс.

> Имена каталогов: `Antigravity` для **Antigravity 2.0**, `Antigravity IDE` для **Antigravity IDE**.

### Windows

```powershell
# 1) закройте приложение, затем сделайте копию каталога данных
Move-Item "$env:APPDATA\Antigravity" "$env:USERPROFILE\Desktop\Antigravity-backup"

# 2) запустите приложение, войдите в аккаунт, отправьте одно тестовое сообщение и закройте

# 3) верните только историю чатов
Remove-Item -Recurse -Force "$env:APPDATA\Antigravity\User\globalStorage"
Remove-Item -Recurse -Force "$env:APPDATA\Antigravity\User\workspaceStorage"
Copy-Item -Recurse "$env:USERPROFILE\Desktop\Antigravity-backup\User\globalStorage" "$env:APPDATA\Antigravity\User\"
Copy-Item -Recurse "$env:USERPROFILE\Desktop\Antigravity-backup\User\workspaceStorage" "$env:APPDATA\Antigravity\User\"

# 4) удалите временную копию
Remove-Item -Recurse -Force "$env:USERPROFILE\Desktop\Antigravity-backup"
```

> ⚠️ Не возвращайте `settings.json` — вместе с ним вернутся сломанные настройки и токены.

### macOS

```bash
mv ~/Library/Application\ Support/Antigravity ~/Desktop/Antigravity-backup

# после свежего запуска, входа и одного тестового сообщения:
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

# после свежего запуска, входа и одного тестового сообщения:
rm -rf ~/.config/Antigravity/User/globalStorage
rm -rf ~/.config/Antigravity/User/workspaceStorage
cp -a ~/Antigravity-backup/User/globalStorage ~/.config/Antigravity/User/
cp -a ~/Antigravity-backup/User/workspaceStorage ~/.config/Antigravity/User/

rm -rf ~/Antigravity-backup
```

---

## ⚠️ Частые ошибки

### 1. HTTP 400 — `User location is not supported`

```json
{ "error": { "code": 400, "message": "User location is not supported for the API use.", "status": "FAILED_PRECONDITION" } }
```

- **Причина:** Google определил ограниченный регион, заблокированный IP или «помеченный» отпечаток сессии.
- **Решение:** примените патч (**пункт `1`**). Если не помогло — используйте DNS для обхода блокировок на
  устройстве или роутере и войдите в аккаунт с историей разрешённой страны.

### 2. HTTP 403 — `SUBSCRIPTION_REQUIRED` (#3501)

- **Причина:** проверка лицензии на **серверах Google**. Патчер меняет только локальные файлы и не может
  выдать подписку.
- **Решение:** смените регион аккаунта или используйте подходящий аккаунт; для стабильной работы оформите
  официальный план Google AI.

### 3. HTTP 429 — `RESOURCE_EXHAUSTED`

- **Причина:** исчерпана квота токенов или сессия недействительна.
- **Решение:** сбросьте каталог данных — см. [Резервные копии и данные](#-резервные-копии-и-данные).

### 4. HTTP 500

- **Причина:** внутренняя ошибка серверов Google. Патчер тут ни при чём; подождите несколько минут или
  смените аккаунт.

### 5. `pattern not found` при патчинге

- **Причина:** установленная сборка Antigravity не совпадает с сигнатурами, известными этой версии патчера.
- **Решение:** укажите точный файл через **пункт `11` (указать путь вручную)** либо обновите патчер /
  установите совместимую сборку Antigravity.

### 6. `Operation not permitted` в macOS

1. Выдайте Terminal **Full Disk Access** в `System Settings → Privacy & Security`.
2. Снимите карантин:
   ```bash
   sudo xattr -rd com.apple.quarantine "/Applications/Antigravity.app"
   sudo xattr -rd com.apple.quarantine "/Applications/Antigravity IDE.app"
   ```
3. Патчер сам переподпишет приложение (ad-hoc):
   ```bash
   codesign --force --deep --sign - "/Applications/Antigravity IDE.app"
   ```

### 7. Не удалось проверить обновления

- **Ограничение GitHub:** анонимные запросы к GitHub API ограничены по количеству в час. Сообщение
  «проверка обновлений не удалась — ограничение GitHub» означает именно это; повторите через несколько минут.
- **Сетевая ошибка:** проверьте интернет или VPN-доступ к `api.github.com`.

### 8. Персидский текст отображается зеркально

Терминалы различаются: большинство не применяет алгоритм bidi и требует **предварительно сформированный**
(reshaped) текст; некоторые терминалы уже применяют bidi и переворачивают его повторно. Поэтому при **первом
запуске** программа один раз калибруется: показывает строку-образец и спрашивает, читается ли она, после чего
запоминает выбор.

Можно задать режим вручную:

```bash
# по умолчанию — предварительно сформированный визуальный порядок (CMD / PowerShell / Windows Terminal)
python main.py --rtl visual

# raw — для терминалов, которые сами применяют bidi
python main.py --rtl raw

> В **старом консольном окне (conhost)** Windows может не иметь нужных глифов и показывать пустые квадраты.
> При интерактивном запуске из него программа **автоматически открывается в Windows Terminal** (кроме случаев,
> когда уже запущена с правами администратора или stdin перенаправлен); иначе запустите **Windows Terminal** вручную.

Либо задайте переменную окружения `AG_PATCHER_RTL=visual` / `AG_PATCHER_RTL=raw`. Чтобы пройти калибровку
заново, удалите файл настроек:

```bash
# Windows
Remove-Item "$env:APPDATA\Antigravity-Patcher\ui.json"
# Linux / macOS
rm -f ~/.config/Antigravity-Patcher/ui.json
```

---

## 🔬 Технические детали

### 1. Патч Antigravity IDE

В `main.js` находится условное выражение, его значение жёстко заменяется на `true`; затем очищаются
компилированные кэши (`CachedData` и `Code Cache/js`), чтобы изменённый код выполнился заново.

```javascript
// до
resetIsTierGCPTos(), this.XXX.isGoogleInternal
// после
resetIsTierGCPTos(), true
```

### 2. Патч бинарника Antigravity 2.0 (`language_server`)

Сервис написан на Go. Патчер находит сигнатуру машинного кода и делает `hasValidAuth` всегда равным `true`:

- **x86-64:** `cmp byte ptr [rax + 8], 0` → `mov byte ptr [rax + 8], 1` плюс `nop`.
- **ARM64:** пара чтения/записи флага переписывается через `mov w3, #1`.

### 3. Патч Antigravity CLI (`agy`)

- **x86-64:** ветка ошибки (`failure_builder`), выдающая сообщение о недопустимости аккаунта, становится
  недостижимой.
- **ARM64:** регистры флага заполняются через `mov w1, #1` (и `w2` / `w4` в новых сборках).

### 4. Патч расширения VS Code

1. **Запрет повторной загрузки:** после строки лога о скачивании бинарника в `extension.js` внедряется код,
   который использует локальный бинарник из `~/.gemini/bin`.
2. **Фиксация канала:** `const isChannelChanged = ...` → `const isChannelChanged = false;`.

> Каждый патч проверяет **уникальность** сигнатуры; если сигнатура неоднозначна или отсутствует, патчер
> отказывается угадывать, чтобы не повредить файл.

---

## 🛠 Сборка бинарников

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

## 📁 Структура проекта

```text
Antigravity-Patcher-FA/
├── README.md                  # английский
├── README.fa.md               # персидский
├── README.ru.md               # русский (этот файл)
├── NOTICE.md                  # авторство и список изменений
├── LICENSE                    # GPL-3.0
├── test-agy/                  # автотесты сигнатур бинарников
│   ├── AGENTS.md
│   └── test_cli_releases.py
└── source/                    # исходный код на Python
    ├── main.py                # точка входа
    ├── requirements.txt       # зависимости
    ├── version.txt            # метаданные исполняемого файла
    └── patcher/
        ├── constants.py       # версии, цвета, ссылки
        ├── cli.py             # интерактивное меню и сценарии
        ├── utils/             # рендеринг RTL/консоли, атомарная замена, бэкапы, обновления
        ├── ide/               # патч Antigravity IDE (main.js)
        ├── agy/               # патч Antigravity CLI
        ├── manager/           # патч Antigravity 2.0 (language_server)
        └── vscode/            # патч расширения VS Code
```

---

## 📜 Лицензия и авторство

Проект распространяется под лицензией **GPL-3.0**; полный текст — в [`LICENSE`](LICENSE). Персидская версия
распространяется по той же лицензии с сохранением текста лицензии, уведомлений об авторских правах
оригинальных авторов и списка изменений.

- Оригинальный проект и автор: **[DrAmir0240/Antigravity-Patcher](https://github.com/DrAmir0240/Antigravity-Patcher)** —
  вся заслуга за логику патчей и исходный дизайн принадлежит ему.
- Первоначальная основа: [trustybird/AvenCores-open-antigravity-patcher](https://github.com/trustybird/AvenCores-open-antigravity-patcher)
- Часть подходов основана на [QNIX-Dev/eligibility-antigravity-patcher](https://github.com/QNIX-Dev/eligibility-antigravity-patcher) (MIT)

Персидская версия и её изменения: [khode-mwri](https://github.com/khode-mwri) — см. [`NOTICE.md`](NOTICE.md).

---

## 💬 Поддержка

- **Этот форк:** [Issues](https://github.com/khode-mwri/Antigravity-Patcher-FA/issues)
- **Оригинальный проект:** [DrAmir0240/Antigravity-Patcher](https://github.com/DrAmir0240/Antigravity-Patcher) — Telegram: [@bxiqm](https://t.me/bxiqm)

---

<details>
<summary><b>🔎 Ключевые слова</b></summary>

`Antigravity Patcher` · `Google Antigravity region lock bypass` · `User location is not supported` ·
`FAILED_PRECONDITION 400` · `Unable to verify account eligibility` · `Eligibility check failed agy` ·
`isGoogleInternal bypass` · `language_server patch` · `Antigravity CLI agy` · `google.google-antigravity` ·
`персидская версия Antigravity Patcher` · `патчер Antigravity` · `پچ آنتی‌گراویتی` · `رفع تحریم Antigravity`

</details>
