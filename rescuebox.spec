# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

runtime_venvdir=os.environ['VIRTUAL_ENV'] + "/Lib/site-packages"

# build rescuebox.exe by running : poetry run pyinstaller rescuebox.spec

# for audio plugin
# copy binary dependency ffmpeg.exe from download to this folder from  https://www.ffmpeg.org/download.html as per plugin pre-req doc.

# get data dependencies  : runtime_venvdir + whisper/assets/mel_filters.npz

hiddenimports = ['torch','torchvision', 'functorch',  'modulefinder', 'timeit', 'scipy']
hiddenimports += ['fastapi', 'main', 'rb', 'rb-api', 'rb-lib', 'rb-doc-parser', 'rb-audio-transcription', 'rb-file-utils', 'makefun']
hiddenimports += collect_submodules('fastapi')
hiddenimports += collect_submodules('scipy')

whisper_file = f'{runtime_venvdir}/whisper/assets'
scipy = f'{runtime_venvdir}/scipy/_lib/array_api_compat'

a = Analysis(
    ['src/rb-api/rb/api/main.py'],
    pathex=[ runtime_venvdir, 'rescuebox', 'src', '.', 'src/rb-api/rb/api' , 'src/rb_audio_transcription', 'src/rb-lib', 'src/rb-api', ' src/rb-doc-parser', 'src/rb-file-utils'],
    binaries=[('ffmpeg.exe', ".")],
    datas=[('src/rb-audio-transcription/rb_audio_transcription/app-info.md', 'audio'),
        ('src/rb-api/rb/api/static', 'static'), ('src/rb-api/rb/api/templates', 'templates'),
         ('src/rb-doc-parser/rb_doc_parser/chat_config.yml', '.'),
        ('static/favicon.ico', 'static'),( whisper_file, 'whisper/assets'),
        (scipy, 'scipy/_lib')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)


exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='rescuebox',
    debug=False,
    exclude_binaries=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)


coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='rescuebox')
