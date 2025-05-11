import os
import time
import threading
import platform

from utils import UFDRMount
from fuse import FUSE
from typing import TypedDict
from flask_ml.flask_ml_server import MLServer, load_file_as_string
from flask_ml.flask_ml_server.models import (
    FileInput, TextInput, InputSchema, InputType,
    TextResponse, ResponseBody, TaskSchema
)

server = MLServer(__name__)
APP_NAME = "ufdr-mounter"

class UFDRInputs(TypedDict):
    ufdr_file: FileInput
    mount_name: TextInput

class UFDRParameters(TypedDict):
    pass

# mount function 
def mount_in_background(ufdr_path, mount_path):
    try:
        FUSE(UFDRMount(ufdr_path), mount_path, foreground=True, ro=True, allow_other=True)
    except Exception as e:
        print(f"[ERROR] Mount thread failed: {e}")

def get_mount_path(mount_name: str) -> str:
    mount_name = mount_name.strip()
    if os.path.isabs(mount_name) or (platform.system() == "Windows" and len(mount_name) == 2 and mount_name[1] == ":"):
        return mount_name
    return os.path.abspath(os.path.join("mnt", mount_name))


server.add_app_metadata(
    name="UFDR Mount Service",
    author="Sribatscha Maharana",
    version="1.0.0",
    info=load_file_as_string("ufdr-app-info.md")
)

def ufdr_task_schema() -> TaskSchema:
    return TaskSchema(
        inputs=[
            InputSchema(key="ufdr_file", label="UFDR File", input_type=InputType.FILE),
            InputSchema(key="mount_name", label="Mount Folder", input_type=InputType.TEXT),
        ],
        parameters=[]
    )

@server.route("/mount", task_schema_func=ufdr_task_schema, short_title="Mount UFDR")
def mount_task(inputs: UFDRInputs, parameters: UFDRParameters) -> ResponseBody:
    ufdr_path = inputs["ufdr_file"].path
    mount_name = inputs["mount_name"].text.strip()
    mount_path = get_mount_path(mount_name)

    if not (platform.system() == "Windows" and len(mount_path) == 2 and mount_path[1] == ":"):
        os.makedirs(mount_path, exist_ok=True)

    t = threading.Thread(target=mount_in_background, args=(ufdr_path, mount_path), daemon=True)
    t.start()

    time.sleep(3)  # give FUSE time to mount

    try:
        contents = os.listdir(mount_path)
        msg = f"Mounted at {mount_path}"
    except Exception as e:
        msg = f"Mount failed: {e}"

    return ResponseBody(root=TextResponse(value=msg, title="Mount Result"))

if __name__ == "__main__":
    server.run()