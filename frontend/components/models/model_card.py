"""
Model Card Component

This module provides the render_model_card function for displaying ML model
information in a card-styled row format. The card shows model metadata, status,
and action buttons.
"""

import logging
from nicegui import ui
from typing import Dict, Optional, Callable

from frontend.constants import UI_BUTTONS

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_model_card(
    container, 
    model: Dict, 
    is_online: bool, 
    on_inspect: Optional[Callable] = None,
    on_connect: Optional[Callable] = None
):
    """
    Render a model card in card-styled row format.
    
    This function creates a visually appealing card component displaying model
    information including name, version, author, GPU requirements, and status.
    The card includes README (plugin details) and, when offline, Connect.
    
    Design Features:
    - Card shell: Zinc-tint surface + Medium Gray #505759 border (see ``.rb-models-plugin-card`` in ``ui_readability_css``)
    - Status indicator: Visual dot (●) showing online/offline status (green/red text)
    - Dynamic icon: Icon changes based on model category (image/audio/text)
    - Hover effects: Shadow appears on hover for better UX
    - Responsive layout: Flex layout adapts to container width
    
    Args:
        container: NiceGUI container element to add the card to (e.g., ui.column())
        model (Dict): Model data dictionary containing:
            - 'uid' (str): Unique identifier
            - 'name' (str): Model display name
            - 'version' (str): Model version
            - 'author' (str): Model author/creator
            - 'gpu' (bool): Whether GPU is required
            - 'category' (str, optional): Model category
        is_online (bool): Whether the model server is currently online/available
        on_inspect (Optional[Callable]): Callback when the README button is clicked.
            Receives model UID as argument: on_inspect(model['uid'])
        on_connect (Optional[Callable]): Callback function called when Connect button is clicked.
            Only shown if model is offline. Receives model UID: on_connect(model['uid'])
    
    Returns:
        None: This function modifies the container directly and doesn't return a value
    
    Examples:
        >>> render_model_card(
        ...     container=my_container,
        ...     model={'uid': 'model-123', 'name': 'Face Detection', 'version': '1.0', ...},
        ...     is_online=True,
        ...     on_inspect=lambda uid: ui.navigate.to(f'/models/{uid}')
        ... )
    
    Tips:
    - Use different callback functions for different actions
    - Online/offline is shown in the status row; card chrome is fixed brand grays
    - GPU requirement badge is only shown if model['gpu'] is True
    - Icons are selected based on model name keywords
    - Card uses Tailwind CSS classes for styling
    """
    logger.info("Rendering model card for model: %s (UID: %s)", model.get('name', 'Unknown'), model.get('uid', 'N/A'))
    logger.info("Model online status: %s", is_online)
    
    status_indicator = '●' if is_online else '○'
    status_text = 'Online' if is_online else 'Offline'
    logger.info("Status indicator: %s, status text: %s", status_indicator, status_text)

    with container:
        logger.debug("Creating model card container")
        with ui.card().classes(
            'rb-models-plugin-card w-full p-6 hover:shadow-lg transition-shadow'
        ):
            with ui.row().classes('items-center justify-between w-full'):
                # Left section - Model info
                with ui.column().classes('flex-1'):
                    # Icon and name row
                    with ui.row().classes('items-center gap-3'):
                        # Model icon based on category (you can enhance this)
                        icon = 'image' if 'image' in model.get('name', '').lower() else \
                               'audiotrack' if 'audio' in model.get('name', '').lower() else \
                               'description' if 'text' in model.get('name', '').lower() else 'category'
                        logger.debug("Selected icon: %s for model category", icon)
                        #ui.icon(icon, size='lg').classes('text-indigo-600')
                        ui.label(model['name']).classes('text-2xl font-bold')
                        logger.debug("Model name label added: %s", model['name'])
                    
                    # Version, author, GPU info
                    with ui.row().classes('gap-4 mt-2 text-sm text-zinc-600 items-center'):
                        ui.label(f"v{model['version']}")
                        ui.label('•')
                        ui.label(model.get('author', 'Unknown'))
                        if model.get('gpu'):
                            ui.badge('GPU Required', color="black").classes('text-xs')
                
                # Right section - Status and actions
                with ui.column().classes('items-end gap-2'):
                    # Status badge
                 
                    
                    # Action buttons
                    with ui.row().classes('gap-2'):
                        logger.debug("Creating action buttons")
                        if on_inspect:
                            ui.button(
                                UI_BUTTONS['plugin_readme'],
                                on_click=lambda m=model: on_inspect(m['uid']) if on_inspect else None
                            ).classes('rb-brand-primary text-white')
                            logger.debug("README button added")
                        
                        if not is_online and on_connect:
                            ui.button(
                                '🔌 Connect',
                                on_click=lambda m=model: on_connect(m['uid']) if on_connect else None
                            ).classes('bg-zinc-600 text-white')
                            logger.debug("Connect button added (model is offline)")
    
    logger.info("Model card rendered successfully")