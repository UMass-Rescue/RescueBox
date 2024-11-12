#!/bin/sh
# make an executable rescuebox clu
# add --debug=imports if needed
# install pre reqs like python , python dev , windows wsl env need wslview ( /usr/bin/xdg-open -> /usr/bin/wslview )

poetry run pyinstaller --onefile --add-data 'src/rb-api/rb/api/static:static' --add-data 'src/rb-api/rb/api/routes/templates:templates' --add-data 'src/rb-api/rb/api/static/favicon.ico:static'  --paths /tmp/rb/RescueBox/src/rb-api/rb/api --hidden-import main --collect-submodules fastapi  --name rescuebox src/rb-api/rb/api/main.py
