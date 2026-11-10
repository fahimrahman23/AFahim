# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

playwright_datas = collect_data_files('playwright')
playwright_hidden = collect_submodules('playwright')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    datas=[*playwright_datas],
    hiddenimports=['tkinter', 'tkinter.ttk', 'queue', 'threading', 'dataclasses', 'pathlib', *playwright_hidden],
    excludes=['pytest', 'unittest'],
    console=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MeWeAutoFollow',
    console=False,
    upx=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='MeWeAutoFollow',
)
