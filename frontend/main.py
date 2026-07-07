"""
RescueBox Desktop Frontend - Main Entry Point

Initializes NiceGUI and optional integrated FastAPI plugin routes; pages register via ``frontend.pages``.

Usage::
    python -m frontend.main
"""

from __future__ import annotations
import sys
import platform
import os
from pathlib import Path
import frontend.pages  # noqa: F401 # (static import for PyInstaller)
import asyncio
import contextlib
import logging
import traceback
from starlette.requests import Request
from starlette.responses import HTMLResponse
from nicegui import app, Client, ui
from frontend.config import (
    API_BASE_URL,
    API_TIMEOUT,
    APP_PORT,
    APP_SHOW_BROWSER,
    APP_TITLE,
    BACKEND_URL,
    LOG_FILE,
    LOG_LEVEL,
    RECONNECT_TIMEOUT,
)
from frontend import utils as _backend_integration
from frontend.database import init_db
from frontend.utils import (
    configure_logging_with_context,
    inject_global_readability_css,
    parse_log_level,
    release_demo_folder_for_client,
)

# Repo root on sys.path for ``python frontend/main.py`` and PyInstaller bundles.
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

logging.basicConfig(level=parse_log_level(LOG_LEVEL))
configure_logging_with_context(log_file_path=str(LOG_FILE), log_level=LOG_LEVEL)

logger = logging.getLogger(__name__)
logger.setLevel(parse_log_level(LOG_LEVEL))

_PERSISTENT_STDIO = contextlib.ExitStack()
_PYINSTALLER_MEIPASS = getattr(sys, "_MEIPASS", None)

# Fix for WinError 10054 Proactor Pipe Transport crashes on Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if sys.stdout is None or not hasattr(sys.stdout, "write"):
    log_path = os.path.join(os.path.dirname(sys.executable), "frontend.log")
    sys.stdout = _PERSISTENT_STDIO.enter_context(
        open(log_path, "w", encoding="utf-8", buffering=1)
    )
    sys.stderr = sys.stdout

if getattr(sys, "frozen", False) and _PYINSTALLER_MEIPASS is not None:
    # 1. Safely get APPDATA, falling back to the standard home directory if it's missing
    appdata_path = os.getenv("APPDATA", str(Path.home()))
    base_dir = Path(appdata_path) / ".rescuebox"
    if platform.system() == "Windows":
        base_dir = Path(appdata_path) / "RescueBox-Desktop"

    # 2. Construct the path
    custom_storage_dir = base_dir / "nicegui"

    # 3. Explicitly cast the Path object to a string for the environment variable
    os.environ["NICEGUI_STORAGE_PATH"] = str(custom_storage_dir)

# Determine the base path for resources in a PyInstaller bundle
if _PYINSTALLER_MEIPASS is not None:
    base_path = _PYINSTALLER_MEIPASS
    if sys.stderr is None or sys.stdout is None:
        _output = _PERSISTENT_STDIO.enter_context(
            open("nicegui-app.log", "w", encoding="utf-8")
        )
        if sys.stderr is None:
            sys.stderr = _output
        if sys.stdout is None:
            sys.stdout = _output
else:
    base_path = os.path.abspath(".")


def _resolve_icons_dir() -> Path | None:
    """Directory for /icons static files (PyInstaller datas live under _MEIPASS/icons)."""
    candidates: list[Path] = []
    if _PYINSTALLER_MEIPASS is not None:
        candidates.append(Path(_PYINSTALLER_MEIPASS) / "icons")
    candidates.append(Path(__file__).resolve().parent / "icons")
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates.append(exe_dir / "_internal" / "icons")
        candidates.append(exe_dir / "icons")
    for path in candidates:
        if path.is_dir():
            return path
    return None


def _resolve_favicon_path() -> str | None:
    icons_dir = _resolve_icons_dir()
    if icons_dir is None:
        return None
    favicon = icons_dir / "favicon.png"
    return str(favicon) if favicon.is_file() else None


APP_FAVICON = _resolve_favicon_path()


