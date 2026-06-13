"""
Models Page

This module provides the ModelsPage class for displaying available ML models,
their server statuses, and actions (inspect, run, connect).
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException
from nicegui import ui
from rb.api.models import AppMetadata

from frontend.api_client import api_client
from frontend.chatbot.config import ToolRegistry
from frontend.components.models import render_model_info_card, render_models_list
from frontend.components.shared import render_page_header
from frontend.constants import (
    ERROR_MESSAGES,
    NAV_LINKS,
    STATUS_MESSAGES,
    UI_BUTTONS,
    UI_TITLES,
)
from frontend.database import get_cached_model_by_uid, get_cached_models
from frontend.pages.page_shell import begin_demo_session_page
from frontend.utils import handle_api_error
from frontend.utils.backend import prefetch_and_cache_models
from frontend.components.ui_exceptions import UI_RENDER_ERRORS

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def _sort_models_by_tool_menu(models: List[Dict]) -> List[Dict]:
    """Order like chatbot TOOL_MENU; unknown plugins (e.g. future additions) sort last by uid."""
    rank = {uid: i for i, uid in enumerate(ToolRegistry.ordered_plugin_uids())}
    return sorted(
        models,
        key=lambda m: (rank.get(m.get("uid") or "", 10_000), m.get("uid") or ""),
    )


def _models_header_buttons(refresh_cb):
    ui.button(
        UI_BUTTONS["open_assistant"],
        on_click=lambda: ui.navigate.to(NAV_LINKS["chatbot"]),
    ).classes("rb-brand-primary text-white rounded-xl")
    ui.button(UI_BUTTONS["refresh"], on_click=refresh_cb).classes(
        "rb-brand-primary text-white rounded-xl"
    )


def _render_models_header(refresh_cb) -> None:
    try:
        render_page_header(
            UI_TITLES["models"],
            actions_callable=lambda: _models_header_buttons(refresh_cb),
        )
    except UI_RENDER_ERRORS:
        with ui.row().classes("items-center justify-between w-full mb-6"):
            ui.label(UI_TITLES["models"]).classes("text-4xl font-bold")
            with ui.row().classes("gap-2"):
                _models_header_buttons(refresh_cb)


def _clear_loading_spinner(loading) -> None:
    if not loading:
        return
    try:
        loading.delete()
    except (ValueError, RuntimeError):
        pass


async def _load_cached_models_with_prefetch() -> List[Dict]:
    models_data = await get_cached_models()
    if models_data:
        return models_data
    try:
        await prefetch_and_cache_models()
        models_data = await get_cached_models()
    except UI_RENDER_ERRORS as e:
        logger.warning("Failed to auto-prefetch models: %s", e)
    return models_data or []


def extract_model_info(model_info, model_info_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Extract model metadata from AppMetadata or a plain dict."""
    if model_info:
        return {
            "info": model_info.info,
            "version": model_info.version,
            "author": model_info.author,
            "name": getattr(model_info, "name", "Unknown"),
            "description": getattr(model_info, "description", ""),
        }
    return {
        "info": model_info_dict.get("info", "No documentation available."),
        "version": model_info_dict.get("version", "N/A"),
        "author": model_info_dict.get("author", "N/A"),
        "name": model_info_dict.get("name", "Unknown"),
        "description": model_info_dict.get("description", ""),
    }


def _parse_app_metadata(model_info_dict: Dict[str, Any]):
    try:
        return AppMetadata(**model_info_dict)
    except UI_RENDER_ERRORS as e:
        logger.debug(
            "Model info does not match AppMetadata format: %s, using dict directly",
            e,
        )
        return None


async def _fetch_server_status(model_uid: str) -> str:
    try:
        status_response = await api_client.get(
            f"/servers/{model_uid}/status", timeout=5.0
        )
        if status_response.status_code == 200:
            return STATUS_MESSAGES["online"]
    except UI_RENDER_ERRORS as e:
        logger.warning("Error checking server status: %s, defaulting to Offline", e)
    return STATUS_MESSAGES["offline"]


async def _load_model_details_context(
    model_uid: str,
) -> Optional[Tuple[Any, Dict[str, Any], str]]:
    model_info_dict = await get_cached_model_by_uid(model_uid)
    if not model_info_dict:
        raise HTTPException(
            status_code=404, detail=f"Model {model_uid} not found in cache."
        )
    model_info = _parse_app_metadata(model_info_dict)
    server_status = await _fetch_server_status(model_uid)
    return model_info, model_info_dict, server_status


