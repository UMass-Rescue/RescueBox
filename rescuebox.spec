# -*- mode: python ; coding: utf-8 -*-
'''
#  rescuebox.spec file to build rescuebox fastapi "server" to run rest-api calls.
#  build rescuebox.exe by running : 
      poetry run pyinstaller rescuebox.spec
   after its built .. completed successfully.

  start server : dist\rescuebox\rescuebox.exe
  now start desktop UI and register models
  
'''
from PyInstaller.utils.hooks import collect_submodules

# for tensorflow
import os
from pathlib import Path


runtime_venvdir=os.environ['VIRTUAL_ENV'] + "/Lib/site-packages"

hiddenimports = ['fastapi']
hiddenimports += collect_submodules('makefun')
hiddenimports += ['uvicorn', 'modulefinder', 'timeit','jinja2','typer']
hiddenimports += [ 'rb', 'rb-api', 'main', 'rb-api.rb.api.main', 'rb-lib', 'rb-doc-parser', 'rb-file-utils', 'rb-audio-transcription', 'age-and-gender-detection', 'text-summary']

# for audio
# download and extract ffmpeg.exe to same folder as this file
audio_md_data = f'src/audio-transcription/audio_transcription/app-info.md'
whisper_data = f'{runtime_venvdir}/whisper/assets'

# for age_and_gender_detection

hiddenimports += ['onnxruntime', 'opencv-python']

age_detection_md_data = f'src/age_and_gender_detection/age_and_gender_detection/img-app-info.md'
age_and_gender_detection_models_dir = f'src/age_and_gender_detection/models'
model_face_detector = f'{age_and_gender_detection_models_dir}/version-RFB-640.onnx'
model_age_classifier =  f'{age_and_gender_detection_models_dir}/age_googlenet.onnx'
model_gender_classifier =  f'{age_and_gender_detection_models_dir}/gender_googlenet.onnx'

# for text-summary
hiddenimports += ['ollama', 'pypdf2', 'requests']

block_cipher = None

a = Analysis(
    ['src/rb-api/rb/api/main.py'],
    pathex=['src/rb-api/rb/api', 'src/rb-lib', 'src/rb-api', 'rescuebox', 'src', '.', 'src/rb-doc-parser', 'src/rb-file-utils', 'src/audio-transcription',
    'src/text-summary', 'src/age_and_gender_detection'],
    binaries=[('ffmpeg.exe', "."),
    (model_face_detector, age_and_gender_detection_models_dir),
    (model_age_classifier, age_and_gender_detection_models_dir),
    (model_gender_classifier, age_and_gender_detection_models_dir),
    ],
    datas=[(audio_md_data, 'audio'), ( whisper_data, 'whisper/assets'),
        (age_detection_md_data, 'age_and_gender_detection'),
        ('src/rb-api/rb/api/static', 'static'), ('src/rb-api/rb/api/templates', 'templates'),
        ('src/doc-parser/doc_parser/chat_config.yml', '.'),
        ('static/favicon.ico', 'static'),
        ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='rescuebox',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
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
    upx=True,
    upx_exclude=[],
    name='rescuebox',
)

# single cmdline
# poetry run pyinstaller --onedir  --paths src/rb-api/rb/api --paths src/rb-lib --paths src/rb-api --paths rescuebox --paths src --paths . --paths src/rb-doc-parser --paths src/rb-file-utils --hidden-import main --hidden-import rb --hidden-import makefun --collect-submodules fastapi --collect-submodules onnxruntime  --clean --name rescuebox src/rb-api/rb/api/main.py