try:
    _backend_integration.set_backend_available(True)
    logger.debug("Backend routes package available")
except ImportError as e:
    _backend_integration.set_backend_available(False)
    logger.warning("Backend routes not available: %s. Running frontend only.", e)

BACKEND_AVAILABLE = _backend_integration.BACKEND_AVAILABLE
prefetch_and_cache_models = _backend_integration.prefetch_and_cache_models
setup_backend_routes = _backend_integration.setup_backend_routes


_LICENSES_COPYRIGHT_DIR = _project_root / "License&Copyright"


if __name__ in {"__main__", "__mp_main__"}:
    logger.debug("Starting unified %s application", APP_TITLE)
    logger.debug("Server will be available at http://localhost:%s", APP_PORT)

    init_db()
    setup_backend_routes(api_base_url=API_BASE_URL)
    logger.debug("Backend API routes integrated: %s", BACKEND_AVAILABLE)

    demo_dir = Path(__file__).parent / "demo"
    if demo_dir.exists():
        app.add_static_files(url_path="/demo", local_directory=str(demo_dir))
        logger.debug("Demo static files served at /demo/")

    icons_dir = _resolve_icons_dir()
    if icons_dir is not None:
        app.add_static_files(url_path="/icons", local_directory=str(icons_dir))
        logger.debug("Icons served at /icons/ from %s", icons_dir)
    else:
        logger.warning("Icons directory not found; /icons/logo.png will 404")

    # Same pattern as /demo: NiceGUI static files (not Starlette mount + directory index iframe).
    if _LICENSES_COPYRIGHT_DIR.is_dir():
        app.add_static_files(
            url_path="/license-copyright",
            local_directory=str(_LICENSES_COPYRIGHT_DIR),
        )
        logger.debug(
            "License & Copyright: About page /about, static /license-copyright/ (%s)",
            _LICENSES_COPYRIGHT_DIR,
        )

    async def _prefetch_models_startup():
        await prefetch_and_cache_models(
            _backend_url=BACKEND_URL, _api_timeout=API_TIMEOUT
        )

    app.on_startup(_prefetch_models_startup)

    inject_global_readability_css()

    @app.exception_handler(Exception)
    async def global_exception_handler(_request: Request, exc: Exception):
        logger.critical("Unhandled exception in NiceGUI application: %s", str(exc))
        logger.critical("Exception type: %s", type(exc).__name__)
        logger.critical("Global exception traceback: %s", traceback.format_exc())

        # Plain Starlette response — no NiceGUI client/slot (ui.html would fail here).
        return HTMLResponse(
            content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>RescueBox - Error</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f5f5; }
                .error-container { max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .error-icon { font-size: 4em; color: #ef4444; margin-bottom: 20px; }
                .error-title { color: #1f2937; margin-bottom: 20px; }
                .error-message { color: #6b7280; margin-bottom: 30px; }
                .reload-btn { background: #881c1c; color: white; padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; display: inline-block; }
                .reload-btn:hover { background: #6a1616; }
            </style>
        </head>
        <body>
            <div class="error-container">
                <div class="error-icon">🚫</div>
                <h1 class="error-title">Something went wrong</h1>
                <p class="error-message">
                    RescueBox encountered an unexpected error.
                </p>
                <button class="reload-btn" onclick="window.location.reload()">Reload Page</button>
            </div>
        </body>
        </html>
        """,
            status_code=500,
        )

    @app.on_delete
    async def _on_client_delete(client: Client):
        release_demo_folder_for_client(client)

    _run_kwargs = dict(
        title=APP_TITLE,
        port=APP_PORT,
        show=APP_SHOW_BROWSER,
        native=False,
        reconnect_timeout=RECONNECT_TIMEOUT,
        storage_secret="REPLACE_WITH_A_REAL_SECRET_KEY",
        reload=False,
        show_welcome_message=APP_SHOW_BROWSER,
    )
    if APP_FAVICON:
        _run_kwargs["favicon"] = APP_FAVICON
    else:
        logger.warning("favicon.png missing; starting without tab icon")
    ui.run(**_run_kwargs)
