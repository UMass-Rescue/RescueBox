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
    BACKEND_URL,
    LOG_FILE,
    LOG_LEVEL,
    RECONNECT_TIMEOUT,
)
from frontend.utils import (
    apply_saved_theme,
    browse_directory_simple,
    get_active_case_id,
    set_active_case_id,
)
from frontend.database import get_case_db
from frontend.database import init_db
from frontend.components.shared import create_navbar
from frontend.utils import configure_logging_with_context
from frontend.utils import parse_log_level
from frontend import utils as _backend_integration
from frontend.design_tokens import Design
from frontend.utils import (
    ensure_explicit_user_id_for_tests,
)

logging.basicConfig(level=parse_log_level(LOG_LEVEL))
configure_logging_with_context(log_file_path=str(LOG_FILE), log_level=LOG_LEVEL)

logger = logging.getLogger(__name__)
logger.setLevel(parse_log_level(LOG_LEVEL))

# Fix for WinError 10054 Proactor Pipe Transport crashes on Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if sys.stdout is None or not hasattr(sys.stdout, "write"):
    # Create a log file in the same directory as the .exe
    log_path = os.path.join(os.path.dirname(sys.executable), "frontend.log")
    sys.stdout = open(log_path, "w", encoding="utf-8", buffering=1)
    sys.stderr = sys.stdout

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    # 1. Safely get APPDATA, falling back to the standard home directory if it's missing
    appdata_path = os.getenv("APPDATA", str(Path.home()))
    base_dir = Path(appdata_path / ".rescuebox")
    if platform.system() == "Windows":
        base_dir = Path(appdata_path / "RescueBox-Desktop")

    # 2. Construct the path
    custom_storage_dir = base_dir / "nicegui"

    # 3. Explicitly cast the Path object to a string for the environment variable
    os.environ["NICEGUI_STORAGE_PATH"] = str(custom_storage_dir)

# Repo root + src (for rb.* plugins when running as a module)
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))

# Determine the base path for resources in a PyInstaller bundle
if hasattr(sys, "_MEIPASS"):
    base_path = sys._MEIPASS
    if sys.stderr is None or sys.stdout is None:
        _output = open(
            "nicegui-app.log", "w"
        )  # noqa: SIM115 # keep it open until the whole python ends.
        if sys.stderr is None:
            sys.stderr = _output
        if sys.stdout is None:
            sys.stdout = _output
else:
    base_path = os.path.abspath(".")

# Construct the absolute path to the icon inside the bundle
if hasattr(sys, "_MEIPASS"):
    APP_FAVICON = os.path.join(sys._MEIPASS, "icons", "favicon.png")
