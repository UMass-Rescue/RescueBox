"""
Frontend Configuration

This module provides centralized configuration for the RescueBox Desktop frontend.
All configuration values can be overridden via environment variables.

Usage:
    from frontend.config import API_BASE_URL, APP_PORT
    
    api_client = httpx.AsyncClient(base_url=API_BASE_URL)
"""

import os
import platform
from pathlib import Path

# API Configuration
# When backend is integrated into NiceGUI, API is on the same port as frontend (8080)
# When running as separate processes, API is on port 8000.
# Since setup_backend_routes is a placeholder, default to standalone backend port 8000.
_DEFAULT_BACKEND_PORT = int(os.getenv("RESCUEBOX_API_PORT", "8000"))
_DEFAULT_API_URL = f"http://127.0.0.1:{_DEFAULT_BACKEND_PORT}"
BACKEND_URL = _DEFAULT_API_URL
# Add /api prefix to the base URL to avoid collisions with UI routes
API_BASE_URL = os.getenv("RESCUEBOX_API_URL", f"{_DEFAULT_API_URL}/api")
API_TIMEOUT = float(os.getenv("RESCUEBOX_API_TIMEOUT", "30.0"))

# Application Configuration
APP_TITLE = os.getenv("RESCUEBOX_APP_TITLE", "RescueBox")
APP_PORT = int(os.getenv("RESCUEBOX_PORT", "8080"))
APP_VERSION = os.getenv("RESCUEBOX_VERSION", "3.0.0")
# Tab icon: filesystem path so NiceGUI can serve it at /favicon.ico
APP_FAVICON = Path(__file__).resolve().parent / "icons" / "favicon.png"
APP_DARK_MODE = os.getenv("RESCUEBOX_DARK_MODE", "false").lower() == "true"
APP_SHOW_BROWSER = os.getenv("RESCUEBOX_SHOW_BROWSER", "false").lower() == "false"

# About page (override for packaging / forks)
ABOUT_AUTHORS = os.getenv("RESCUEBOX_ABOUT_AUTHORS", "RescueBox Team")
ABOUT_REPO_URL = os.getenv(
    "RESCUEBOX_REPO_URL", "https://github.com/UMass-Rescue/RescueBox"
)
ABOUT_REPO_DESKTOP_URL = os.getenv(
    "RESCUEBOX_REPO_DESKTOP_URL",
    "https://github.com/UMass-Rescue/RescueBox-Desktop",
)

# Database Configuration
base_dir = None
DATA_DIR = ""
if os.getenv("HOME") is not None:
    base_dir = Path(os.getenv("HOME"))
    DATA_DIR = base_dir / ".rescuebox" / "data"
if platform.system() == "Windows":
    base_dir = Path(os.getenv("APPDATA"))
    DATA_DIR = base_dir / "RescueBox-Desktop" / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "jobs.db"

# Logging Configuration
LOG_LEVEL = os.getenv("RESCUEBOX_LOG_LEVEL", "INFO")
LOG_FILE = base_dir / "RescueBox-Desktop" / "logs" / "frontend.log"

# Demo folders: each browser session gets one folder from this pool (Option 1 auto-assign)
DEMO_BASE = "."
DEMO_FOLDERS_BASE = Path(os.getenv("RESCUEBOX_HOME", DEMO_BASE))
DEMO_FOLDER_NAMES = ["demo"]

# Browsable tree on /demo (inputs/outputs samples). Override with RESCUEBOX_DEMO_FILES_DIR.
DEMO_FILES_BROWSE_ROOT = Path(
    os.getenv("RESCUEBOX_HOME", str(DEMO_FOLDERS_BASE / "demo"))
).expanduser()

# Reconnect timeout (seconds) before client is deleted; 1 hour keeps demo folder for entire demo
RECONNECT_TIMEOUT = float(os.getenv("RESCUEBOX_RECONNECT_TIMEOUT", "3600"))
