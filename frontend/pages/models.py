import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

"""
Models Page

This module provides the ModelsPage class for displaying available ML models,
their server statuses, and actions (inspect, run, connect).
"""

import logging
from nicegui import ui
import asyncio
import httpx
from typing import List, Dict, Optional

import sys
from pathlib import Path

def setup_models_path():
    """Setup backend path for models module imports."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

setup_models_path()

from frontend.components.shared import create_navbar
from frontend.components.models import render_model_card
from frontend.api_client import api_client
from frontend.constants import UI_TITLES, UI_BUTTONS, STATUS_MESSAGES, ERROR_MESSAGES, SUCCESS_MESSAGES, NAV_LINKS
from frontend.utils import handle_api_error
# Assuming a database module exists for retrieving cached models
# This function would read the data pre-fetched by main.py on startup.
from frontend.database import get_cached_models
from frontend.chatbot.config import ToolRegistry

# Configure logging for this module

logger.setLevel(logging.DEBUG)


def _sort_models_by_tool_menu(models: List[Dict]) -> List[Dict]:
    """Order like chatbot TOOL_MENU; unknown plugins (e.g. future additions) sort last by uid."""
    rank = {uid: i for i, uid in enumerate(ToolRegistry.ordered_plugin_uids())}
    return sorted(
        models,
        key=lambda m: (rank.get(m.get("uid") or "", 10_000), m.get("uid") or ""),
    )


class ModelsPage:
    """Models listing page. Displays all available ML models with their server statuses, allowing users"""

    def __init__(self):
        """Initialize ModelsPage. Sets up API client and initializes empty state containers."""
        logger.info("Initializing ModelsPage")
        self.api_client = api_client
        self.models: List[Dict] = []
        self.server_statuses: Dict[str, str] = {}
        logger.debug("ModelsPage initialized successfully")

    async def render(self):
        """Render the models page UI. Creates the page layout with header, refresh button, loading indicator,"""
        logger.debug("Rendering models page")
        try:
            with ui.column().classes('container mx-auto p-8'):
                # Header
                logger.debug("Creating page header")
                try:
                    from frontend.components.shared import render_page_header
                    def _header_actions():
                        ui.button(
                            UI_BUTTONS['open_assistant'],
                            on_click=lambda: ui.navigate.to(NAV_LINKS['chatbot'])
                        ).classes('rb-brand-primary text-white rounded-xl')
                        ui.button(
                            UI_BUTTONS['refresh'],
                            on_click=self.refresh_models
                        ).classes('rb-brand-primary text-white rounded-xl')
                       

                    render_page_header(UI_TITLES['models'], actions_callable=_header_actions)
                except Exception:
                    with ui.row().classes('items-center justify-between w-full mb-6'):
                        ui.label(UI_TITLES['models']).classes('text-4xl font-bold')
                        with ui.row().classes('gap-2'):
                            ui.button(
                                UI_BUTTONS['open_assistant'],
                                on_click=lambda: ui.navigate.to(NAV_LINKS['chatbot'])
                            ).classes('rb-brand-primary text-white rounded-xl')
                            ui.button(UI_BUTTONS['refresh'], on_click=self.refresh_models).classes('rb-brand-primary text-white')

                # Loading indicator
                logger.debug("Creating models container")
                self.models_container = ui.column().classes('space-y-4 w-full')
                with self.models_container:
                    self.loading = ui.spinner(size='lg')
                    await self.load_models()

            logger.info("Models page rendered successfully")
        except Exception as e:
            logger.error(f"Error rendering models page: {str(e)}", exc_info=True)
            ui.label(f"Error rendering models page: {str(e)}").classes('text-red-600')

    async def refresh_models(self):
        """Fetch fresh model metadata from API, save to database cache, and reload."""
        logger.info("Manual refresh triggered. Fetching models from backend API...")
        self.models_container.clear()
        with self.models_container:
            self.loading = ui.spinner(size='lg')
        try:
            from frontend.utils.backend import prefetch_and_cache_models
            await prefetch_and_cache_models()
        except Exception as e:
            logger.warning("Failed to prefetch models during manual refresh: %s", e)
        await self.load_models()

    async def load_models(self):
        """Load models and their server statuses from the API. Fetches the list of models and checks server status for each model."""
        logger.info("Loading models and server statuses")
        try:
            # Fetch models from the local database/cache
            logger.info("Fetching models from the database cache.")
            models_data = await get_cached_models()
            if not models_data:
                logger.warning("No models found in the database cache. Attempting auto-prefetch.")
                try:
                    from frontend.utils.backend import prefetch_and_cache_models
                    await prefetch_and_cache_models()
                    models_data = await get_cached_models()
                except Exception as e:
                    logger.warning("Failed to auto-prefetch models: %s", e)

            if not models_data:
                logger.warning("No models found in database cache after prefetch attempt.")
                self.models = []
                self.server_statuses = {}
                self.loading = None  # Prevent deletion in finally block
                await self.render_models()
                return

            logger.info("Loaded %d models", len(models_data))

            # Match chatbot tool picker order (TOOL_MENU in config.py)
            self.models = _sort_models_by_tool_menu(models_data)
            for model in self.models:
                logger.info("Fetched models %s", model["uid"] )
            self.server_statuses = {model["uid"]: 'Online' for model in models_data}
            
            # Set to None before rendering because render_models() clears the container
            # which contains the loading spinner.
            self.loading = None
            await self.render_models()
            logger.info("Models loaded and rendered successfully")

        except Exception as e:
            await handle_api_error(e, 
            str("Error loading models " + str(ERROR_MESSAGES['load_models'])), show_to_user=True)
        finally:
            if self.loading:
                try:
                    self.loading.delete()
                except (ValueError, RuntimeError):
                    pass # Element already removed by container.clear()
                self.loading = None

    async def render_models(self):
        """Render model cards in the UI. Separates models into online and offline categories and renders"""
        logger.info("Rendering models in UI")
        self.models_container.clear()
        
        with self.models_container:
            # Separate online and offline models
            online_models = [m for m in self.models if self.server_statuses.get(m['uid']) == 'Online']
            offline_models = [m for m in self.models if self.server_statuses.get(m['uid']) != 'Online']
            logger.debug("Models breakdown: %d online, %d offline", len(online_models), len(offline_models))

            try:
                from frontend.components.models import render_models_list
                render_models_list(
                    self.models_container,
                    self.models,
                    self.server_statuses,
                    on_inspect=lambda uid: ui.navigate.to(f"/models/{uid}/details"),
                    on_connect=lambda uid: ui.navigate.to(f"/registration/{uid}")
                )
            except Exception as e:
                logger.exception("Failed to render models via component: %s", e)

        logger.info("Models rendered successfully")

@ui.page('/models', response_timeout=10)
async def models_page():
    """Page route handler for /models. Creates the models page with navigation bar and renders the ModelsPage."""
    logger.info("Models page route accessed")
    try:
        from frontend.utils import apply_saved_theme
        apply_saved_theme()
        create_navbar()
        from frontend.utils import require_demo_user_session

        if not require_demo_user_session():
            return
        models_page_instance = ModelsPage()
        logger.info("Models models_page_instance created")
        await models_page_instance.render()
        logger.info("Models page render completed")
    except Exception as e:
        logger.error(f"Error in models page: {str(e)}", exc_info=True)
        ui.label(f"Error loading models page: {str(e)}").classes('text-red-600')


"""
Models Utilities

