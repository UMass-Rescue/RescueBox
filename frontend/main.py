"""
RescueBox Desktop Frontend - Main Entry Point

Initializes NiceGUI, optional integrated FastAPI plugin routes, and the home page.

Usage::
    python -m frontend.main
"""
from __future__ import annotations
import sys
import platform
import os
from pathlib import Path    
import asyncio
import logging
from starlette.responses import HTMLResponse
from nicegui import app, Client, ui
from frontend.config import (
    API_BASE_URL,
    API_TIMEOUT,
    APP_PORT,
    APP_TITLE,
    APP_VERSION,
    BACKEND_URL,
    LOG_FILE,
    LOG_LEVEL,
    RECONNECT_TIMEOUT,
)
from frontend.constants import (
    HOME_USER_ID,
    NAV_LINKS,
    UI_BUTTONS,
    UI_TITLES,
    is_valid_explicit_user_id,
)
from frontend.database import init_db
from frontend.components.shared import create_navbar
from frontend.utils import configure_logging_with_context
from frontend.utils import parse_log_level
from frontend import utils as _backend_integration
from frontend.design_tokens import Design
from frontend.utils import (
    clear_explicit_user_id,
    ensure_explicit_user_id_for_tests,
    get_explicit_user_id,
    set_explicit_user_id,
    try_claim_explicit_user_id,
)

logging.basicConfig(level=parse_log_level(LOG_LEVEL))
configure_logging_with_context(log_file_path=str(LOG_FILE), log_level=LOG_LEVEL)

logger = logging.getLogger(__name__)
logger.setLevel(parse_log_level(LOG_LEVEL))

# Fix for WinError 10054 Proactor Pipe Transport crashes on Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if sys.stdout is None or not hasattr(sys.stdout, 'write'):
    # Create a log file in the same directory as the .exe
    log_path = os.path.join(os.path.dirname(sys.executable), "frontend.log")
    sys.stdout = open(log_path, "w", encoding="utf-8", buffering=1)
    sys.stderr = sys.stdout

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    # 1. Safely get APPDATA, falling back to the standard home directory if it's missing
    appdata_path = os.getenv('APPDATA', str(Path.home()))
    base_dir = Path(appdata_path / '.rescuebox')
    if platform.system() == "Windows":
        base_dir = Path(appdata_path / 'RescueBox-Desktop')


    # 2. Construct the path
    custom_storage_dir = base_dir / 'nicegui'

    # 3. Explicitly cast the Path object to a string for the environment variable
    os.environ['NICEGUI_STORAGE_PATH'] = str(custom_storage_dir)

# Repo root + src (for rb.* plugins when running as a module)
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))

# Determine the base path for resources in a PyInstaller bundle
if hasattr(sys, '_MEIPASS'):
    base_path = sys._MEIPASS
    if sys.stderr is None or sys.stdout is None:
        _output = open("nicegui-app.log", "w")  # noqa: SIM115 # keep it open until the whole python ends.
        if sys.stderr is None:
            sys.stderr = _output
        if sys.stdout is None:
            sys.stdout = _output
else:
    base_path = os.path.abspath(".")

# Construct the absolute path to the icon inside the bundle
APP_FAVICON = os.path.join(base_path, 'icons', 'rb.webp')



try:
    _backend_integration.set_backend_available(True)
    logger.debug("Backend routes package available")
except ImportError as e:
    _backend_integration.set_backend_available(False)
    logger.warning("Backend routes not available: %s. Running frontend only.", e)

BACKEND_AVAILABLE = _backend_integration.BACKEND_AVAILABLE
prefetch_and_cache_models = _backend_integration.prefetch_and_cache_models
setup_backend_routes = _backend_integration.setup_backend_routes


