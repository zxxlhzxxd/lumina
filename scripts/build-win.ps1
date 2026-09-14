# Build the Windows x64 installer.
# Usage:
#   .\scripts\build-win.ps1
#   .\scripts\build-win.ps1 -Bible D:\bibles\custom.lumina-bible
#   .\scripts\build-win.ps1 -Bible D:\bibles\custom.lumina-bible -BibleTag cuv1919
[CmdletBinding()]
param(
    [string]$Bible = "",
    [string]$BibleTag = ""
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"

if ($Bible -ne "") {
    if (-not (Test-Path -LiteralPath $Bible)) {
        throw "找不到圣经源 $Bible"
    }
    $Bible = (Resolve-Path -LiteralPath $Bible).Path
}

if ($BibleTag -ne "" -and $BibleTag -notmatch '^[A-Za-z0-9._-]+$') {
    throw "圣经版本缩写只能包含字母、数字、点、下划线和连字符"
}

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

function Get-Python {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $cmd = Get-Command py -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    throw "未找到 Python。请安装 Python 3.11+ 并确保 python 在 PATH 中。"
}

$Python = Get-Python
$VenvPython = Join-Path $Backend ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $VenvPython)) {
    & $Python -m venv (Join-Path $Backend ".venv")
    if ($LASTEXITCODE -ne 0) { throw "创建 venv 失败" }
}

& $VenvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip 升级失败" }
& $VenvPython -m pip install -r (Join-Path $Backend "requirements-build.txt")
if ($LASTEXITCODE -ne 0) { throw "安装后端构建依赖失败" }

# npm dist:* runs `python3 scripts/generate_app_icons.py --check`, which is the
# runner Python on Windows CI, not the backend venv.
$IconPython = Get-Command python3 -ErrorAction SilentlyContinue
if ($IconPython) {
    & $IconPython.Source -m pip install -r (Join-Path $Frontend "scripts\requirements-icons.txt")
} else {
    & $Python -m pip install -r (Join-Path $Frontend "scripts\requirements-icons.txt")
}
if ($LASTEXITCODE -ne 0) { throw "安装图标校验依赖失败" }

Push-Location $Backend
try {
    if ($Bible -ne "") {
        & $VenvPython -m app.data.import_bible --source $Bible
    } else {
        & $VenvPython -m app.data.import_bible
    }
    if ($LASTEXITCODE -ne 0) { throw "导入圣经失败" }
    & $VenvPython -m PyInstaller --noconfirm --clean lumina-backend.spec
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller 失败" }
} finally {
    Pop-Location
}

if ($env:WIN_CSC_LINK) {
    $env:CSC_LINK = $env:WIN_CSC_LINK
    $env:CSC_KEY_PASSWORD = $env:WIN_CSC_KEY_PASSWORD
} else {
    $env:CSC_IDENTITY_AUTO_DISCOVERY = "false"
}

Push-Location $Frontend
try {
    if (Test-Path -LiteralPath (Join-Path $Frontend "package-lock.json")) {
        npm ci
    } else {
        npm install
    }
    if ($LASTEXITCODE -ne 0) { throw "npm 安装失败" }
    npm run dist:win
    if ($LASTEXITCODE -ne 0) { throw "electron-builder Windows 打包失败" }
} finally {
    Pop-Location
}

if ($BibleTag -ne "") {
    $releaseDir = Join-Path $Frontend "release"
    Get-ChildItem -LiteralPath $releaseDir -File | Where-Object {
        $_.Name -match '^Lumina-.+-win-x64\.exe(\.blockmap)?$'
    } | ForEach-Object {
        if ($_.Name.EndsWith(".exe.blockmap")) {
            $stem = $_.Name.Substring(0, $_.Name.Length - ".exe.blockmap".Length)
            $destName = "$stem-$BibleTag.exe.blockmap"
        } else {
            $stem = $_.Name.Substring(0, $_.Name.Length - ".exe".Length)
            $destName = "$stem-$BibleTag.exe"
        }
        Rename-Item -LiteralPath $_.FullName -NewName $destName
        Write-Host "安装包已标记圣经版本: $(Join-Path $releaseDir $destName)"
    }
}
