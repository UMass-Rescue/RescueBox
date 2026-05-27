# -*- mode: python ; coding: utf-8 -*-
'''
#  frontend.spec file to build rescuebox fastapi "ui" .
#  build rescuebox.exe by running : 
      poetry run pyinstaller rescuebox.spec
   after its built .. completed successfully.

  start server : dist\rescuebox\frontend.exe
  now start desktop UI and register models
  
'''
from PyInstaller.utils.hooks import collect_submodules

# for tensorflow
import os
from pathlib import Path

# --- ADD THIS TO THE TOP OF YOUR SPEC FILE ---
import dataclasses
try:
    # If the attribute is missing, force it so the hook doesn't crash
    if not hasattr(dataclasses, "__version__"):
        dataclasses.__version__ = "0.8" 
except Exception:
    pass
# ---------------------------------------------

runtime_venvdir=os.environ['VIRTUAL_ENV'] + "/Lib/site-packages"

hiddenimports = ['fastapi' , 'nicegui']

os.environ['XDG_CACHE_HOME '] = '.'

# for text-summary
hiddenimports += ['ollama', 'httpx']

block_cipher = None

a = Analysis(
    ['frontend/main.py'],
    pathex=['.', 'frontend'],
    binaries=[],
    datas=[('frontend/icons/rb.webp', 'icons'),],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    excludes=['web', 'torch'],
    runtime_hooks=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='frontend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    excludes=['web', 'torch'],
    target_arch=None,
    codesign_identity=None,
    icon='./src-tauri/icons/icon.ico',
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='frontend',
)

# single cmdline
# poetry run pyinstaller --onedir  --paths frontend --paths . --hidden-import makefun --collect-submodules fastapi --name rescuebox frontend/main.py
