$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".venv")) {
    py -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -e . -r requirements-dev.txt
& .\.venv\Scripts\pyinstaller.exe installer\pyinstaller\iconify.spec --noconfirm
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed with exit code $LASTEXITCODE"
}
Copy-Item -LiteralPath (Join-Path $Root "icon.ico") -Destination (Join-Path $Root "dist\Iconify\icon.ico") -Force

$iscc = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue
if ($iscc) {
    & $iscc.Source installer\windows\iconify.iss
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup build failed with exit code $LASTEXITCODE"
    }
    Write-Host "Windows installer written to dist\installer"
} else {
    Write-Host "PyInstaller executable written to dist\Iconify. Install Inno Setup to build the .exe installer."
}

$zipPath = Join-Path $Root "dist\Iconify-windows.zip"
if (Test-Path $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}
Compress-Archive -Path (Join-Path $Root "dist\Iconify\*") -DestinationPath $zipPath
Write-Host "Windows zip written to dist\Iconify-windows.zip"