class ModelsPage:
    """Models listing page. Displays all available ML models with their server statuses, allowing users"""

    def __init__(self):
        """Initialize ModelsPage. Sets up API client and initializes empty state containers."""
        logger.info("Initializing ModelsPage")
        self.api_client = api_client
        self.models: List[Dict] = []
        self.server_statuses: Dict[str, str] = {}
        self.models_container = None
        self.loading = None
        logger.debug("ModelsPage initialized successfully")

    async def render(self):
        """Render the models page UI. Creates the page layout with header, refresh button, loading indicator,"""
        logger.debug("Rendering models page")
        try:
            with ui.column().classes(
                "container mx-auto px-4 sm:px-8 py-8 w-full max-w-6xl pb-16"
            ):
                logger.debug("Creating page header")
                _render_models_header(self.refresh_models)

                logger.debug("Creating models container")
                self.models_container = ui.column().classes("space-y-4 w-full")
                with self.models_container:
                    self.loading = ui.spinner(size="lg")
                    await self.load_models()

            logger.info("Models page rendered successfully")
        except UI_RENDER_ERRORS as e:
            logger.error("Error rendering models page: %s", e, exc_info=True)
            ui.label(f"Error rendering models page: {str(e)}").classes("text-red-600")

    def cached_model_count(self) -> int:
        """Number of models currently loaded in memory."""
        return len(self.models)

    async def refresh_models(self):
        """Fetch fresh model metadata from API, save to database cache, and reload."""
        logger.info("Manual refresh triggered. Fetching models from backend API...")
        self.models_container.clear()
        with self.models_container:
            self.loading = ui.spinner(size="lg")
        try:
            await prefetch_and_cache_models()
        except UI_RENDER_ERRORS as e:
            logger.warning("Failed to prefetch models during manual refresh: %s", e)
        await self.load_models()

    async def load_models(self):
        """Load models and server statuses from the API/cache."""
        logger.info("Loading models and server statuses")
        try:
            logger.info("Fetching models from the database cache.")
            models_data = await _load_cached_models_with_prefetch()

            if not models_data:
                logger.warning(
                    "No models found in database cache after prefetch attempt."
                )
                self.models = []
                self.server_statuses = {}
                self.loading = None
                await self.render_models()
                return

            logger.info("Loaded %d models", len(models_data))
            self.models = _sort_models_by_tool_menu(models_data)
            for model in self.models:
                logger.info("Fetched models %s", model["uid"])
            self.server_statuses = {model["uid"]: "Online" for model in models_data}

            self.loading = None
            await self.render_models()
            logger.info("Models loaded and rendered successfully")

        except UI_RENDER_ERRORS as e:
            await handle_api_error(
                e,
                str("Error loading models " + str(ERROR_MESSAGES["load_models"])),
                show_to_user=True,
            )
        finally:
            _clear_loading_spinner(self.loading)
            self.loading = None

    async def render_models(self):
        """Render model cards in the UI. Separates models into online and offline categories and renders"""
        logger.info("Rendering models in UI")
        self.models_container.clear()

        with self.models_container:
            online_models = [
                m for m in self.models if self.server_statuses.get(m["uid"]) == "Online"
            ]
            offline_models = [
                m for m in self.models if self.server_statuses.get(m["uid"]) != "Online"
            ]
            logger.debug(
                "Models breakdown: %d online, %d offline",
                len(online_models),
                len(offline_models),
            )

            try:
                render_models_list(
                    self.models_container,
                    self.models,
                    self.server_statuses,
                    on_inspect=lambda uid: ui.navigate.to(f"/models/{uid}/details"),
                    on_connect=lambda uid: ui.navigate.to(f"/registration/{uid}"),
                )
            except UI_RENDER_ERRORS as e:
                logger.exception("Failed to render models via component: %s", e)

        logger.info("Models rendered successfully")


@ui.page("/models", response_timeout=10)
async def models_page():
    """Page route handler for /models. Creates the models page with navigation bar and renders the ModelsPage."""
    logger.info("Models page route accessed")
    try:
        if not begin_demo_session_page():
            return
        models_page_instance = ModelsPage()
        logger.info("Models models_page_instance created")
        await models_page_instance.render()
        logger.info("Models page render completed")
    except UI_RENDER_ERRORS as e:
        logger.error("Error in models page: %s", e, exc_info=True)
        ui.label(f"Error loading models page: {str(e)}").classes("text-red-600")


@ui.page("/models/{model_uid}/details")
async def model_details_page(model_uid: str):
    """Page route handler for model details. Displays model documentation, metadata, version information, and server"""
    logger.info("Model details page accessed for model: %s", model_uid)
    if not begin_demo_session_page():
        return

    try:
        logger.debug("Fetching model metadata from cache for model_uid: %s", model_uid)
        bundle = await _load_model_details_context(model_uid)
        logger.info("Model metadata loaded successfully from cache")
    except UI_RENDER_ERRORS as e:
        await handle_api_error(
            e,
            f"Error loading model {model_uid} {ERROR_MESSAGES['not_found']}",
            show_to_user=True,
        )
        return

    model_info, model_info_dict, server_status = bundle

    with ui.column().classes(
        "container mx-auto px-4 sm:px-8 py-8 w-full max-w-6xl pb-16"
    ):
        with ui.row().classes("gap-6 w-full"):
            with ui.column().classes("flex-1"):
                ui.label(model_uid + " Model Documentation").classes(
                    "text-2xl font-bold mb-4"
                )

                model_data = extract_model_info(model_info, model_info_dict)
                info_text = model_data["info"]
                _ = model_data["version"]
                _ = model_data["author"]

                with ui.card().classes("bg-white p-6"):
                    ui.markdown(info_text).classes("prose max-w-none")

            with ui.column().classes("w-80"):
                try:
                    render_model_info_card(
                        ui.column(),
                        model_info if model_info else {},
                        model_info_dict,
                        server_status,
                    )
                except UI_RENDER_ERRORS as e:
                    logger.exception(
                        "Failed to render model info card component: %s", e
                    )

    logger.info("Model details page rendered successfully")
