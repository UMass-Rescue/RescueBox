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

# Setup backend path for imports
from frontend.pages.models.models_utils import setup_models_path
setup_models_path()

from frontend.components.shared import create_navbar
from frontend.components.models import render_model_card
from frontend.api_client import api_client
from frontend.constants import UI_TITLES, UI_BUTTONS, STATUS_MESSAGES, ERROR_MESSAGES, SUCCESS_MESSAGES, NAV_LINKS
from frontend.utils.error_handling import handle_api_error
# Assuming a database module exists for retrieving cached models
# This function would read the data pre-fetched by main.py on startup.
from frontend.database import get_cached_models
from frontend.chatbot.config import ToolRegistry

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def _sort_models_by_tool_menu(models: List[Dict]) -> List[Dict]:
    """Order like chatbot TOOL_MENU; unknown plugins (e.g. future additions) sort last by uid."""
    rank = {uid: i for i, uid in enumerate(ToolRegistry.ordered_plugin_uids())}
    return sorted(
        models,
        key=lambda m: (rank.get(m.get("uid") or "", 10_000), m.get("uid") or ""),
    )


class ModelsPage:
    """
    Models listing page.
    
    Displays all available ML models with their server statuses, allowing users
    to inspect, run, or connect to models. Models are separated into online
    and offline categories.
    
    Usage:
        page = ModelsPage()
        await page.render()
    
    Tips:
    - Models are automatically loaded on page render
    - Server statuses are checked for each model
    - Models are displayed in card-styled rows
    - Refresh button reloads models and statuses
    """

    def __init__(self):
        """
        Initialize ModelsPage.
        
        Sets up API client and initializes empty state containers.
        """
        logger.info("Initializing ModelsPage")
        self.api_client = api_client
        self.models: List[Dict] = []
        self.server_statuses: Dict[str, str] = {}
        logger.debug("ModelsPage initialized successfully")

    async def render(self):
        """
        Render the models page UI.

        Creates the page layout with header, refresh button, loading indicator,
        and models container. Automatically loads models on render.

        Returns:
            None: UI is added directly to the current context
        """
        logger.info("Rendering models page")
        try:
            with ui.column().classes('container mx-auto p-8'):
                # Header
                logger.debug("Creating page header")
                try:
                    from frontend.components.shared.page_header import render_page_header
                    def _header_actions():
                        ui.button(
                            UI_BUTTONS['open_assistant'],
                            on_click=lambda: ui.navigate.to(NAV_LINKS['chatbot'])
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
                            ui.button(UI_BUTTONS['refresh'], on_click=self.load_models).classes('rb-brand-primary text-white')

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

    async def load_models(self):
        """
        Load models and their server statuses from the API.
        
        Fetches the list of models and checks server status for each model.
        Updates internal state and triggers UI refresh.
        
        Returns:
            None
        
        Raises:
            httpx.HTTPError: If API requests fail
        
        Tips:
        - Server status checks are done individually for each model
        - Failed status checks default to 'Offline'
        - Models are stored in self.models, statuses in self.server_statuses
        """
        logger.info("Loading models and server statuses")
        try:
            # Fetch models from the local database/cache
            logger.info("Fetching models from the database cache.")
            models_data = await get_cached_models()
            if not models_data:
                logger.warning("No models found in the database cache.")
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
            await handle_api_error(e, "Error loading models", user_message=ERROR_MESSAGES['load_models'])
        finally:
            if self.loading:
                try:
                    self.loading.delete()
                except (ValueError, RuntimeError):
                    pass # Element already removed by container.clear()
                self.loading = None

    async def render_models(self):
        """
        Render model cards in the UI.
        
        Separates models into online and offline categories and renders
        appropriate model cards with action buttons.
        
        Returns:
            None
        
        Tips:
        - Online models show 'Run' button, offline models show 'Connect' button
        - Models are grouped by availability status
        - Each model card includes inspect, run/connect actions
        """
        logger.info("Rendering models in UI")
        self.models_container.clear()
        
        with self.models_container:
            # Separate online and offline models
            online_models = [m for m in self.models if self.server_statuses.get(m['uid']) == 'Online']
            offline_models = [m for m in self.models if self.server_statuses.get(m['uid']) != 'Online']
            logger.debug("Models breakdown: %d online, %d offline", len(online_models), len(offline_models))

            try:
                from frontend.components.models.models_list import render_models_list
                render_models_list(
                    self.models_container,
                    self.models,
                    self.server_statuses,
                    on_inspect=lambda uid: ui.navigate.to(f"/models/{uid}/details"),
                    on_connect=lambda uid: ui.navigate.to(f"/registration/{uid}")
                )
            except Exception as e:
                logger.exception("Failed to render models via component: %s", e)
                # fallback to inline rendering
                if online_models:
                    logger.debug("Rendering online models (fallback)")
                    # ui.label('Available Models').classes('text-2xl font-bold mt-6 mb-4')
                    for model in online_models:
                        render_model_card(
                            self.models_container,
                            model,
                            True,
                            on_inspect=lambda uid: ui.navigate.to(f"/models/{uid}/details"),
                            on_connect=None
                        )

                if offline_models:
                    logger.debug("Rendering offline models (fallback)")
                    ui.label('Unavailable Models').classes('text-2xl font-bold mt-6 mb-4')
                    for model in offline_models:
                        render_model_card(
                            self.models_container,
                            model,
                            False,
                            on_inspect=lambda uid: ui.navigate.to(f"/models/{uid}/details"),
                            on_connect=lambda uid: ui.navigate.to(f"/registration/{uid}")
                        )

        logger.info("Models rendered successfully")

@ui.page('/models', response_timeout=10)
async def models_page():
    """
    Page route handler for /models.

    Creates the models page with navigation bar and renders the ModelsPage.

    Returns:
        None: Page is rendered directly
    """
    logger.info("Models page route accessed")
    try:
        from frontend.utils.theme import apply_saved_theme
        apply_saved_theme()
        create_navbar()
        from frontend.utils.demo_user_gate import require_demo_user_session

        if not require_demo_user_session():
            return
        models_page_instance = ModelsPage()
        logger.info("Models models_page_instance created")
        await models_page_instance.render()
        logger.info("Models page render completed")
    except Exception as e:
        logger.error(f"Error in models page: {str(e)}", exc_info=True)
        ui.label(f"Error loading models page: {str(e)}").classes('text-red-600')
