# Build the Windows x64 installer.
# Usage:
#   .\scripts\build-win.ps1
#   .\scripts\build-win.ps1 -Bible D:\bibles\custom.lumina-bible
[CmdletBinding()]
param(
    [string]$Bible = ""
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
