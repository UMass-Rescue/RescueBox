import os
from pathlib import Path


project_root = Path(__file__).resolve().parent.parent
DATA_DIR = os.path.join(project_root, "resources")

os.makedirs(DATA_DIR, exist_ok=True)


def get_resource_path(filename):
    return os.path.join(DATA_DIR, filename)


def get_config_path(filename):
    return os.path.join(project_root, "config", filename)
