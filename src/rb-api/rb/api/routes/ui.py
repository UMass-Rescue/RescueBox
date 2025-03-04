import json
import os
import os.path as op
import sys

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from rb.lib.typer import typer_app_to_tree


from rescuebox.main import app as rescuebox_app

ui_router = APIRouter()

"""
#BASE_DIR = Path(__file__).parent.resolve() 
#fpath = os.path.join("." , "templates")
"""

# determine if application is a script file or frozen exe

this_file = op.abspath(__file__)

if getattr(sys, 'frozen', False):
    application_path = getattr(sys, '_MEIPASS', op.dirname(sys.executable))
else:
    application_path = op.dirname(this_file)

print("application_path ", application_path)
templates = Jinja2Templates(
    directory=os.path.join( application_path, "..",  "templates"),
)


@ui_router.get("/")
async def interface(request: Request):
    tree = typer_app_to_tree(rescuebox_app)
    return templates.TemplateResponse(
        "index.html.j2", {"request": request, "tree": json.dumps(tree)}
    )