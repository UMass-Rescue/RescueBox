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
import frontend.constants as constants
from frontend.design_tokens import Design
from frontend.utils.nicegui_storage import get_user_id_for_jobs

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
    - Assistant, Jobs, Demo (direct links)
    - Resources (dropdown): About, Readme (plugins /models), Logs
    
    Returns:
        None: This function directly modifies the UI context
    
    Tips:
    - The navbar is sticky, so it will remain visible when scrolling
    - Links use hover effects (hover:underline, hover:bg-white/10)
    - Brand row (logo + title) is left-aligned; links use a tight row with ``flex-1 justify-end``
    - Use consistent styling classes for new navigation links
    """
    #logger.info("Creating navigation bar component")
    
    with ui.header(wrap=False).classes(Design.NAV_HEADER):
        #logger.debug("Header created with sticky positioning and blue theme")

        _logo_px = '11.25rem'
        _logo_style = (
            f'width:{_logo_px};height:{_logo_px};max-width:{_logo_px};max-height:{_logo_px};'
            'min-width:0;min-height:0;display:block;object-fit:contain;'
        )

        _link_cls = Design.NAV_LINK
        _nav_locked = get_user_id_for_jobs() is None

        def _nav_blocked_msg():
            ui.notify(
                'Enter a valid User ID on the home page.',
                type='warning',
                classes='rb-notify-505759'
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
                        '!text-base sm:!text-lg lg:!text-xl font-bold !leading-tight text-white '
                        'truncate min-w-0 max-w-[12rem] sm:max-w-[16rem] lg:max-w-[18rem]'
                    )
                    ui.label(APP_VERSION).classes(Design.NAV_VERSION_MUTED)

            with ui.row().classes('min-w-0 flex-1 justify-end items-center'):
                with ui.row().classes(
                    'inline-flex flex-wrap items-center justify-end gap-x-0.5 gap-y-0 '
                    'max-w-full py-0'
                ):
                    #logger.debug("Creating navigation links row")

                    _nav_items = (
                        ('Assistant', '/chatbot'),
                        ('Jobs', '/jobs'),
                        ('Demo', '/demo'),
                    )
                    for label, path in _nav_items:
                        if _nav_locked and label != 'Demo':
                            ui.label(label).classes(
                                _link_cls + ' opacity-50 cursor-not-allowed select-none'
                            ).on('click', lambda _: _nav_blocked_msg())
                        else:
                            ui.link(label, path).classes(_link_cls)

                    def _open_about() -> None:
                        ui.navigate.to(constants.NAV_LINKS['about'])

                    def _open_readme() -> None:
                        if _nav_locked:
                            _nav_blocked_msg()
                        else:
                            ui.navigate.to('/models')

                    def _open_logs() -> None:
                        if _nav_locked:
                            _nav_blocked_msg()
                        else:
                            ui.navigate.to('/logs')

                    with ui.dropdown_button(
                        'Resources',
                        color=None,
                        auto_close=True,
                    ).classes(_link_cls).props('flat dense no-caps'):
                        ui.menu_item('Readme', on_click=_open_readme)
                        ui.menu_item('Logs', on_click=_open_logs)
                        ui.menu_item('About', on_click=_open_about)

                # Session display removed for demo safety (avoids accidental user actions)

                # Clear Session button removed to avoid accidental data loss
    
 