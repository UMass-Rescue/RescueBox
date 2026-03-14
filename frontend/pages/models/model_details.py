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
from frontend.pages.models.models_utils import setup_models_path, extract_model_info
setup_models_path()
from frontend.database import get_cached_model_by_uid
from rb.api.models import AppMetadata
from frontend.components.shared import create_navbar
from frontend.api_client import api_client
from frontend.constants import UI_TITLES, STATUS_MESSAGES, ERROR_MESSAGES
from frontend.utils.error_handling import handle_api_error
from fastapi import HTTPException

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@ui.page('/models/{model_uid}/details')
async def model_details_page(model_uid: str):
    """
    Page route handler for model details.
    
    Displays model documentation, metadata, version information, and server
    status. Uses two-column layout with documentation on left and metadata on right.
    
    Args:
        model_uid (str): Model unique identifier
    
    Returns:
        None: Page is rendered directly
    """
    logger.info("Model details page accessed for model: %s", model_uid)
    from frontend.utils.theme import apply_saved_theme
    apply_saved_theme()
    create_navbar()
    
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
        await handle_api_error(e, f"Error loading model {model_uid}", user_message=ERROR_MESSAGES['not_found'])
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
                    from frontend.components.models.model_info_card import render_model_info_card
                    render_model_info_card(ui.column(), model_info if model_info else {}, model_info_dict, server_status)
                except Exception as e:
                    logger.exception("Failed to render model info card component: %s", e)
                    with ui.card().classes('bg-sky-50 border border-sky-300 p-6 sticky top-24'):
                        ui.label('Model Information').classes('text-xl font-bold mb-4')
                        # Fallback inline rendering (minimal)
                        ui.label(f'Author: {author}').classes('text-sm')
                        ui.label(f'Status: {server_status}').classes('text-sm')
    
    logger.info("Model details page rendered successfully")