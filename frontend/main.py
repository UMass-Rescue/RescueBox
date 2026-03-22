"""
RescueBox Desktop Frontend - Main Entry Point

This module serves as the main entry point for the RescueBox Desktop application.
It initializes NiceGUI and integrates the FastAPI backend routes into a single unified server.

Key responsibilities:
- Configure NiceGUI application settings
- Integrate backend FastAPI routes into NiceGUI's FastAPI app
- Render the main dashboard/home page

Usage:
    Run this module to start the unified RescueBox Desktop application:
    python -m frontend.main

Tips:
    - The application runs on port 8080 by default (configurable via RESCUEBOX_PORT env var)
    - All backend API routes are available at the root (e.g., /models, /probes, etc.)
    - Configuration is centralized in frontend.config
    - Navigation is handled through NiceGUI's routing system
"""

import logging
import os
import asyncio
import httpx
import sys
from pathlib import Path
from nicegui import ui, app, Client
from frontend.config import APP_TITLE, APP_PORT, APP_FAVICON, APP_DARK_MODE, APP_SHOW_BROWSER, RECONNECT_TIMEOUT
from frontend.components.shared import create_navbar
from frontend.constants import UI_TITLES, UI_BUTTONS, NAV_LINKS
from frontend.config import API_BASE_URL, BACKEND_URL, API_TIMEOUT, LOG_FILE, LOG_LEVEL
from frontend.database import init_db, cache_models
# Configure logging with context support
from frontend.utils.logging_context import configure_logging_with_context

# Import page modules to register routes with @ui.page decorator
# By importing the modules directly, we ensure that the @ui.page decorators
# within them are executed. This registers all necessary routes with the
# NiceGUI application and resolves "not accessed" linter warnings.
import frontend.pages.models
import frontend.pages.chatbot
import frontend.pages.jobs
import frontend.pages.demo

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

logging.basicConfig(level=logging.DEBUG)

# Configure root logger with context filter and file handler
LOG_LEVEL='DEBUG'
configure_logging_with_context(log_file_path=str(LOG_FILE), log_level=LOG_LEVEL)

# Configure logging for this module

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# Ensure root logger and common server loggers are at DEBUG for full diagnostics
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

# Quiet noisy socket/engineio logs
try:
    logging.getLogger('socketio.server').setLevel(logging.WARNING)
    logging.getLogger('socketio').setLevel(logging.WARNING)
    logging.getLogger('engineio.server').setLevel(logging.WARNING)
    logging.getLogger('engineio').setLevel(logging.WARNING)
except Exception:
    pass

# reduce noisy socket/engineio logs

    
# Configuration options for backend integration:
# Option 1: Explicit Configuration (Always use external backend)
#   export RESCUEBOX_USE_EXTERNAL_BACKEND=true
#   export RESCUEBOX_API_URL=http://localhost:8000
#   python -m frontend.main
#   This skips route integration and uses the external backend.
#
# Option 2: Auto-Detection (Detect if backend is running)
#   export RESCUEBOX_CHECK_EXTERNAL_BACKEND=true
#   export RESCUEBOX_API_URL=http://localhost:8000
#   python -m frontend.main
#   This checks if a backend is running at the configured URL and skips
#   integration if detected.

# Import backend routes
try:
    from rb.api import routes
    from fastapi.exceptions import RequestValidationError
    from fastapi import Request, status, HTTPException
    
    BACKEND_AVAILABLE = True
    logger.info("Backend routes imported successfully")
except ImportError as e:
    BACKEND_AVAILABLE = False
    logger.warning("Backend routes not available: %s. Running frontend only.", e)


def check_backend_running(backend_url: str = "http://localhost:8000", timeout: float = 1.0) -> bool:
    """
    Check if a backend server is already running.
    
    Args:
        backend_url: URL of the backend server to check
        timeout: Timeout in seconds for the check
        
    Returns:
        True if backend is running, False otherwise
    """
    try:
        import httpx
        response = httpx.get(f"{backend_url}/probes/liveness/", timeout=timeout)
        return response.status_code == 200
    except Exception:
        return False


