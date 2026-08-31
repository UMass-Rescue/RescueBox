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
from PyInstaller.utils.hooks import copy_metadata
# for tensorflow
import os
from pathlib import Path


runtime_venvdir=os.environ['VIRTUAL_ENV'] + "/Lib/site-packages"

hiddenimports = ['fastapi']
hiddenimports += collect_submodules('makefun')
hiddenimports += ['uvicorn', 'modulefinder', 'timeit','jinja2','typer']
hiddenimports += [ 'rb', 'rb-api', 'main', 'rb-api.rb.api.main', 'rb-lib', 'rb-doc-parser', 'rb-file-utils', 'rb-audio-transcription', 'age-and-gender-detection', 'text-summary']

hiddenimports += ['image-summary' , 'test-embeddings' , 'image-embeddings', 'text-embeddings', 'ufdr-mounter', 'case-export']
hiddenimports += ['sentence_transformers']
# for audio
# download and extract ffmpeg.exe to same folder as this file
audio_md_data = f'src/audio-transcription/audio_transcription/app-info.md'


text_summary_data = f'src/text-summary/text_summary/app-info.md'
age_and_gender_detection_data = f'src/age_and_gender_detection/age_and_gender_detection/app-info.md'

hiddenimports += [ 'onnxruntime-gpu', 'opencv-python']

age_and_gender_detection_models_dir = f'src/age_and_gender_detection/age_and_gender_detection/onnx_models'
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

facematch_models= f'face_detection_recognition/onnx_models'
facematch_config= f'face_detection_recognition/config'
src_models_facematch = f'src/face-detection-recognition/{facematch_models}'

src_facematch_config = f'src/face-detection-recognition/{facematch_config}'

src_facematch_db_config = f'{src_facematch_config}/db_config.json'
src_facematch_model_config = f'{src_facematch_config}/model_config.json'

facematch_md_data = f'src/face-detection-recognition/face_detection_recognition/app-info.md'

ufdr_md_data = f'src/ufdr-mounter/ufdr_mounter/ufdr-app-info.md'


image_embeddings_models_path = f'image_embeddings/onnx_models'
src_models_image_embeddings = f'src/image-embeddings/{image_embeddings_models_path}'
src_models_image_embeddings_text_onnx = f'{src_models_image_embeddings}/text.onnx'
src_models_image_embeddings_vision_onnx = f'{src_models_image_embeddings}/vision.onnx'
src_models_image_embeddings_config_json = f'{src_models_image_embeddings}/preprocessor_config.json'

image_similarity_models_path = f'image_similarity/onnx_models'
src_models_image_similarity = f'src/image-similarity/{image_similarity_models_path}'
src_models_image_similarity_onnx = f'{src_models_image_similarity}/siglip2-so400m-patch14-384.onnx'
src_models_image_similarity_config_json = f'{src_models_image_similarity}/preprocessor_config.json'


image_embeddings_data = f'src/image-embeddings/image_embeddings/app-info.md'
text_embeddings_data = f'src/text-embeddings/text_embeddings/app-info.md'
image_summary_data = f'src/image-summary/image_summary/app-info.md'

image_similarity_data = f'src/image-similarity/image_similarity/app-info.md'

# Collect the necessary metadata
transformers_metadata = []
transformers_metadata += copy_metadata('regex')
transformers_metadata += copy_metadata('transformers')
transformers_metadata += copy_metadata('tokenizers')
transformers_metadata += copy_metadata('tqdm')
transformers_metadata += copy_metadata('packaging')
transformers_metadata += copy_metadata('requests')
transformers_metadata += copy_metadata('filelock')

hiddenimports += [
        'pywin32',
        'win32api', 
        'win32com', 
        'pywintypes', 
        'pythoncom', 
        'win32timezone'
    ]
# keep these for facematch

src_model_facematch_resnet50_1 = f'{src_models_facematch}/retinaface-resnet50.onnx'
src_model_facematch_yolov8 = f'{src_models_facematch}/yolov8-face-detection.onnx'
src_model_facematch_facenet512 = f'{src_models_facematch}/facenet512_model.onnx'




# for text-summary
hiddenimports += ['ollama', 'pypdf2', 'requests', 'pdqhash', 'pillow']

hiddenimports += ['llama_index','llama_index.core']
block_cipher = None

#too large
(model_face_detector, age_and_gender_detection_models_dir),
#(model_age_classifier, age_and_gender_detection_models_dir),
#(model_gender_classifier, age_and_gender_detection_models_dir),
#(src_model_bnext_M_dffd, deepfake_detection_models_path),
#(src_model_facecrop, deepfake_detection_models_path),
#(src_model_facematch_facenet512, facematch_models),
#(src_model_facematch_resnet50_1, facematch_models),
#(src_model_facematch_yolov8, facematch_models)
#(src_models_image_embeddings_text_onnx, image_embeddings_models_path),
#(src_models_image_embeddings_vision_onnx, image_embeddings_models_path),
#(src_models_image_embeddings_config_json, image_embeddings_models_path)
#(src_models_image_similarity_onnx, image_similarity_models_path),
#(src_models_image_similarity_config_json, image_similarity_models_path)

a = Analysis(
    ['src/rb-api/rb/api/main.py'],
    pathex=['src/rb-api/rb/api', 'src/rb-lib', 'src/rb-api', 'rescuebox', 'src', '.', 'src/rb-doc-parser', 'src/rb-file-utils', 'src/audio-transcription',
    'src/text-summary', 'src/age_and_gender_detection'],
    binaries=[('ffmpeg.exe', ".")
    ],
    datas=[(audio_md_data, 'audio_transcription'),
        (deepfake_md_data, 'deepfake_detection'), (ufdr_md_data, 'ufdr_mounter'),
        (src_facematch_db_config, facematch_config),(facematch_md_data, 'face_detection_recognition'),
        (image_embeddings_data, 'image_embeddings'), (text_embeddings_data, 'text_embeddings'),
        (image_summary_data, 'image_summary'), (image_similarity_data, 'image_similarity'),
        (age_and_gender_detection_data, 'age_and_gender_detection'),
        (text_summary_data, 'text_summary'),
        (src_facematch_model_config, facematch_config),
        ('src/rb-api/rb/api/static', 'static'), ('src/rb-api/rb/api/templates', 'templates'),
        ('src/doc-parser/doc_parser/chat_config.yml', '.'),
        ('static/favicon.ico', 'static'),
        ] ,
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
    name='rescuebox',
)

# single cmdline
# poetry run pyinstaller --onedir  --paths src/rb-api/rb/api --paths src/rb-lib --paths src/rb-api --paths rescuebox --paths src --paths . --paths src/rb-doc-parser --paths src/rb-file-utils --hidden-import main --hidden-import rb --hidden-import makefun --collect-submodules fastapi --collect-submodules onnxruntime  --clean --name rescuebox src/rb-api/rb/api/main.py