This module provides shared utilities and common setup for the models package.
"""

import logging
from pathlib import Path
import sys
from typing import Dict, Any, Optional



# Configure logging for models package

logger.setLevel(logging.DEBUG)


def extract_model_info(model_info, model_info_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Extract model information from various sources. Provides a standardized way to extract model metadata from AppMetadata objects"""
    if model_info:
        return {
            'info': model_info.info,
            'version': model_info.version,
            'author': model_info.author,
            'name': getattr(model_info, 'name', 'Unknown'),
            'description': getattr(model_info, 'description', ''),
        }
    else:
        return {
            'info': model_info_dict.get('info', 'No documentation available.'),
            'version': model_info_dict.get('version', 'N/A'),
            'author': model_info_dict.get('author', 'N/A'),
            'name': model_info_dict.get('name', 'Unknown'),
            'description': model_info_dict.get('description', ''),
        }


"""
Model Details Page

This module provides the model details page for displaying model documentation,
metadata, version information, and server status.
"""

import logging
from nicegui import ui
from typing import Optional
from datetime import datetime

# Setup backend path for imports

setup_models_path()
from frontend.database import get_cached_model_by_uid
from rb.api.models import AppMetadata
from frontend.components.shared import create_navbar
from frontend.api_client import api_client
from frontend.constants import UI_TITLES, STATUS_MESSAGES, ERROR_MESSAGES
from frontend.utils import handle_api_error
from fastapi import HTTPException

