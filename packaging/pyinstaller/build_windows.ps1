# Build Windows onedir under repo-root dist/AniVault (requires: pip install -e ".[build]")
$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
$root = (Resolve-Path (Join-Path $here "..\..")).Path
Set-Location $root
python -m PyInstaller --noconfirm (Join-Path $here "anivault_windows.spec")