def setup_backend_routes(use_external_backend: bool = False):
    """
    Integrate backend FastAPI routes into NiceGUI's FastAPI app.
    
    NiceGUI is built on FastAPI, so we can access its underlying FastAPI app
    via `app` (which is `nicegui.app`) and include backend routes directly.
    
    This creates a unified server where:
    - Backend API routes are available at root (e.g., /models, /probes)
    - Frontend UI routes are available via NiceGUI (e.g., /, /chatbot, /models-page)
    
    Args:
        use_external_backend: If True, skip route integration and use external backend
                              (frontend will use API_BASE_URL from config to connect)
    """
    if not BACKEND_AVAILABLE:
        logger.warning("Skipping backend route integration - backend not available")
        return
    
    # Check if external backend should be used (explicitly configured)
    use_external = use_external_backend or os.getenv('RESCUEBOX_USE_EXTERNAL_BACKEND', '').lower() == 'true'
    if use_external:
        logger.info("Using external backend (route integration skipped)")
        logger.info("Frontend will connect to backend at: %s", API_BASE_URL)
        return
    
    # Optionally auto-detect if external backend is running and skip integration
    check_external = os.getenv('RESCUEBOX_CHECK_EXTERNAL_BACKEND', 'false').lower() == 'true'
    if check_external:
        external_backend_url = API_BASE_URL
        if check_backend_running(external_backend_url):
            logger.info("External backend detected at %s - skipping route integration", external_backend_url)
            logger.info("Frontend will connect to external backend instead of integrated routes")
            return
    
    logger.info("Integrating backend FastAPI routes into NiceGUI app")
    
    # Access NiceGUI's underlying FastAPI app
    # nicegui.app is the FastAPI application instance
    fastapi_app = app
    
    # Add CORS middleware if not already present
    # (Backend may have added it, but ensure it's there)
    from fastapi.middleware.cors import CORSMiddleware
    cors_exists = any(
        isinstance(middleware, CORSMiddleware) 
        for middleware in fastapi_app.user_middleware
    )
    if not cors_exists:
        fastapi_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info("Added CORS middleware")
    
    # Add backend exception handler
    @fastapi_app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_request: Request, exc: RequestValidationError):
        """Response handler for all plugin input validation errors"""
        error_msg = str(exc)
        for e in exc.errors():
            error_msg = e.get("msg")
        
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": f"{error_msg}"},
        )
    
    # Include backend routers
    # Note: We include routes without prefix so they're at root level
    # FIX: Use /api prefix for all backend routes to avoid collisions with NiceGUI UI routes
    # and to match the API_BASE_URL configuration.
    fastapi_app.include_router(routes.probes_router, prefix="/api/probes")
    fastapi_app.include_router(routes.cli_to_api_router, prefix="/api")
    fastapi_app.include_router(routes.models_router, prefix="/api")
    
    # Don't include ui_router as it conflicts with NiceGUI's routing
    # The backend's ui_router is for the old web UI template, not needed with NiceGUI
    # fastapi_app.include_router(routes.ui_router)  # Excluded - conflicts with NiceGUI root route
    
    logger.info("Backend routes integrated successfully")
    logger.info("Backend API available at: /models, /probes, /{endpoint}/*, etc.")


async def prefetch_and_cache_models():
    """
    Fetches models from the backend on startup and caches them.
    This runs in an executor to avoid deadlocking the main server thread.
    """
    logger.info("Attempting to pre-fetch and cache models on application startup...")
    loop = asyncio.get_event_loop()

    def fetch_sync():
        """Synchronous fetch function to run in an executor."""
        try:
            with httpx.Client(base_url=BACKEND_URL, timeout=API_TIMEOUT) as client:
                # Update to use the new /api prefix
                response = client.get('/api/models')
                response.raise_for_status()

                # Check content type
                content_type = response.headers.get('content-type', '').lower()
                logger.debug(f"Models API response status: {response.status_code}")
                logger.debug(f"Models API response content type: {content_type}")
                logger.debug(f"Models API response content length: {len(response.content)}")

                # Check if response is JSON
                if 'application/json' not in content_type:
                    logger.warning(f"Models API returned non-JSON content type: {content_type}")
                    if response.content:
                        logger.warning(f"Response content preview: {response.content[:200]}...")
                    return None

                # Check if response has content
                if not response.content.strip():
                    logger.warning("Models API returned empty response")
                    return None

                # Try to parse JSON
                try:
                    return response.json()
                except ValueError as json_error:
                    logger.error(f"Failed to parse JSON response: {json_error}")
                    logger.error(f"Raw response content: {response.content[:500]}...")
                    return None

        except Exception as e:
            logger.error(f"Synchronous fetch in executor failed: {e}")
            return None

    try:
        models_data = await loop.run_in_executor(None, fetch_sync)
        if models_data:
            logger.info(f"Successfully pre-fetched {len(models_data)} models from the backend.")
            # Cache the fetched models into the database.
            await cache_models(models_data)
        else:
            logger.warning("Pre-fetching models returned no data. Skipping cache update.")
    except Exception as e:
        logger.error(f"Failed to pre-fetch models during startup: {e}")

# Note: setup_backend_routes() is called in __main__ block before ui.run()
# This ensures NiceGUI's app is ready when we integrate backend routes


