<#
.SYNOPSIS
    Capture a real-terminal screenshot of the Antigravity Patcher Persian UI,
    in both a legacy console window (conhost.exe) and Windows Terminal (wt.exe).

.DESCRIPTION
    For every selected terminal host the script:

      1. writes a small launcher .cmd that sets a unique window title
         (AGVERIFY by default), SKIP_ELEVATION=1 and the RTL mode, then runs
         `python main.py` with `echo 0|` on stdin so the app renders its menu
         once and exits cleanly;
      2. starts the app inside that terminal host:
           - legacy console : conhost.exe cmd.exe /k <launcher.cmd>
           - Windows Terminal: wt.exe -w -1 ... cmd.exe /k <launcher.cmd>
      3. waits for the window (EnumWindows + exact title match) and for the
         launcher's status file (application exit code), then calls
         ShowWindow/SetForegroundWindow, reads GetWindowRect
         (DwmGetWindowAttribute extended frame when available) and copies just
         that rectangle into a PNG with System.Drawing;
      4. validates the PNG (size, distinct colours, non-black pixels) and
         writes evidence/<name>.png plus a JSON report;
      5. cleans up: closes the window (PostMessage WM_CLOSE) and kills the
         launcher's process tree; Windows Terminal itself is never killed.

    The screenshots are saved next to each other in the workspace evidence
    folder (default: <workspace>/evidence/app_conhost.png and app_wt.png).

.PARAMETER ProjectRoot
    Project root containing source\main.py. Defaults to the parent of this
    script's folder (...\Antigravity-Patcher-FA\tools\..).

.PARAMETER EvidenceDir
    Folder for the PNGs and JSON report. Defaults to <workspace>\evidence,
    i.e. the parent folder of ProjectRoot plus \evidence.

.PARAMETER Title
    Window title used to find the window. Keep it unique to this test.

.PARAMETER RtlMode
    auto | visual | raw. Ignored when -NoRtlEnv is used. Defaults to visual.

.PARAMETER Hosts
    both | conhost | wt. Defaults to both.

.PARAMETER MenuChoice
    Text fed through the `echo N|` stdin pipe (default 0 = exit).

.PARAMETER TimeoutSec
    How long to wait for the window to appear and the app to exit.

