param(
    [string]$VenvPython = ".\.venv\Scripts\python.exe",
    [string]$QgisRoot = "C:\Program Files\QGIS 3.40.1"
)

$ErrorActionPreference = "Stop"

$venvPath = Split-Path -Parent (Split-Path -Parent (Resolve-Path $VenvPython))
$sitePackages = Join-Path $venvPath "Lib\site-packages"
$siteCustomize = Join-Path $sitePackages "sitecustomize.py"
$qgisBin = Join-Path $QgisRoot "bin"
$qgisPython = Join-Path $QgisRoot "apps\Python312"
$qgisDlls = Join-Path $qgisPython "DLLs"

if (!(Test-Path $VenvPython)) {
    throw "Venv Python not found: $VenvPython"
}
if (!(Test-Path $qgisBin)) {
    throw "QGIS bin directory not found: $qgisBin"
}

@"
"""Local venv startup customizations for the QGIS Python runtime."""

from __future__ import annotations

import os
from pathlib import Path


QGIS_DLL_DIRS = [
    Path(r"$qgisBin"),
    Path(r"$qgisPython"),
    Path(r"$qgisDlls"),
]

for dll_dir in QGIS_DLL_DIRS:
    if dll_dir.exists():
        try:
            os.add_dll_directory(str(dll_dir))
        except (AttributeError, OSError):
            pass
"@ | Set-Content -LiteralPath $siteCustomize -Encoding UTF8

& $VenvPython -m pip install "setuptools<81"
& $VenvPython -c "import sqlite3, pkg_resources; print('sqlite3', sqlite3.sqlite_version); print('pkg_resources ok')"