else:
    APP_FAVICON = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "icons", "favicon.png"
    )


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
    """Main dashboard / home page (Case Management Dashboard)."""
    logger.debug("Rendering main dashboard page (index route)")

    apply_saved_theme()
    logger.debug("Theme preference applied")

    ui.add_head_html(
        """
        <style>
            .q-header { min-height: 54px !important; }
            .q-toolbar { min-height: 54px !important; padding: 0 16px !important; }
            .q-toolbar__title { font-size: 1.2rem !important; min-height: unset !important; line-height: 54px !important; }
            .q-btn { font-size: 0.95rem !important; padding: 6px 12px !important; min-height: unset !important; }
            body { font-size: 1.05rem !important; }
        </style>
    """
    )

    create_navbar()
    logger.debug("Navigation bar added to page")

    ensure_explicit_user_id_for_tests()

    with ui.column().classes(
        "container mx-auto px-4 sm:px-8 py-8 w-full max-w-6xl pb-16 gap-8"
    ):
        # Main Header
        with ui.row().classes("w-full items-center gap-3 mb-2"):
            ui.icon("folder_shared", size="lg").classes("text-[#881c1c]")
            ui.label("RescueBox Case Management").classes(
                "text-4xl font-bold text-slate-800"
            )
        ui.label(
            "Create a new investigative case or load an existing one to begin."
        ).classes("text-lg text-slate-500 mb-8 pl-1")

        # Unconditional Dual-pane Case Management setup
        with ui.row().classes("w-full gap-8 items-stretch flex-wrap md:flex-nowrap"):
            # Left Pane: Create New Case
            with ui.card().classes(
                "flex-1 p-6 border-t-4 border-t-[#881c1c] border-x border-b border-slate-200 shadow-md rounded-2xl bg-white"
            ):
                with ui.row().classes("items-center gap-2 mb-4"):
                    ui.icon("create_new_folder", size="sm").classes("text-[#881c1c]")
                    ui.label("Create New Case").classes(
                        "text-2xl font-bold text-slate-800"
                    )

                case_num_input = (
                    ui.input(
                        "Case Number / ID (Required, Unique)",
                        placeholder="e.g., CASE-2026-0042",
                    )
                    .classes("w-full mb-4")
                    .props("outlined dense")
                )
                with case_num_input.add_slot("prepend"):
                    ui.icon("assignment").classes("text-slate-400")

                investigators_input = (
                    ui.input(
                        "Investigators",
                        placeholder="e.g., Det. Smith, Agent Jones",
                    )
                    .classes("w-full mb-4")
                    .props("outlined dense")
                )
                with investigators_input.add_slot("prepend"):
                    ui.icon("people").classes("text-slate-400")

                with ui.column().classes("w-full mb-6 gap-1"):
                    ui.label("Evidence Directory / UFDR Path").classes(
                        "text-sm font-medium text-slate-700"
                    )
                    with ui.row().classes("w-full items-center gap-2 flex-nowrap"):
                        path_input = (
                            ui.input(
                                placeholder="/path/to/evidence",
                            )
                            .classes("flex-1")
                            .props("outlined dense")
                        )
                        with path_input.add_slot("prepend"):
                            ui.icon("folder").classes("text-slate-400")

                        ui.button(
                            "Browse",
                            icon="folder_open",
                            color=None,
                            on_click=lambda: browse_directory_simple(path_input),
                        ).classes(Design.BTN_MEDIUM_GRAY)

                async def _create_case():
                    num = (case_num_input.value or "").strip()
                    inv = (investigators_input.value or "").strip()
                    path = (path_input.value or "").strip()

                    if not num:
                        ui.notify("Case Number is required.", type="warning")
                        return
                    if not path:
                        ui.notify("Evidence Path is required.", type="warning")
                        return

                    try:
                        case_db = get_case_db()
                        new_case = await case_db.create_case(
                            case_number=num,
                            investigators=inv,
                            evidence_path=path,
                        )
                        set_active_case_id(new_case.caseId)
                        ui.notify(
                            f"Case {num} created and loaded successfully.",
                            type="positive",
                        )
                        ui.timer(0.5, lambda: ui.navigate.to("/case"), once=True)
                    except ValueError as e:
                        ui.notify(str(e), type="negative")
                    except Exception as e:
                        ui.notify(f"Failed to create case: {e}", type="negative")

                ui.button(
                    "Create & Load Case",
                    icon="add_circle",
                    color=None,
                    on_click=_create_case,
                ).classes(Design.BTN_PRIMARY + " w-full py-3 text-base")

            # Right Pane: Load Existing Case
            with ui.card().classes(
                "flex-1 p-6 border-t-4 border-t-[#881c1c] border-x border-b border-slate-200 shadow-md rounded-2xl bg-white flex flex-col"
            ):
                with ui.row().classes("items-center gap-2 mb-4"):
                    ui.icon("folder_open", size="sm").classes("text-[#881c1c]")
                    ui.label("Load Existing Case").classes(
                        "text-2xl font-bold text-slate-800"
                    )

                cases_container = ui.column().classes(
                    "w-full flex-1 overflow-y-auto space-y-3 max-h-[400px]"
                )

                async def _load_cases():
                    cases_container.clear()
                    try:
                        case_db = get_case_db()
                        all_cases = await case_db.get_all_cases()
                        if not all_cases:
                            with cases_container:
                                ui.label("No existing cases found.").classes(
                                    "text-slate-400 italic p-4 text-center w-full"
                                )
                            return

                        with cases_container:
                            for c in all_cases:
                                with ui.card().classes(
                                    "w-full p-4 border-l-4 border-l-[#881c1c] border-y border-r border-slate-200 hover:border-slate-300 hover:shadow-md transition-all bg-slate-50 rounded-xl"
                                ):
                                    with ui.row().classes(
                                        "w-full justify-between items-center"
                                    ):
                                        with ui.column().classes(
                                            "gap-1 flex-1 min-w-0"
                                        ):
                                            with ui.row().classes(
                                                "items-center gap-1.5"
                                            ):
                                                ui.icon("folder", size="xs").classes(
                                                    "text-[#881c1c]"
                                                )
                                                ui.label(c.caseNumber).classes(
                                                    "font-bold text-lg text-slate-800 truncate"
                                                )
                                            if c.investigators:
                                                with ui.row().classes(
                                                    "items-center gap-1.5"
                                                ):
                                                    ui.icon(
                                                        "people", size="xs"
                                                    ).classes("text-slate-400")
                                                    ui.label(
                                                        f"Investigators: {c.investigators}"
                                                    ).classes(
                                                        "text-sm text-slate-600 truncate"
                                                    )
                                            with ui.row().classes(
                                                "items-center gap-1.5"
                                            ):
                                                ui.icon("link", size="xs").classes(
                                                    "text-slate-400"
                                                )
                                                ui.label(
                                                    f"Path: {c.evidencePath}"
                                                ).classes(
                                                    "text-xs font-mono text-slate-500 truncate"
                                                )

                                        def _load(cid=c.caseId, cnum=c.caseNumber):
                                            set_active_case_id(cid)
                                            ui.notify(
                                                f"Loaded case {cnum}.", type="positive"
                                            )
                                            ui.timer(
                                                0.3,
                                                lambda: ui.navigate.to("/case"),
                                                once=True,
                                            )

                                        ui.button(
                                            "Load",
                                            icon="login",
                                            color=None,
                                            on_click=lambda cid=c.caseId, cnum=c.caseNumber: _load(
                                                cid, cnum
                                            ),
                                        ).classes(Design.BTN_PRIMARY_COMPACT)
                    except Exception as e:
                        logger.error("Error loading cases: %s", e)
                        with cases_container:
                            ui.label(f"Error loading cases: {e}").classes(
                                "text-red-500"
                            )

                await _load_cases()

    logger.debug("Main dashboard page rendered successfully")