@ui.page("/")
async def index():
    """Main dashboard / home page."""
    logger.debug("Rendering main dashboard page (index route)")

    from frontend.utils import apply_saved_theme

    apply_saved_theme()
    logger.debug("Theme preference applied")

    ui.add_head_html(
        """
        <style>
            .q-header { min-height: 12px !important; }
            .q-toolbar { min-height: 12px !important; padding: 0 8px !important; }
            .q-toolbar__title { font-size: 0.85rem !important; min-height: unset !important; line-height: 32px !important; }
            .q-btn { font-size: 0.7rem !important; padding: 2px 6px !important; min-height: unset !important; }
            body { font-size: 0.8rem !important; }
        </style>
    """
    )

    create_navbar()
    logger.debug("Navigation bar added to page")

    ensure_explicit_user_id_for_tests()
    explicit_user_id = get_explicit_user_id()

    with ui.column().classes("container mx-auto p-8"):
        logger.debug("Creating main content container")
        if explicit_user_id:
            ui.label(UI_TITLES["home"]).classes("text-4xl font-bold mb-4")
            ui.label(UI_TITLES["home_subtitle"]).classes("text-xl text-zinc-600")
            with ui.card().classes("w-full max-w-xl mt-4 p-4 bg-zinc-50"):
                ui.label(f"{HOME_USER_ID['current_prefix']} {explicit_user_id}").classes(
                    "text-sm font-medium"
                )
                ui.label(HOME_USER_ID["change_user_hint"]).classes("text-xs text-zinc-500 mt-1")
                with ui.row().classes("mt-3"):

                    def _change_user_id():
                        clear_explicit_user_id()
                        ui.timer(0.2, lambda: ui.navigate.reload(), once=True)

                   # ui.button(
                   #     HOME_USER_ID["change_user_button"],
                   #     on_click=_change_user_id,
                   # ).classes("bg-zinc-200 text-zinc-800")

            with ui.row().classes("gap-4 mt-8"):
                logger.debug("Creating action buttons")

                ui.button(
                    UI_BUTTONS["browse_models"],
                    on_click=lambda: ui.navigate.to(NAV_LINKS["models"]),
                ).classes(Design.BTN_PRIMARY)
                logger.debug("Browse Models button created")

                ui.button(
                    UI_BUTTONS["open_assistant"],
                    on_click=lambda: ui.navigate.to(NAV_LINKS["chatbot"]),
                ).classes(Design.BTN_PRIMARY)
                logger.debug("Open Assistant button created")
        else:
            with ui.card().classes("w-full max-w-xl p-6 shadow-md border"):
                ui.label(HOME_USER_ID["title"]).classes("text-xl font-semibold mb-2")
                ui.label(HOME_USER_ID["blurb"]).classes("text-zinc-600 mb-4")
                uid_input = ui.input(
                    HOME_USER_ID["input_label"],
                    placeholder=HOME_USER_ID["placeholder"],
                ).classes("w-full")

                def _save_home_user_id():
                    val = (uid_input.value or "").strip()
                    if not val:
                        ui.notify("Please enter a User ID.", type="warning", classes="rb-notify-505759")
                        return
                    if not is_valid_explicit_user_id(val):
                        ui.notify(HOME_USER_ID["invalid_format"], type="warning", classes="rb-notify-505759")
                        return
                    claim = try_claim_explicit_user_id(val)
                    if claim == "taken":
                        ui.notify(
                            HOME_USER_ID["id_taken"],
                            type="warning",
                            classes="rb-notify-a2aaad",
                        )
                        return
                    if claim != "ok":
                        return
                    set_explicit_user_id(val)
                    # After set_explicit_user_id (deferred browser write); reload must run later.
                    ui.timer(0.08, lambda: ui.navigate.reload(), once=True)

                def _on_uid_keydown(e):
                    if getattr(e, "args", None) and e.args.get("key") == "Enter":
                        _save_home_user_id()

                uid_input.on("keydown", _on_uid_keydown)
                ui.button(
                    HOME_USER_ID["save_button"],
                    on_click=_save_home_user_id,
                ).classes(f"mt-4 {Design.BTN_PRIMARY}")

    logger.debug("Main dashboard page rendered successfully")


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

    icons_dir = Path(__file__).parent / "icons"
    if icons_dir.is_dir():
        app.add_static_files(url_path="/icons", local_directory=str(icons_dir))
        logger.debug("Icons served at /icons/")

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
        await prefetch_and_cache_models(backend_url=BACKEND_URL, api_timeout=API_TIMEOUT)

    app.on_startup(_prefetch_models_startup)

    from frontend.utils import inject_global_readability_css

    # Register brand + readability CSS before ui.run so it is not lost vs. on_startup ordering.
    inject_global_readability_css()

    import importlib

    importlib.import_module("frontend.pages")  # register @ui.page handlers

    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.critical("Unhandled exception in NiceGUI application: %s", str(exc))
        logger.critical("Exception type: %s", type(exc).__name__)
        import traceback

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
                    RescueBox encountered an unexpected error. This has been logged and will be investigated.
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
        from frontend.utils import release_demo_folder_for_client

        release_demo_folder_for_client(client)

    ui.run(
        title=f"{APP_TITLE} · {APP_VERSION}",
        port=APP_PORT,
        favicon=APP_FAVICON,
        show=False,
        reconnect_timeout=RECONNECT_TIMEOUT,
        storage_secret="REPLACE_WITH_A_REAL_SECRET_KEY",
        reload=False
    )