@ui.page('/')
async def index():
    """
    Main dashboard/home page route handler.
    
    This is the landing page for the RescueBox Desktop application. It provides
    quick access to major features through action buttons.
    
    Page structure:
    1. Navigation bar (created via create_navbar())
    2. Welcome message and description
    3. Action buttons for quick navigation
    
    Action buttons:
    - Browse Models: Navigate to models listing page
    - Open Assistant: Navigate to chatbot interface
    - View Jobs: Navigate to jobs listing page
    
    Routing:
    - This function is decorated with @ui.page('/') making it the root route
    - NiceGUI automatically handles routing when users navigate to '/'
    - Backend API routes are also available at root level (e.g., /models)
    
    Returns:
        None: This function builds the UI directly and doesn't return a value
    
    Tips:
    - Use ui.open() for programmatic navigation instead of manual URL changes
    - The container classes ensure responsive centering and padding
    - Button click handlers use lambda for simple inline callbacks
    - For more complex navigation logic, define separate handler functions
    """
    logger.info("Rendering main dashboard page (index route)")
    
    # Apply saved theme preference
    from frontend.utils.theme import apply_saved_theme
    apply_saved_theme()
    logger.debug("Theme preference applied")
    
    # Inject global CSS to shrink the navbar and general UI elements
    ui.add_head_html('''
        <style>
            .q-header { min-height: 12px !important; }
            .q-toolbar { min-height: 12px !important; padding: 0 8px !important; }
            .q-toolbar__title { font-size: 0.85rem !important; min-height: unset !important; line-height: 32px !important; }
            .q-btn { font-size: 0.7rem !important; padding: 2px 6px !important; min-height: unset !important; }
            body { font-size: 0.8rem !important; }
        </style>
    ''')

    create_navbar()
    logger.debug("Navigation bar added to page")
    
    with ui.column().classes('container mx-auto p-8'):
        logger.debug("Creating main content container")
        ui.label(UI_TITLES['home']).classes('text-4xl font-bold mb-4')
        ui.label(UI_TITLES['home_subtitle']).classes('text-xl text-gray-600')
        
        with ui.row().classes('gap-4 mt-8'):
            logger.debug("Creating action buttons")
            
            # Browse Models button
            ui.button(
                UI_BUTTONS['browse_models'],
                on_click=lambda: ui.navigate.to(NAV_LINKS['models'])
            ).classes('bg-blue-600 text-white px-6 py-3')
            logger.debug("Browse Models button created")
            
            # Open Assistant button
            ui.button(
                UI_BUTTONS['open_assistant'],
                on_click=lambda: ui.navigate.to(NAV_LINKS['chatbot'])
            ).classes('bg-green-600 text-white px-6 py-3')
            logger.debug("Open Assistant button created")
    
    logger.info("Main dashboard page rendered successfully")


if __name__ in {"__main__", "__mp_main__"}:
    logger.info("Starting unified %s application", APP_TITLE)
    logger.info("Server will be available at http://localhost:%s", APP_PORT)
    
    # Initialize the database before starting the server
    init_db()
    
    # Setup backend routes integration before starting the server
    setup_backend_routes()
    logger.info("Backend API routes integrated: %s", BACKEND_AVAILABLE)

    # Serve demo PDFs at /demo/...
    demo_dir = Path(__file__).parent / 'demo'
    if demo_dir.exists():
        app.add_static_files(url_path='/demo', local_directory=str(demo_dir))
        logger.info("Demo PDFs served at /demo/")
    
    # Register the startup handler. This is the compatible way for older NiceGUI versions.
    app.on_startup(prefetch_and_cache_models)

    # Add global error handling for unhandled exceptions
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Global exception handler for unhandled errors."""
        logger.critical("Unhandled exception in NiceGUI application: %s", str(exc))
        logger.critical("Exception type: %s", type(exc).__name__)
        import traceback
        logger.critical("Global exception traceback: %s", traceback.format_exc())

        # Return a user-friendly error page
        return ui.html("""
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
                .reload-btn { background: #3b82f6; color: white; padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; display: inline-block; }
                .reload-btn:hover { background: #2563eb; }
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
        """, sanitize=False)

    # Release demo folder when client is deleted (browser closed) so it can be reused
    @app.on_delete
    async def _on_client_delete(client: Client):
        from frontend.utils.nicegui_storage import release_demo_folder_for_client
        release_demo_folder_for_client(client)

    # Start the unified server
    # This runs both NiceGUI frontend and backend API on the same port
    ui.run(
        title=APP_TITLE,
        port=APP_PORT,
        dark=APP_DARK_MODE,
        favicon=APP_FAVICON,
        show=APP_SHOW_BROWSER,
        # Reconnect timeout: 1 hour keeps demo folder for entire demo (no release on brief disconnect)
        reconnect_timeout=RECONNECT_TIMEOUT,
        # Add a secret key for user-specific storage (e.g., chat history)
        # This should be a long, random string in a real application
        storage_secret='REPLACE_WITH_A_REAL_SECRET_KEY',
        reload=False
    )
