# Install syncsub on Windows: fetch ffmpeg + alass, install the package,
# create a SendTo shortcut and a Start Menu shortcut for the drag-and-drop GUI.
#
#   powershell -ExecutionPolicy Bypass -File install.ps1
#
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$BinDir   = Join-Path $env:LOCALAPPDATA "syncsub\bin"
New-Item -ItemType Directory -Force -Path $BinDir | Out-Null

function Info($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }
function Warn($msg) { Write-Host "警告: $msg" -ForegroundColor Yellow }

function Get-ReleaseAsset($repo, $pattern) {
    $api = "https://api.github.com/repos/$repo/releases/latest"
    $rel = Invoke-RestMethod -Uri $api -Headers @{ "User-Agent" = "syncsub-installer" }
    $asset = $rel.assets | Where-Object { $_.name -match $pattern } | Select-Object -First 1
    if (-not $asset) { throw "在 $repo 的最新 release 里找不到匹配 '$pattern' 的资源" }
    return $asset.browser_download_url
}

function Install-Binaries($url, $exeNames) {
    $tmp = Join-Path $env:TEMP ("syncsub_" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Force -Path $tmp | Out-Null
    $zip = Join-Path $tmp "pkg.zip"
    Invoke-WebRequest -Uri $url -OutFile $zip
    Expand-Archive -Path $zip -DestinationPath $tmp -Force
    foreach ($name in $exeNames) {
        $found = Get-ChildItem -Path $tmp -Recurse -Filter $name | Select-Object -First 1
        if ($found) { Copy-Item $found.FullName (Join-Path $BinDir $name) -Force }
    }
    Remove-Item -Recurse -Force $tmp
}

# 1. ffmpeg / ffprobe
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue) -and
    -not (Test-Path (Join-Path $BinDir "ffmpeg.exe"))) {
    Info "下载 ffmpeg / ffprobe ..."
    $url = Get-ReleaseAsset "BtbN/FFmpeg-Builds" "win64-gpl.*\.zip$"
    Install-Binaries $url @("ffmpeg.exe", "ffprobe.exe")
} else { Info "ffmpeg 已存在" }

# 2. alass
if (-not (Get-Command alass -ErrorAction SilentlyContinue) -and
    -not (Get-Command alass-cli -ErrorAction SilentlyContinue) -and
    -not (Test-Path (Join-Path $BinDir "alass.exe"))) {
    Info "下载 alass ..."
    $url = Get-ReleaseAsset "kaegi/alass" "windows.*\.zip$"
    $tmp = Join-Path $env:TEMP ("alass_" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Force -Path $tmp | Out-Null
    $zip = Join-Path $tmp "alass.zip"
    Invoke-WebRequest -Uri $url -OutFile $zip
    Expand-Archive -Path $zip -DestinationPath $tmp -Force
    $exe = Get-ChildItem -Path $tmp -Recurse -Filter "alass*.exe" | Select-Object -First 1
    if (-not $exe) { throw "alass 压缩包内未找到可执行文件" }
    Copy-Item $exe.FullName (Join-Path $BinDir "alass.exe") -Force
    Remove-Item -Recurse -Force $tmp
} else { Info "alass 已存在" }

# 3. add bin dir to the user PATH
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$BinDir*") {
    Info "把 $BinDir 加入用户 PATH ..."
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$BinDir", "User")
}
$env:Path = "$env:Path;$BinDir"

# 4. python package
$py = (Get-Command py -ErrorAction SilentlyContinue) ?? (Get-Command python -ErrorAction SilentlyContinue)
if (-not $py) { throw "未找到 Python，请先从 python.org 安装 Python 3.9+" }
Info "安装 syncsub ..."
& $py.Source -m pip install --user --upgrade "$RepoRoot[gui]"

# 5. shortcuts: GUI in SendTo and Start Menu
$guiTarget = Join-Path $RepoRoot "platform\windows\syncsub-gui.cmd"
$shell = New-Object -ComObject WScript.Shell
function New-Shortcut($lnkPath) {
    $sc = $shell.CreateShortcut($lnkPath)
    $sc.TargetPath = $guiTarget
    $sc.WorkingDirectory = $RepoRoot
    $sc.Save()
}
New-Shortcut (Join-Path ([Environment]::GetFolderPath("SendTo")) "字幕按内嵌时间轴对齐.lnk")
$startMenu = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
New-Shortcut (Join-Path $startMenu "字幕按内嵌时间轴对齐.lnk")

Write-Host ""
Write-Host "安装完成。" -ForegroundColor Green
Write-Host "用法：开始菜单打开「字幕按内嵌时间轴对齐」，把 1 个视频 + 1 个字幕拖进窗口。"
Write-Host "或在资源管理器选中两个文件 → 右键 → 发送到 → 字幕按内嵌时间轴对齐。"
