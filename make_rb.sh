#!/bin/sh
# make an executable rescuebox clu
# add --debug=imports if needed
# install pre reqs like python , python dev , windows wsl env need wslview ( /usr/bin/xdg-open -> /usr/bin/wslview )

poetry run pyinstaller --onefile --add-data 'src/rb-api/rb/api/static:static' --add-data 'src/rb-api/rb/api/routes/templates:templates' --add-data 'src/rb-api/rb/api/static/favicon.ico:static'  --paths /tmp/rb/RescueBox/src/rb-api/rb/api --hidden-import main --collect-submodules fastapi  --name rescuebox src/rb-api/rb/api/main.py

# to get fastapi
poetry install 
# to get metadata
pip install .

poetry run pyinstaller --clean --onefile --add-data 'src/rb-api/rb/api/static:static' --add-data 'src/rb-api/rb/api/routes/templates:templates' --add-data 'src/rb-api/rb/api/static/favicon.ico:static'  --paths /tmp/rb/RescueBox/src/rb-api/rb/api --paths src/rb-api/rb/api --paths src/rb-lib --paths src/rb-api --paths rescuebox --paths src --paths . --paths src/rb-doc-parser --paths src/rb-file-utils  --hidden-import rb --hidden-import makefun --collect-submodules fastapi  --hidden-import main --collect-submodules fastapi --copy-metadata rescuebox  --name rescuebox src/rb-api/rb/api/main.py
