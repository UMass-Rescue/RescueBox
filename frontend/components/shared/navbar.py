"""
Navigation Bar Component

This module provides the main navigation bar component used across all pages
in the RescueBox Desktop application. The navbar provides consistent navigation
and branding throughout the application.

Key features:
- Sticky positioning (stays visible when scrolling)
- Responsive layout
- Accessible navigation links
- Consistent branding
"""

import logging
from nicegui import ui

from frontend.config import APP_TITLE, APP_VERSION

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_navbar():
    """
    Create and render the main navigation bar component.
    
    This function generates a sticky navigation bar that appears at the top
    of every page. It includes the RescueBox branding and navigation links
    to major sections of the application.
    
    
    Navigation Links:
    - Models: Browse available ML models (/models)
    - Jobs: View job history and status (/jobs)
    - Assistant: Access chatbot interface (/chatbot)
    - Logs: View application logs (/logs)
    
    Returns:
        None: This function directly modifies the UI context
    
    Tips:
    - The navbar is sticky, so it will remain visible when scrolling
    - Links use hover effects (hover:underline, hover:bg-blue-700)
    - Brand row (logo + title) is left-aligned; links use a tight row with ``flex-1 justify-end``
    - Use consistent styling classes for new navigation links
    """
    #logger.info("Creating navigation bar component")
    
    with ui.header(wrap=False).classes(
        'bg-blue-600 text-white shadow-lg sticky top-0 z-50 w-full max-w-[100vw] overflow-hidden'
    ):
        #logger.debug("Header created with sticky positioning and blue theme")

        _logo_px = '11.25rem'
        _logo_style = (
            f'width:{_logo_px};height:{_logo_px};max-width:{_logo_px};max-height:{_logo_px};'
            'min-width:0;min-height:0;display:block;object-fit:contain;'
        )

        _link_cls = (
            'text-white hover:underline px-1 py-0 sm:px-1.5 sm:py-0.5 rounded '
            'hover:bg-blue-700 text-xs whitespace-nowrap leading-none'
        )

        with ui.row().classes(
            'w-full min-w-0 min-h-12 h-auto sm:h-14 px-2 sm:px-3 py-0 items-center gap-2 sm:gap-3 '
            'box-border flex-wrap sm:flex-nowrap justify-start'
        ):
            #logger.debug("Creating navbar container with responsive layout")

            with ui.row().classes('shrink-0 items-center gap-2 min-w-0'):
                (
                    ui.element('img')
                    .props(f'src=/icons/rb.webp alt="{APP_TITLE}"')
                    .classes('shrink-0 object-contain')
                    .style(_logo_style)
                )
                with ui.row().classes('items-baseline gap-2 min-w-0'):
                    ui.label(APP_TITLE).classes(
                        'text-sm sm:text-base font-bold leading-tight text-white '
                        'truncate min-w-0 max-w-[10rem] sm:max-w-[14rem]'
                    )
                    ui.label(APP_VERSION).classes(
                        'text-xs sm:text-sm font-medium text-blue-100 shrink-0'
                    )

            with ui.row().classes('min-w-0 flex-1 justify-end items-center'):
                with ui.row().classes(
                    'inline-flex flex-wrap items-center justify-end gap-x-0.5 gap-y-0 '
                    'max-w-full py-0'
                ):
                    #logger.debug("Creating navigation links row")

                    ui.link('Browse Plugins', '/models').classes(_link_cls)
                    ui.link('Assistant', '/chatbot').classes(_link_cls)
                    ui.link('Jobs', '/jobs').classes(_link_cls)
                    ui.link('Logs', '/logs').classes(_link_cls)
                    ui.link('Demo', '/demo').classes(_link_cls)

                # Session display removed for demo safety (avoids accidental user actions)

                # Clear Session button removed to avoid accidental data loss
    
 