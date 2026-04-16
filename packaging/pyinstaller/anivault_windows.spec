# -*- mode: python ; coding: utf-8 -*-
"""Windows onedir bundle: same entry as `python -m anivault`."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all

_spec_dir = Path(SPECPATH)
_project_root = _spec_dir.parent.parent
_src = _project_root / "src"
_entry = _src / "anivault" / "__main__.py"
_migrations = _src / "anivault" / "adapters" / "persistence" / "sqlite" / "migrations"

pyside6_datas, pyside6_binaries, pyside6_hiddenimports = collect_all("PySide6")

_datas = list(pyside6_datas)
if _migrations.is_dir():
    _datas.append((str(_migrations), "anivault/adapters/persistence/sqlite/migrations"))

block_cipher = None

a = Analysis(
    [str(_entry)],
    pathex=[str(_src)],
    binaries=list(pyside6_binaries),
    datas=_datas,
    hiddenimports=list(pyside6_hiddenimports),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AniVault",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="AniVault",
)
