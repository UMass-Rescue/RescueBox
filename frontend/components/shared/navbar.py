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

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_navbar():
    """
    Create and render the main navigation bar component.
    
    This function generates a sticky navigation bar that appears at the top
    of every page. It includes the RescueBox branding and navigation links
    to major sections of the application.
    
    Design Features:
    - Sticky positioning: Navbar remains visible while scrolling (sticky top-0)
    - High z-index: Ensures navbar appears above other content (z-50)
    - Blue theme: Matches RescueBox branding (bg-blue-600)
    - Shadow: Adds depth with shadow-lg
    - Responsive: Container centers content and adjusts to screen size
    
    Navigation Links:
    - Models: Browse available ML models (/models)
    - Jobs: View job history and status (/jobs)
    - Assistant: Access chatbot interface (/chatbot)
    - Logs: View application logs (/logs)
    
    Returns:
        None: This function directly modifies the UI context
        
    Usage:
        Import and call at the start of any page:
        from frontend.components.shared import create_navbar
        
        @ui.page('/mypage')
        async def my_page():
            create_navbar()
            # ... rest of page content
    
    Tips:
    - The navbar is sticky, so it will remain visible when scrolling
    - Links use hover effects (hover:underline, hover:bg-blue-700)
    - ui.space() pushes navigation links to the right side
    - Use consistent styling classes for new navigation links
    """
    logger.info("Creating navigation bar component")
    
    with ui.header().classes('bg-blue-600 text-white shadow-lg sticky top-0 z-50'):
        logger.debug("Header created with sticky positioning and blue theme")
        
        with ui.row().classes('container mx-auto items-center w-full px-4'):
            logger.debug("Creating navbar container with responsive layout")
            
            # Application branding
            ui.label('🚑 RescueBox Desktop').classes('text-2xl font-bold')
            logger.debug("Brand label added")
            
            # Push navigation links to the right
            ui.space()
            logger.debug("Space added to push navigation links right")
            
            # Navigation links
            with ui.row().classes('gap-4 items-center'):
                logger.debug("Creating navigation links row")

                ui.link('Plugin Details', '/models').classes('text-white hover:underline px-3 py-2 rounded hover:bg-blue-700')
                logger.debug("Models link created")

                ui.link('Assistant', '/chatbot').classes('text-white hover:underline px-3 py-2 rounded hover:bg-blue-700')
                logger.debug("chatbot link created")
                
                ui.link('Jobs', '/jobs').classes('text-white hover:underline px-3 py-2 rounded hover:bg-blue-700')
                logger.debug("Jobs link created")
                
                ui.link('Logs', '/logs').classes('text-white hover:underline px-3 py-2 rounded hover:bg-blue-700')
                logger.debug("Logs link created")

                ui.link('Demo', '/demo').classes('text-white hover:underline px-3 py-2 rounded hover:bg-blue-700')
                logger.debug("Demo link created")

                # Theme toggle
                from frontend.utils.theme import create_theme_toggle
                theme_toggle = create_theme_toggle()
                # Style the toggle for navbar (white text/label for visibility)
                theme_toggle.classes('ml-4 items-center')
                theme_toggle.props('color=white')
                logger.debug("Theme toggle added to navbar")

                # Session display removed for demo safety (avoids accidental user actions)

                # Clear Session button removed to avoid accidental data loss
    
    logger.info("Navigation bar created successfully")