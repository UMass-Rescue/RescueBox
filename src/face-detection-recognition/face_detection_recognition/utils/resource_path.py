import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
DATA_DIR = os.path.join(project_root, "resources")
if hasattr(sys, "_MEIPASS"):
    DATA_DIR = sys._MEIPASS


def get_resource_path(filename):
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, filename)


def get_config_path(filename):
    return os.path.join(project_root, "config", filename)
