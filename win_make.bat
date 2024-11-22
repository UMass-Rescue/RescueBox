rem pip install fastapi pyinstaller



ModuleNotFoundError: No module named 'rb'
[PYI-16468:ERROR] Failed to execute script 'main' due to unhandled exception!

fix :add --hidden-import rb , --paths src/rb-api

fix : --paths src/rb-doc-parser , add all subfolders

ModuleNotFoundError: No module named 'makefun'
[PYI-16468:ERROR] Failed to execute script 'main' due to unhandled exception!

fix
pip install makefun


pyinstaller --onefile  --add-data src/rb-api/rb/api/static:static --add-data src/rb-api/rb/api/routes/templates:templates --add-data src/rb-api/rb/api/static/favicon.ico:static --paths src/rb-api/rb/api --paths src/rb-lib --paths src/rb-api --paths rescuebox --paths src --paths . --paths src/rb-doc-parser --paths src/rb-file-utils --hidden-import main --hidden-import rb --hidden-import makefun --collect-submodules fastapi  --clean --name rescuebox src/rb-api/rb/api/main.py


ModuleNotFoundError: No module named 'ollama'
fix : pip install ollama

stuck here


pyinstaller --onefile  --add-data src/rb-api/rb/api/static:static --add-data src/rb-api/rb/api/routes/templates:templates --add-data src/rb-api/rb/api/static/favicon.ico:static --paths src/rb-api/rb/api --paths src/rb-lib --paths src/rb-api --paths rescuebox --paths src --paths . --paths src/rb-doc-parser --paths src/rb-file-utils --hidden-import main --hidden-import rb --hidden-import makefun --collect-submodules fastapi  --clean --name rescuebox src/rb-api/rb/api/main.py

importlib.metadata.PackageNotFoundError: No package metadata was found for rescuebox
[PYI-6016:ERROR] Failed to execute script 'main' due to unhandled exception!

fix : pip install . ( to create the metadata ) !!

fix poetry install
poetry run pyinstaller --clean --onefile --add-data 'src/rb-api/rb/api/static:static' --add-data 'src/rb-api/rb/api/routes/templates:templates' --add-data 'src/rb-api/rb/api/static/favicon.ico:static'  --paths /tmp/rb/RescueBox/src/rb-api/rb/api --paths src/rb-api/rb/api --paths src/rb-lib --paths src/rb-api --paths rescuebox --paths src --paths . --paths src/rb-doc-parser --paths src/rb-file-utils  --hidden-import rb --hidden-import makefun --collect-submodules fastapi  --hidden-import main --collect-submodules fastapi --copy-metadata rescuebox --debug=imports --name rescuebox src/rb-api/rb/api/main.py