# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_all


PROJECT_ROOT = Path(SPECPATH).parent.resolve()
ICON_DIR = PROJECT_ROOT / "packaging" / "icons"

datas = [
    (str(PROJECT_ROOT / "VERSION"), "."),
    (str(ICON_DIR / "abisses.png"), "packaging/icons"),
]
binaries = []
hiddenimports = []

# Ces bibliothèques contiennent des données ou binaires natifs que l'analyse
# d'import seule ne retrouve pas toujours (notamment pillow-heif).
for package_name in (
    "pillow_heif",
    "tkintermapview",
    "tzdata",
):
    package_datas, package_binaries, package_hidden = collect_all(package_name)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hidden

a = Analysis(
    [str(PROJECT_ROOT / "gestion_bisses.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Abisses",
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
    icon=str(ICON_DIR / "abisses.ico") if sys.platform.startswith("win") else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Abisses",
)