.PARAMETER Width / Height
    Optional window resize before capture (0 = keep the terminal's own size).

.PARAMETER Suffix
    Appended to the PNG/JSON file names, e.g. -Suffix _raw -> app_wt_raw.png.

.PARAMETER Exe
    Optional path to a built .exe. When given, the launcher runs that executable
    instead of `python main.py`, so the frozen build can be screenshot-tested too.

.PARAMETER KeepWindows
    Do not close the windows after capture (debugging only).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File tools\screenshot_ui.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File tools\screenshot_ui.ps1 -Hosts wt -RtlMode raw -Suffix _raw
#>
#Requires -Version 5.1
[CmdletBinding()]
param(
    [string]$ProjectRoot,
    [string]$EvidenceDir,
    [string]$Title = 'AGVERIFY',
    [ValidateSet('auto', 'visual', 'raw')][string]$RtlMode = 'visual',
    [ValidateSet('both', 'conhost', 'wt')][string]$Hosts = 'both',
    [string]$MenuChoice = '0',
    [int]$TimeoutSec = 90,
    [int]$Width = 0,
    [int]$Height = 0,
    [string]$Suffix = '',
    [string]$Exe,
    [switch]$KeepWindows,
    [switch]$NoRtlEnv
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

# ---------------------------------------------------------------- paths ----
if (-not $ProjectRoot) { $ProjectRoot = Split-Path -Parent $PSScriptRoot }
$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$SourceDir = Join-Path $ProjectRoot 'source'
if (-not (Test-Path -LiteralPath (Join-Path $SourceDir 'main.py'))) {
    throw "source\main.py not found under '$ProjectRoot'"
}
if (-not $EvidenceDir) { $EvidenceDir = Join-Path (Split-Path -Parent $ProjectRoot) 'evidence' }
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null
$EvidenceDir = (Resolve-Path -LiteralPath $EvidenceDir).Path

$RuntimeDir = Join-Path $ProjectRoot 'tools\_runtime\screenshot'
New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null
$AppDataDir = Join-Path $RuntimeDir 'appdata'
New-Item -ItemType Directory -Force -Path $AppDataDir | Out-Null

# Optional: screenshot a frozen build instead of `python main.py`.
$ExePath = $null
if ($Exe) {
    $candidate = $Exe
    if (-not (Test-Path -LiteralPath $candidate)) {
        $candidate = Join-Path $ProjectRoot $Exe
    }
    if (-not (Test-Path -LiteralPath $candidate)) {
        throw "exe not found: $Exe"
    }
    $ExePath = (Resolve-Path -LiteralPath $candidate).Path
}

$LauncherPath = Join-Path $RuntimeDir 'ag_verify_launch.cmd'
$LauncherName = Split-Path -Leaf $LauncherPath
$StatusFile = Join-Path $RuntimeDir 'app_exit.txt'
$DoneFlag = Join-Path $RuntimeDir 'app_done.flag'
$ReportPath = Join-Path $EvidenceDir ('screenshot_report' + $Suffix + '.json')

# ------------------------------------------------------------- helpers ----
function Resolve-Python {
    $candidates = @()
    $cmd = Get-Command python.exe -ErrorAction SilentlyContinue
    if (-not $cmd) { $cmd = Get-Command python -ErrorAction SilentlyContinue }
    if ($cmd) { $candidates += $cmd.Source }
    $candidates += (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe')
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            # Reject the Microsoft Store 0-byte execution alias.
            if ((Get-Item -LiteralPath $candidate).Length -gt 0) { return $candidate }
        }
    }
    throw 'python.exe not found (install Python 3.x or make it available on PATH)'
}

if (-not ('AGShotWin' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Text;
using System.Runtime.InteropServices;
public static class AGShotWin {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetWindowTextW(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetClassNameW(IntPtr hWnd, StringBuilder lpClassName, int nMaxCount);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool IsWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr hWnd, int x, int y, int w, int h, bool repaint);
    [DllImport("user32.dll")] public static extern bool PostMessageW(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern IntPtr SetActiveWindow(IntPtr hWnd);
    [DllImport("kernel32.dll")] public static extern uint GetCurrentThreadId();
    [DllImport("user32.dll")] public static extern bool AttachThreadInput(uint idAttach, uint idAttachTo, bool fAttach);
    [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int x, int y, int cx, int cy, uint uFlags);
    [DllImport("user32.dll")] public static extern IntPtr WindowFromPoint(POINT pt);
    [DllImport("user32.dll")] public static extern IntPtr GetAncestor(IntPtr hWnd, uint gaFlags);
    [DllImport("user32.dll")] public static extern bool SetProcessDpiAwarenessContext(IntPtr value);
    [DllImport("dwmapi.dll")] public static extern int DwmGetWindowAttribute(IntPtr hwnd, int dwAttribute, out RECT pvAttribute, int cbAttribute);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
    [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X; public int Y; }
}
'@
}

# Best effort: make this process per-monitor DPI aware so GetWindowRect and
# CopyFromScreen agree on physical pixels on scaled displays.
try { [void][AGShotWin]::SetProcessDpiAwarenessContext([IntPtr](-4)) } catch { }

Add-Type -AssemblyName System.Drawing

$script:WindowHits = @()

function Find-WindowByTitle {
    param([string]$WantTitle)
    $script:WindowHits = @()
    $callback = [AGShotWin+EnumWindowsProc] {
        param($hWnd, $lParam)
        if ([AGShotWin]::IsWindowVisible($hWnd)) {
            $text = New-Object System.Text.StringBuilder 512
            [void][AGShotWin]::GetWindowTextW($hWnd, $text, 512)
            if ($text.ToString() -eq $WantTitle) {
                $class = New-Object System.Text.StringBuilder 256
                [void][AGShotWin]::GetClassNameW($hWnd, $class, 256)
                $procId = 0
                [void][AGShotWin]::GetWindowThreadProcessId($hWnd, [ref]$procId)
                $script:WindowHits += [pscustomobject]@{
                    Handle = $hWnd
                    Title = $text.ToString()
                    Class = $class.ToString()
                    Pid = [int]$procId
                }
            }
        }
        return $true
    }
    [void][AGShotWin]::EnumWindows($callback, [IntPtr]::Zero)
    return @($script:WindowHits)
}

function Get-WindowRectActual {
    param([IntPtr]$Handle)
    $rect = New-Object AGShotWin+RECT
    $dwm = -1
    try { $dwm = [AGShotWin]::DwmGetWindowAttribute($Handle, 9, [ref]$rect, [System.Runtime.InteropServices.Marshal]::SizeOf([type][AGShotWin+RECT])) } catch { $dwm = -1 }
    $source = 'GetWindowRect'
    if ($dwm -ne 0) {
        $rect = New-Object AGShotWin+RECT
        [void][AGShotWin]::GetWindowRect($Handle, [ref]$rect)
    } else {
        $source = 'DwmGetWindowAttribute(EXTENDED_FRAME_BOUNDS)'
    }
    return [pscustomobject]@{
        Left = [int]$rect.Left; Top = [int]$rect.Top
        Right = [int]$rect.Right; Bottom = [int]$rect.Bottom
        Width = [int]($rect.Right - $rect.Left)
        Height = [int]($rect.Bottom - $rect.Top)
        Source = $source
    }
}

function Get-ImageStats {
    param([System.Drawing.Bitmap]$Bitmap)
    $sampled = 0; $lit = 0
    $colours = New-Object 'System.Collections.Generic.HashSet[int]'
    $stepX = [Math]::Max(1, [int]($Bitmap.Width / 300))
    $stepY = [Math]::Max(1, [int]($Bitmap.Height / 200))
    for ($y = 0; $y -lt $Bitmap.Height; $y += $stepY) {
        for ($x = 0; $x -lt $Bitmap.Width; $x += $stepX) {
            $c = $Bitmap.GetPixel($x, $y)
            $sampled++
            if (($c.R + $c.G + $c.B) -gt 24) { $lit++ }
            [void]$colours.Add($c.ToArgb())
        }
    }
    return [pscustomobject]@{
        SampledPixels = $sampled
        NonBlackRatio = if ($sampled -gt 0) { [Math]::Round($lit / $sampled, 4) } else { 0 }
        DistinctColours = $colours.Count
    }
}

function Force-WindowForeground {
    param([IntPtr]$Handle)
    # SetForegroundWindow is refused when the calling process does not own the
    # foreground window; attaching to the foreground thread's input queue is the
    # standard workaround. Windows Terminal especially tends to open behind other
    # windows when started from a background process like this test harness.
    $foreground = [AGShotWin]::GetForegroundWindow()
    if ($foreground -eq $Handle) { return $true }
    $targetThread = 0
    $targetPid = 0
    $targetThread = [AGShotWin]::GetWindowThreadProcessId($Handle, [ref]$targetPid)
    $foregroundThread = 0
    $foregroundPid = 0
    if ($foreground -ne [IntPtr]::Zero) {
        $foregroundThread = [AGShotWin]::GetWindowThreadProcessId($foreground, [ref]$foregroundPid)
    }
    $currentThread = [AGShotWin]::GetCurrentThreadId()
    [void][AGShotWin]::ShowWindow($Handle, 9)   # SW_RESTORE
    try {
        if ($foregroundThread -ne 0 -and $foregroundThread -ne $currentThread) {
            [void][AGShotWin]::AttachThreadInput($currentThread, $foregroundThread, $true)
        }
        [void][AGShotWin]::BringWindowToTop($Handle)
        [void][AGShotWin]::SetForegroundWindow($Handle)
        [void][AGShotWin]::SetActiveWindow($Handle)
    } finally {
        if ($foregroundThread -ne 0 -and $foregroundThread -ne $currentThread) {
            [void][AGShotWin]::AttachThreadInput($currentThread, $foregroundThread, $false)
        }
    }
    Start-Sleep -Milliseconds 350
    if ([AGShotWin]::GetForegroundWindow() -eq $Handle) { return $true }

    # Last resort: briefly make the test window top-most, then drop the flag so
    # the user's window is not left pinned above everything.
    $HWND_TOPMOST = [IntPtr](-1)
    $HWND_NOTOPMOST = [IntPtr](-2)
    $SWP_NOSIZE = 0x0001
    $SWP_NOMOVE = 0x0002
    [void][AGShotWin]::SetWindowPos($Handle, $HWND_TOPMOST, 0, 0, 0, 0, ($SWP_NOSIZE -bor $SWP_NOMOVE))
    Start-Sleep -Milliseconds 350
    $ok = ([AGShotWin]::GetForegroundWindow() -eq $Handle)
    [void][AGShotWin]::SetWindowPos($Handle, $HWND_NOTOPMOST, 0, 0, 0, 0, ($SWP_NOSIZE -bor $SWP_NOMOVE))
    return $ok
}

function Test-WindowUnobstructed {
    param([IntPtr]$Handle, $Rect)
    $point = New-Object AGShotWin+POINT
    $point.X = [int](($Rect.Left + $Rect.Right) / 2)
    $point.Y = [int]($Rect.Top + 20)
    $atPoint = [AGShotWin]::WindowFromPoint($point)
    $root = [AGShotWin]::GetAncestor($atPoint, 2)  # GA_ROOT
    return ($atPoint -eq $Handle -or $root -eq $Handle)
}

function Save-WindowPng {
    param([IntPtr]$Handle, [string]$Path)
    $foregroundOk = Force-WindowForeground -Handle $Handle
    Start-Sleep -Milliseconds 500

    $rect = Get-WindowRectActual -Handle $Handle
    if ($rect.Width -lt 100 -or $rect.Height -lt 80) {
        throw "implausible window rect $($rect.Width)x$($rect.Height)"
    }
    $unobstructed = Test-WindowUnobstructed -Handle $Handle -Rect $rect
    $bitmap = New-Object System.Drawing.Bitmap($rect.Width, $rect.Height)
    try {
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        try {
            $graphics.CopyFromScreen($rect.Left, $rect.Top, 0, 0, $bitmap.Size)
        } finally { $graphics.Dispose() }
        $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
        $stats = Get-ImageStats -Bitmap $bitmap
    } finally { $bitmap.Dispose() }
    return [pscustomobject]@{
        Rect = $rect
        Stats = $stats
        Foreground = $foregroundOk
        Unobstructed = $unobstructed
    }
}

function Stop-ProcessTree {
    param([int]$TargetPid)
    if (-not $TargetPid) { return }
    # cmd.exe swallows taskkill's "process not found" stderr; a raw native call
    # would trip $ErrorActionPreference = 'Stop' during cleanup.
    $null = & cmd.exe /c "taskkill /PID $TargetPid /T /F >nul 2>&1"
}

function Stop-LauncherProcesses {
    param([string]$LauncherLeafName)
    $killed = @()
    try {
        $procs = @(Get-CimInstance Win32_Process -ErrorAction Stop |
            Where-Object { $_.CommandLine -and $_.CommandLine -like "*$LauncherLeafName*" })
    } catch { $procs = @() }
    foreach ($proc in $procs) {
        if ($proc.ProcessId -eq $PID) { continue }
        if ($proc.Name -eq 'powershell.exe' -or $proc.Name -eq 'pwsh.exe') { continue }
        $killed += [int]$proc.ProcessId
        Stop-ProcessTree -TargetPid ([int]$proc.ProcessId)
    }
    return @($killed)
}

function Close-TestWindow {
    param([string]$WantTitle)
    $closed = @()
    $wins = @(Find-WindowByTitle -WantTitle $WantTitle)
    foreach ($win in $wins) {
        [void][AGShotWin]::PostMessageW($win.Handle, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero)  # WM_CLOSE
        $closed += [pscustomobject]@{ Title = $win.Title; Class = $win.Class; Pid = $win.Pid; Via = 'WM_CLOSE' }
    }
    return @($closed)
}

function Stop-WindowOwnerTree {
    param([string]$WantTitle)
    $wins = @(Find-WindowByTitle -WantTitle $WantTitle)
    $killed = @()
    foreach ($win in $wins) {
        # Windows Terminal (CASCADIA) must not be killed: only its tab contents.
        if ($win.Class -eq 'ConsoleWindowClass') {
            Stop-ProcessTree -TargetPid ([int]$win.Pid)
            $killed += [int]$win.Pid
        }
    }
    return @($killed)
}

# --------------------------------------------------------------- launcher ----
$PythonExe = $null
if (-not $ExePath) { $PythonExe = Resolve-Python }
if ($ExePath) { $RunnerLabel = "exe: $ExePath" } else { $RunnerLabel = "python: $PythonExe main.py" }
Write-Host "screenshot_ui: runner = $RunnerLabel"
Write-Host "screenshot_ui: project = $ProjectRoot"
Write-Host "screenshot_ui: evidence = $EvidenceDir"

$launcherLines = @(
    '@echo off',
    "title $Title",
    "cd /d `"$SourceDir`"",
    'set "SKIP_ELEVATION=1"'
)
# NOTE: %APPDATA% is intentionally NOT overridden here. This launcher runs the
# app from source with the system Python, whose user site-packages (and hence
# third-party deps such as `packaging`) live under %APPDATA%\Python. The RTL
# mode is pinned through AG_PATCHER_RTL, so the app never needs the
# %APPDATA%\Antigravity-Patcher\ui.json preference file in this test anyway.
if (-not $NoRtlEnv -and $RtlMode -ne 'auto') {
    $launcherLines += "set `"AG_PATCHER_RTL=$RtlMode`""
}
if ($ExePath) {
    $launcherLines += "echo $MenuChoice| `"$ExePath`""
} else {
    $launcherLines += "echo $MenuChoice| `"$PythonExe`" main.py"
}
$launcherLines += @(
    'set "RC=%ERRORLEVEL%"',
    'echo.',
    'echo   [harness] application exited with code %RC%',
    "> `"$StatusFile`" echo EXIT=%RC%",
    "> `"$DoneFlag`" echo done"
)
# Batch files must be CRLF + ASCII for cmd.exe.
Set-Content -LiteralPath $LauncherPath -Value $launcherLines -Encoding ASCII
Write-Host "screenshot_ui: launcher = $LauncherPath"

# Hash the source tree so the report states exactly which revision was shown.
$sourceHashes = @()
$newestSource = Get-ChildItem -Recurse -File -LiteralPath $SourceDir |
    Where-Object { $_.FullName -notmatch '__pycache__' } | Sort-Object FullName
foreach ($file in $newestSource) {
    $relative = $file.FullName.Substring($SourceDir.Length + 1).Replace('\', '/')
    $fileHash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    $sourceHashes += ($relative + '|' + $fileHash)
}
$treeText = ($sourceHashes -join "`n")
$sha256 = [System.Security.Cryptography.SHA256]::Create()
try {
    $treeBytes = [System.Text.Encoding]::UTF8.GetBytes($treeText)
    $sourceTreeHash = (($sha256.ComputeHash($treeBytes) | ForEach-Object { $_.ToString('x2') }) -join '')
} finally { $sha256.Dispose() }
$newestSourceTime = ($newestSource | Sort-Object LastWriteTime -Descending |
    Select-Object -First 1).LastWriteTime

$script:Report = [ordered]@{
    tool          = 'screenshot_ui'
    started_at    = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    project_root  = $ProjectRoot
    evidence_dir  = $EvidenceDir
    runner        = $RunnerLabel
    exe           = $ExePath
    python        = $PythonExe
    source_tree_sha256 = $sourceTreeHash
    source_newest_mtime = $newestSourceTime.ToString('yyyy-MM-dd HH:mm:ss')
    launcher      = $LauncherPath
    title         = $Title
    rtl_mode      = $(if ($NoRtlEnv) { 'auto(no env)' } else { $RtlMode })
    menu_choice   = $MenuChoice
    captures      = @()
    cleanup       = @()
    result        = 'FAIL'
}

function Invoke-Capture {
    param(
        [ValidateSet('conhost', 'wt')][string]$HostName,
        [string]$ExpectedClass,
        [string]$PngPath
    )
    $capture = [ordered]@{
        host = $HostName
        expected_window_class = $ExpectedClass
        png = $PngPath
        launched_at = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
        window = $null
        app_exit_code = $null
        image = $null
        result = 'FAIL'
        error = $null
    }

    Remove-Item -LiteralPath $StatusFile, $DoneFlag -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $PngPath -Force -ErrorAction SilentlyContinue

    try {
        switch ($HostName) {
            'conhost' {
                $conhostExe = Join-Path $env:SystemRoot 'System32\conhost.exe'
                if (-not (Test-Path -LiteralPath $conhostExe)) { throw 'conhost.exe not found' }
                Write-Host "[conhost] starting legacy console window ..."
                Start-Process -FilePath $conhostExe `
                    -ArgumentList ("cmd.exe /k $LauncherName") `
                    -WorkingDirectory $RuntimeDir | Out-Null
            }
            'wt' {
                $wt = Get-Command wt.exe -ErrorAction SilentlyContinue
                if (-not $wt) { throw 'Windows Terminal (wt.exe) is not installed' }
                Write-Host "[wt] starting Windows Terminal window ..."
                $wtArgs = "-w -1 -d `"$RuntimeDir`" cmd.exe /k `"$LauncherPath`""
                Start-Process -FilePath $wt.Source -ArgumentList $wtArgs -WorkingDirectory $RuntimeDir | Out-Null
            }
        }

        # --- wait for window + application exit --------------------------------
        $deadline = (Get-Date).AddSeconds($TimeoutSec)
        $window = $null
        $appExited = $false
        while ((Get-Date) -lt $deadline) {
            Start-Sleep -Milliseconds 400
            $hits = @(Find-WindowByTitle -WantTitle $Title |
                Where-Object { $_.Class -eq $ExpectedClass })
            if ($hits.Count -gt 0) { $window = $hits[0] }
            if ((Test-Path -LiteralPath $DoneFlag) -and (Test-Path -LiteralPath $StatusFile)) { $appExited = $true }
            if ($window -and $appExited) { break }
        }
        if (-not $window) {
            $allHits = @(Find-WindowByTitle -WantTitle $Title)
            $classes = ($allHits | ForEach-Object { $_.Class }) -join ', '
            throw ("window titled '$Title' with class '$ExpectedClass' did not appear " +
                   "within ${TimeoutSec}s (windows with that title: [$classes])")
        }
        if (-not $appExited) {
            Write-Warning "[$HostName] application exit marker not found within ${TimeoutSec}s; capturing anyway"
        } else {
            $statusText = Get-Content -LiteralPath $StatusFile -Raw -ErrorAction SilentlyContinue
            if ($statusText -match 'EXIT=(-?\d+)') {
                $capture.app_exit_code = [int]$Matches[1]
            }
        }

        $capture.window = [ordered]@{
            handle = "$($window.Handle)"
            class = $window.Class
            title = $window.Title
            pid = $window.Pid
            process = (Get-Process -Id $window.Pid -ErrorAction SilentlyContinue).ProcessName
        }

        # --- optional resize, then capture exactly the window ------------------
        if ($Width -gt 0 -and $Height -gt 0) {
            # Anchor the resized window near the top-left corner so a tall window
            # still fits on the desktop (and the PNG is not partly off-screen).
            [void][AGShotWin]::MoveWindow($window.Handle, 30, 20, $Width, $Height, $true)
            Start-Sleep -Milliseconds 800
        }
        $shot = $null
        for ($attempt = 1; $attempt -le 3; $attempt++) {
            $shot = Save-WindowPng -Handle $window.Handle -Path $PngPath
            if ($shot.Foreground -and $shot.Unobstructed) { break }
            Write-Warning ("[$HostName] capture attempt $attempt was not a clear foreground window " +
                           "(foreground=$($shot.Foreground), unobstructed=$($shot.Unobstructed)); retrying")
            Start-Sleep -Milliseconds 900
        }
        $capture.image = [ordered]@{
            width = $shot.Rect.Width
            height = $shot.Rect.Height
            rect_left = $shot.Rect.Left
            rect_top = $shot.Rect.Top
            rect_source = $shot.Rect.Source
            window_foreground = $shot.Foreground
            window_unobstructed = $shot.Unobstructed
            non_black_ratio = $shot.Stats.NonBlackRatio
            distinct_colours = $shot.Stats.DistinctColours
            png_bytes = (Get-Item -LiteralPath $PngPath).Length
        }
        $pngOk = ($capture.image.png_bytes -gt 4000) -and
                 ($capture.image.non_black_ratio -gt 0.005) -and
                 ($capture.image.distinct_colours -gt 8)
        if ($pngOk) {
            $capture.result = 'PASS'
        } else {
            $capture.result = 'FAIL'
            $capture.error = 'captured PNG looks blank or nearly monochrome'
        }
        if (-not ($shot.Foreground -and $shot.Unobstructed)) {
            $capture.error = "window was not clearly in the foreground while capturing " +
                             "(foreground=$($shot.Foreground), unobstructed=$($shot.Unobstructed))"
            $capture.result = 'FAIL'
        }
        if ($capture.app_exit_code -ne $null -and $capture.app_exit_code -ne 0) {
            $capture.error = "application exit code was $($capture.app_exit_code) (expected 0)"
        }
    } catch {
        $capture.result = 'FAIL'
        $capture.error = $_.Exception.Message
        Write-Warning "[$HostName] $($_.Exception.Message)"
    } finally {
        if (-not $KeepWindows) {
            Write-Host "[$HostName] cleaning up window and child processes ..."
            $killed = @(Stop-LauncherProcesses -LauncherLeafName $LauncherName)
            $closed = @(Close-TestWindow -WantTitle $Title)
            Start-Sleep -Milliseconds 900
            $remaining = @(Find-WindowByTitle -WantTitle $Title | Where-Object { $_.Class -eq $ExpectedClass })
            if ($remaining.Count -gt 0) {
                $killed += @(Stop-WindowOwnerTree -WantTitle $Title)
                Start-Sleep -Milliseconds 700
                $remaining = @(Find-WindowByTitle -WantTitle $Title | Where-Object { $_.Class -eq $ExpectedClass })
            }
            $script:Report.cleanup += [ordered]@{
                host = $HostName
                killed_pids = @($killed)
                closed_windows = @($closed)
                windows_remaining = $remaining.Count
            }
            if ($remaining.Count -gt 0) {
                Write-Warning "[$HostName] $($remaining.Count) window(s) still open"
            }
        }
    }
    return $capture
}

# --------------------------------------------------------------- run -------
$hostsToRun = switch ($Hosts) {
    'conhost' { @('conhost') }
    'wt'      { @('wt') }
    default   { @('conhost', 'wt') }
}

try {
    if ($hostsToRun -contains 'conhost') {
        $png = Join-Path $EvidenceDir ('app_conhost' + $Suffix + '.png')
        $script:Report.captures += Invoke-Capture -HostName 'conhost' -ExpectedClass 'ConsoleWindowClass' -PngPath $png
    }
    if ($hostsToRun -contains 'wt') {
        $png = Join-Path $EvidenceDir ('app_wt' + $Suffix + '.png')
        $script:Report.captures += Invoke-Capture -HostName 'wt' -ExpectedClass 'CASCADIA_HOSTING_WINDOW_CLASS' -PngPath $png
    }
} finally {
    if (-not $KeepWindows) {
        # final sweep for leftovers of *this* launcher only
        $leftovers = @(Stop-LauncherProcesses -LauncherLeafName $LauncherName)
        if ($leftovers.Count -gt 0) {
            $script:Report.cleanup += [ordered]@{ host = 'final-sweep'; killed_pids = @($leftovers) }
        }
    }
    $failed = @($script:Report.captures | Where-Object { $_.result -ne 'PASS' })
    $script:Report.result = if ($script:Report.captures.Count -gt 0 -and $failed.Count -eq 0) { 'PASS' } else { 'FAIL' }
    $script:Report.finished_at = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    $json = $script:Report | ConvertTo-Json -Depth 8
    # UTF-8 without BOM: the JSON report is also read by Python tooling.
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($ReportPath, $json, $utf8NoBom)
}

# --------------------------------------------------------------- report ----
Write-Host ''
Write-Host '================ screenshot_ui summary ================'
foreach ($capture in $script:Report.captures) {
    Write-Host ("[{0}] {1}" -f $capture.host, $capture.result)
    if ($capture.png) { Write-Host ("      png    : {0}" -f $capture.png) }
    if ($capture.window) {
        Write-Host ("      window : class={0} pid={1} ({2})" -f $capture.window.class, $capture.window.pid, $capture.window.process)
    }
    if ($capture.image) {
        Write-Host ("      image  : {0}x{1}px, non-black={2}, colours={3}, bytes={4}" -f `
            $capture.image.width, $capture.image.height, $capture.image.non_black_ratio,
            $capture.image.distinct_colours, $capture.image.png_bytes)
    }
    if ($null -ne $capture.app_exit_code) { Write-Host ("      app exit code: {0}" -f $capture.app_exit_code) }
    if ($capture.error) { Write-Host ("      note   : {0}" -f $capture.error) }
}
Write-Host ("report: {0}" -f $ReportPath)
Write-Host ("RESULT: {0}" -f $script:Report.result)
Write-Host '======================================================'

if ($script:Report.result -ne 'PASS') { exit 1 }
exit 0
