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

os.environ['XDG_CACHE_HOME '] = '.'
# for age_and_gender_detection

hiddenimports += ['onnxruntime', 'onnxruntime-gpu', 'nvidia-cudnn-cu12', 'nvidia-cuda-runtime-cu12', 'opencv-python']

age_and_gender_detection_models_dir = f'src/age_and_gender_detection/models'
model_face_detector = f'{age_and_gender_detection_models_dir}/version-RFB-640.onnx'
model_age_classifier =  f'{age_and_gender_detection_models_dir}/age_googlenet.onnx'
model_gender_classifier =  f'{age_and_gender_detection_models_dir}/gender_googlenet.onnx'

# deepfake
hiddenimports += ['numpy', 'pandas', 'pillow']


deepfake_md_data = f'src/deepfake-detection/deepfake_detection/img-app-info.md'

deepfake_detection_models_path = f'deepfake_detection/onnx_models'

src_models_deepfake = f'src/deepfake-detection/{deepfake_detection_models_path}'

# keep this for deepfake + add resnet
src_model_bnext_M_dffd = f'{src_models_deepfake}/bnext_M_dffd_model.onnx'
src_model_facecrop = f'{src_models_deepfake}/face_detector.onnx'


# remove these  
#src_model_bnext_S_coco = f'{src_models_deepfake}/bnext_S_coco_model.onnx'
#src_model_transformer = f'{src_models_deepfake}/transformer_model_deepfake.onnx'
#src_model_resnet50_fakes = f'{src_models_deepfake}/resnet50_fakes.onnx'


facematch_models= f'face_detection_recognition/models'
facematch_config= f'face_detection_recognition/config'
src_models_facematch = f'src/face-detection-recognition/{facematch_models}'

src_facematch_config = f'src/face-detection-recognition/{facematch_config}'

src_facematch_db_config = f'{src_facematch_config}/db_config.json'
src_facematch_model_config = f'{src_facematch_config}/model_config.json'

facematch_md_data = f'src/face-detection-recognition/face_detection_recognition/app-info.md'

ufdr_md_data = f'src/ufdr-mounter/ufdr_mounter/ufdr-app-info.md'

# for chromadb https://github.com/chroma-core/chroma/issues/4092
hiddenimports += [
    'chromadb',
    'chromadb.api',
    'chromadb.api.rust',
    'chromadb.api.fastapi',
    'chromadb.config',
    'chromadb.db',
    'chromadb.db.impl',
    'chromadb.utils',
    'chromadb.telemetry',
    'chromadb.segment',
    'chromadb.segment.impl',
    'chromadb.plugins',
    'chromadb.auth',
    'chromadb.server',
    'chromadb.telemetry.product.posthog',
    'chromadb.api.segment',
    'chromadb.db.impl',
    'chromadb.db.impl.sqlite',
    'chromadb.migrations',
    'chromadb.migrations.embeddings_queue',
    'chromadb.segment.impl.manager',
    'chromadb.segment.impl.manager.local',
    'chromadb.segment.impl.metadata',
    'chromadb.segment.impl.metadata.sqlite',
    'chromadb.segment.impl.vector',
    'chromadb.execution.executor.local',
    'chromadb.quota.simple_quota_enforcer',
    'chromadb.rate_limit.simple_rate_limit',
    'chromadb.api.fastapi',
    'chromadb.utils.embedding_functions',
    'analytics',  # dependency for posthog
]


# keep these for facematch

src_model_facematch_resnet50_1 = f'{src_models_facematch}/retinaface-resnet50.onnx'
src_model_facematch_yolov8 = f'{src_models_facematch}/yolov8-face-detection.onnx'
src_model_facematch_facenet512 = f'{src_models_facematch}/facenet512_model.onnx'

# remove these 
#src_model_facematch_arcface = f'{src_models_facematch}/arcface_model_new.onnx'
#src_model_facematch_resnet50_2 = f'{src_models_facematch}/retinaface_resnet50.onnx'
#src_model_facematch_yolo11m = f'{src_models_facematch}/yolo11m.onnx'
#src_model_facematch_yolov9 = f'{src_models_facematch}/yolov9.onnx'



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
    (src_model_bnext_M_dffd, deepfake_detection_models_path),
    (src_model_facecrop, deepfake_detection_models_path),
    (src_model_facematch_facenet512, facematch_models),
    (src_model_facematch_resnet50_1, facematch_models),
    (src_model_facematch_yolov8, facematch_models),
    
    ],
    datas=[(audio_md_data, 'audio'), ( whisper_data, 'whisper/assets'), ("whisper/base.pt", 'whisper'),
        (deepfake_md_data, 'deepfake_detection'), (ufdr_md_data, 'ufdr_mounter'),
        (src_facematch_db_config, facematch_config),(facematch_md_data, 'face_detection_recognition'),
        (src_facematch_model_config, facematch_config),
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