@ui.page("/case")
async def case_overview():
    """Active Case Overview / Dashboard."""
    logger.debug("Rendering case overview page")

    from frontend.utils import (
        apply_saved_theme,
        clear_active_case_id,
    )
    from frontend.database import get_case_db, get_job_db

    apply_saved_theme()
    logger.debug("Theme preference applied")

    ui.add_head_html(
        """
        <style>
            .q-header { min-height: 54px !important; }
            .q-toolbar { min-height: 54px !important; padding: 0 16px !important; }
            .q-toolbar__title { font-size: 1.2rem !important; min-height: unset !important; line-height: 54px !important; }
            .q-btn { font-size: 0.95rem !important; padding: 6px 12px !important; min-height: unset !important; }
            body { font-size: 1.05rem !important; }
        </style>
    """
    )

    create_navbar()
    logger.debug("Navigation bar added to page")

    ensure_explicit_user_id_for_tests()
    active_case_id = get_active_case_id()

    if not active_case_id:
        # If no active case, redirect to home page to create or load one
        ui.notify(
            "No active case loaded. Please create or load a case.", type="warning"
        )
        ui.timer(0.1, lambda: ui.navigate.to("/"), once=True)
        return

    with ui.column().classes(
        "container mx-auto px-4 sm:px-8 py-8 w-full max-w-6xl pb-16 gap-8"
    ):
        # Active Case Dashboard
        case_db = get_case_db()
        case = await case_db.get_case_by_id(active_case_id)
        if not case:
            # Fallback if case not found
            clear_active_case_id()
            ui.timer(0.1, lambda: ui.navigate.to("/"), once=True)
            return

        with ui.row().classes("items-center gap-3 mb-2"):
            ui.icon("folder_special", size="lg").classes("text-[#881c1c]")
            ui.label(f"Case: {case.caseNumber}").classes(
                "text-4xl font-bold text-slate-800"
            )
        if case.investigators:
            with ui.row().classes("items-center gap-2 mb-6 pl-1"):
                ui.icon("people", size="xs").classes("text-slate-500")
                ui.label(f"Investigators: {case.investigators}").classes(
                    "text-lg text-slate-600"
                )

        # Case Details Card
        with ui.card().classes(
            "w-full p-6 border-t-4 border-t-[#881c1c] border-x border-b border-slate-200 shadow-md rounded-2xl bg-white mb-8"
        ):
            with ui.row().classes(
                "items-center gap-2 mb-4 border-b pb-2 border-slate-100"
            ):
                ui.icon("info", size="sm").classes("text-[#881c1c]")
                ui.label("Case Information").classes("text-xl font-bold text-slate-800")
            with ui.column().classes("w-full gap-3"):
                with ui.row().classes("items-center gap-2.5"):
                    ui.icon("fingerprint", size="xs").classes("text-slate-400")
                    ui.label("Case ID:").classes(
                        "font-semibold text-slate-700 w-24 shrink-0"
                    )
                    ui.label(case.caseId).classes(
                        "font-mono text-slate-600 truncate bg-slate-50 px-2 py-0.5 rounded border border-slate-100"
                    )
                with ui.row().classes("items-center gap-2.5"):
                    ui.icon("today", size="xs").classes("text-slate-400")
                    ui.label("Created:").classes(
                        "font-semibold text-slate-700 w-24 shrink-0"
                    )
                    ui.label(case.createdAt[:10] + " " + case.createdAt[11:16]).classes(
                        "text-slate-600"
                    )
                with ui.row().classes(
                    "items-center gap-2.5 w-full flex-wrap sm:flex-nowrap"
                ):
                    ui.icon("folder", size="xs").classes("text-slate-400")
                    ui.label("Evidence Path:").classes(
                        "font-semibold text-slate-700 w-24 shrink-0"
                    )
                    path_display = (
                        ui.input(value=case.evidencePath)
                        .classes("flex-1 min-w-0")
                        .props("outlined dense readonly")
                    )
                    with path_display.add_slot("prepend"):
                        ui.icon("folder", size="xs").classes("text-slate-400")

                    async def _change_path():
                        with ui.dialog() as d, ui.card().classes(
                            "p-6 w-full max-w-lg bg-white border-t-4 border-t-[#881c1c] border-x border-b border-slate-200 rounded-2xl shadow-xl"
                        ):
                            with ui.row().classes("items-center gap-2 mb-4"):
                                ui.icon("edit", size="sm").classes("text-[#881c1c]")
                                ui.label("Update Evidence Path").classes(
                                    "text-xl font-bold text-slate-800"
                                )
                            new_path_input = (
                                ui.input(
                                    "New Evidence Directory / UFDR Path",
                                    value=case.evidencePath,
                                )
                                .classes("w-full mb-6")
                                .props("outlined dense")
                            )
                            with new_path_input.add_slot("prepend"):
                                ui.icon("folder").classes("text-slate-400")
                            with ui.row().classes("w-full justify-end gap-2"):
                                ui.button(
                                    "Cancel", icon="close", color=None, on_click=d.close
                                ).classes(Design.BTN_MEDIUM_GRAY)

                                async def _save_path():
                                    p = (new_path_input.value or "").strip()
                                    if not p:
                                        ui.notify(
                                            "Path cannot be empty.", type="warning"
                                        )
                                        return
                                    await case_db.update_case_evidence_path(
                                        case.caseId, p
                                    )
                                    ui.notify(
                                        "Evidence path updated successfully.",
                                        type="positive",
                                    )
                                    d.close()
                                    ui.timer(
                                        0.3, lambda: ui.navigate.reload(), once=True
                                    )

                                ui.button(
                                    "Save", icon="save", color=None, on_click=_save_path
                                ).classes(Design.BTN_PRIMARY_COMPACT)
                        d.open()

                    ui.button(
                        "Change Path", icon="edit", color=None, on_click=_change_path
                    ).classes(Design.BTN_MEDIUM_GRAY)

        # Case Results (Jobs) Table
        with ui.row().classes("items-center gap-2 mb-4"):
            ui.icon("view_list", size="sm").classes("text-[#881c1c]")
            ui.label("Case Results & Jobs").classes("text-2xl font-bold text-slate-800")

        jobs_container = ui.column().classes("w-full space-y-2")

        async def _load_case_jobs():
            jobs_container.clear()
            try:
                job_db = get_job_db()
                jobs_data = await job_db.get_all_jobs()
                if not jobs_data:
                    with jobs_container:
                        ui.label(
                            "No jobs or results associated with this case yet."
                        ).classes(
                            "text-slate-400 italic p-6 text-center w-full bg-slate-50 rounded-xl border border-dashed border-slate-200"
                        )
                    return

                with jobs_container:
                    # Header Row
                    with ui.row().classes(
                        "bg-[#1c1c1c] text-white p-4 font-semibold w-full rounded-t-xl items-center"
                    ):
                        ui.label("Job ID").classes("w-32 shrink-0")
                        ui.label("Plugin / Task").classes("flex-1 min-w-0")
                        ui.label("Start Time").classes("w-48 shrink-0")
                        ui.label("Status").classes("w-36 shrink-0")
                        ui.label("Actions").classes("w-48 shrink-0")

                    for job in jobs_data:
                        uid = job.get("uid")
                        endpoint = job.get("endpoint")
                        pname = job.get("plugin_name") or endpoint or "Unknown"
                        start_time = job.get("startTime") or "N/A"
                        if "T" in start_time:
                            start_time = start_time.replace("T", " ")[:16]
                        status = job.get("status", "Unknown")

                        # Status Pill Badges
                        status_pill_classes = {
                            "Completed": "bg-emerald-50 text-emerald-700 border border-emerald-200",
                            "Running": "bg-rose-50 text-[#881c1c] border border-rose-200",
                            "Failed": "bg-rose-50 text-rose-700 border border-rose-200",
                            "Canceled": "bg-slate-100 text-slate-600 border border-slate-200",
                        }
                        pill_cls = status_pill_classes.get(
                            status, "bg-slate-50 text-slate-500 border border-slate-200"
                        )

                        with ui.row().classes(
                            "p-4 border-b border-slate-200 hover:bg-slate-50 items-center w-full flex-nowrap gap-2 bg-white"
                        ):
                            ui.label(uid).classes(
                                "font-mono text-sm w-32 shrink-0 truncate text-slate-800"
                            ).tooltip(uid)
                            ui.label(pname).classes(
                                "flex-1 min-w-0 truncate text-slate-800"
                            )
                            ui.label(start_time).classes(
                                "w-48 shrink-0 text-sm text-slate-600"
                            )

                            # Render status pill badge
                            with ui.row().classes(
                                f"w-36 shrink-0 items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold {pill_cls}"
                            ):
                                if status == "Completed":
                                    ui.icon("check_circle", size="14px")
                                elif status == "Running":
                                    ui.spinner(size="14px").classes("text-[#881c1c]")
                                elif status == "Failed":
                                    ui.icon("error", size="14px")
                                else:
                                    ui.icon("cancel", size="14px")
                                ui.label(status)

                            with ui.row().classes("w-48 shrink-0 gap-2 flex-nowrap"):
                                ui.button(
                                    "Open",
                                    icon="visibility",
                                    color=None,
                                    on_click=lambda jid=uid: ui.navigate.to(
                                        f"/jobs/{jid}"
                                    ),
                                ).classes(Design.BTN_PRIMARY_TIGHT)

                                async def _remove_job(jid=uid):
                                    await get_job_db().disassociate_job_from_case(jid)
                                    ui.notify(
                                        f"Job {jid} removed from case.", type="info"
                                    )
                                    await _load_case_jobs()

                                ui.button(
                                    "Remove",
                                    icon="delete",
                                    color=None,
                                    on_click=lambda jid=uid: _remove_job(jid),
                                ).classes(
                                    "bg-rose-50 hover:bg-rose-100 text-[#881c1c] px-3 py-1 rounded text-sm transition-colors border border-rose-200"
                                )

            except Exception as e:
                logger.error("Error loading case jobs: %s", e)
                with jobs_container:
                    ui.label(f"Error loading jobs: {e}").classes("text-red-500")

        await _load_case_jobs()

    logger.debug("Case overview page rendered successfully")


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
        await prefetch_and_cache_models(
            backend_url=BACKEND_URL, api_timeout=API_TIMEOUT
        )

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
        title=APP_TITLE,
        port=APP_PORT,
        favicon=APP_FAVICON,
        show=False,
        reconnect_timeout=RECONNECT_TIMEOUT,
        storage_secret="REPLACE_WITH_A_REAL_SECRET_KEY",
        reload=False,
    )
