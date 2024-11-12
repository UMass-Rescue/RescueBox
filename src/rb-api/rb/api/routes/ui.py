import json
import os
import os.path as op
import sys

from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from rb.lib.typer import typer_app_to_tree
import jinja2

from rescuebox.main import app as rescuebox_app

ui_router = APIRouter()

"""
#BASE_DIR = Path(__file__).parent.resolve() 
#fpath = os.path.join("." , "templates")
"""

# determine if application is a script file or frozen exe
try:
    this_file = __file__
except NameError:
    this_file = sys.argv[0]
this_file = op.abspath(this_file)

if getattr(sys, 'frozen', False):
    application_path = getattr(sys, '_MEIPASS', op.dirname(sys.executable))
else:
    application_path = op.dirname(this_file)

"""
fpath = os.path.join(".," , application_path , "templates")
for file_ in os.listdir(fpath):
    print("debug jinja " + file_)

print("debug jinja" + this_file)
print("debug jinja" + fpath)

envj = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath=fpath))
template = envj.get_template('index.html.j2')

print("debug " + str(template))
"""

templates = Jinja2Templates(
    directory=os.path.join("..", application_path,  "templates"),
    # this works directory='/tmp/templates'
)



@ui_router.get("/")
async def interface(request: Request):
    tree = typer_app_to_tree(rescuebox_app)
    return templates.TemplateResponse(
        "index.html.j2", {"request": request, "tree": json.dumps(tree)}
    )
