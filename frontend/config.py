"""
Frontend Configuration

This module provides centralized configuration for the RescueBox Desktop frontend.
All configuration values can be overridden via environment variables.

Usage:
    from frontend.config import API_BASE_URL, APP_PORT
    
    api_client = httpx.AsyncClient(base_url=API_BASE_URL)
"""

import os
from pathlib import Path

# API Configuration
# When backend is integrated into NiceGUI, API is on the same port as frontend
# Default to same port as frontend (unified server)
_DEFAULT_API_URL = f'http://localhost:{int(os.getenv("RESCUEBOX_PORT", "8080"))}'
_DEFAULT_BACKEND_PORT = 8080
BACKEND_URL = f'http://localhost:{_DEFAULT_BACKEND_PORT}'
# Add /api prefix to the base URL to avoid collisions with UI routes
API_BASE_URL = os.getenv('RESCUEBOX_API_URL', f"{_DEFAULT_API_URL}/api")
API_TIMEOUT = float(os.getenv('RESCUEBOX_API_TIMEOUT', '30.0'))

# Application Configuration
APP_TITLE = os.getenv('RESCUEBOX_APP_TITLE', 'RescueBox')
APP_PORT = int(os.getenv('RESCUEBOX_PORT', '8080'))
APP_VERSION = os.getenv('RESCUEBOX_VERSION', '3.0.0')
# Tab icon: filesystem path so NiceGUI can serve it at /favicon.ico (webp is fine for modern browsers)
APP_FAVICON = Path(__file__).resolve().parent / 'icons' / 'rb.webp'
APP_DARK_MODE = os.getenv('RESCUEBOX_DARK_MODE', 'false').lower() == 'true'
APP_SHOW_BROWSER = os.getenv('RESCUEBOX_SHOW_BROWSER', 'false').lower() == 'true'

# Database Configuration
DATA_DIR = Path(__file__).parent / 'data'
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / 'jobs.db'

# Logging Configuration
LOG_LEVEL = os.getenv('RESCUEBOX_LOG_LEVEL', 'INFO')
LOG_FILE = DATA_DIR / 'rescuebox.log'

# Demo folders: each browser session gets one folder from this pool (Option 1 auto-assign)
DEMO_FOLDERS_BASE = Path(os.getenv('RESCUEBOX_DEMO_FOLDERS_BASE', '/home/tester/Documents'))
DEMO_FOLDER_NAMES = ['demo1', 'demo2', 'demo3', 'demo4', 'demo5', 'demo6', 'demo7', 'demo8', 'demo9', 'demo10']

# Browsable tree on /demo (inputs/outputs samples). Override with RESCUEBOX_DEMO_FILES_DIR.
DEMO_FILES_BROWSE_ROOT = Path(
    os.getenv('RESCUEBOX_DEMO_FILES_DIR', str(DEMO_FOLDERS_BASE / 'demo'))
).expanduser()

# Reconnect timeout (seconds) before client is deleted; 1 hour keeps demo folder for entire demo
RECONNECT_TIMEOUT = float(os.getenv('RESCUEBOX_RECONNECT_TIMEOUT', '3600'))