# Configure logging for this module



@ui.page('/models/{model_uid}/details')
async def model_details_page(model_uid: str):
    """Page route handler for model details. Displays model documentation, metadata, version information, and server"""
    logger.info("Model details page accessed for model: %s", model_uid)
    from frontend.utils import apply_saved_theme
    apply_saved_theme()
    create_navbar()
    from frontend.utils import require_demo_user_session

    if not require_demo_user_session():
        return

    # Load model info
    try:
        # Get model metadata from cache
        logger.debug("Fetching model metadata from cache for model_uid: %s", model_uid)
        model_info_dict = await get_cached_model_by_uid(model_uid)
        if not model_info_dict:
            raise HTTPException(status_code=404, detail=f"Model {model_uid} not found in cache.")
        logger.info("Model metadata loaded successfully from cache")
        
        # Validate using AppMetadata (if API returns metadata format)
        try:
            logger.debug("Validating model info using AppMetadata")
            model_info = AppMetadata(**model_info_dict)
            logger.debug("Model info validated as AppMetadata")
        except Exception as e:
            logger.debug("Model info does not match AppMetadata format: %s, using dict directly", str(e))
            # If it doesn't match AppMetadata, use dict directly
            model_info = None
        
        # Get server status
        try:
            logger.debug("Checking server status for model: %s", model_uid)
            status_response = await api_client.get(f'/servers/{model_uid}/status', timeout=5.0)
            server_status = STATUS_MESSAGES['online'] if status_response.status_code == 200 else STATUS_MESSAGES['offline']
            logger.debug("Server status: %s", server_status)
        except Exception as e:
            logger.warning("Error checking server status: %s, defaulting to Offline", str(e))
            server_status = STATUS_MESSAGES['offline']
        
    except Exception as e:
        await handle_api_error(e, 
        f"Error loading model {model_uid} {ERROR_MESSAGES['not_found']}",
        show_to_user=True)
        return
    
    with ui.column().classes('container mx-auto p-8'):
        # Two-column layout
        with ui.row().classes('gap-6 w-full'):
            # Left column - Documentation
            with ui.column().classes('flex-1'):
                ui.label(model_uid + ' Model Documentation').classes('text-2xl font-bold mb-4')
                
                # Render markdown documentation
                model_data = extract_model_info(model_info, model_info_dict)
                info_text = model_data['info']
                version = model_data['version']
                author = model_data['author']
                
                with ui.card().classes('bg-white p-6'):
                    ui.markdown(info_text).classes('prose max-w-none')
            
            # Right column - Model metadata
            # Right column - Model metadata
            with ui.column().classes('w-80'):
                try:
                    from frontend.components.models import render_model_info_card
                    render_model_info_card(ui.column(), model_info if model_info else {}, model_info_dict, server_status)
                except Exception as e:
                    logger.exception("Failed to render model info card component: %s", e)
    
    logger.info("Model details page rendered successfully")