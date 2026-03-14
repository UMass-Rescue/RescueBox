"""
Breadcrumb Navigation Component

This module provides breadcrumb navigation for better UX and quick navigation
between related pages (e.g., Jobs > Job Details > Results > Submit).

Usage:
    from frontend.components.shared import create_breadcrumbs
    
    create_breadcrumbs([
        {'label': 'Jobs', 'link': '/jobs'},
        {'label': f'Job {job_id}', 'link': f'/jobs/{job_id}'},
        {'label': 'Results'}
    ])
"""

import logging
from nicegui import ui
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_breadcrumbs(items: List[Dict[str, Optional[str]]], container=None):
    """
    Create breadcrumb navigation component.
    
    Creates a breadcrumb trail showing the navigation path with links.
    The last item is displayed as plain text (current page).
    
    Args:
        items (List[Dict[str, Optional[str]]]): List of breadcrumb items.
            Each item should have:
            - 'label' (str): Display text
            - 'link' (Optional[str]): Navigation link (None for current page)
        container: Optional NiceGUI container to add breadcrumbs to.
            If None, breadcrumbs are added to current context.
    
    Returns:
        ui.element: The breadcrumb container element
    
    Examples:
        # Simple breadcrumb
        create_breadcrumbs([
            {'label': 'Jobs', 'link': '/jobs'},
            {'label': 'JOB_123'}
        ])
        
        # With multiple levels
        create_breadcrumbs([
            {'label': 'Home', 'link': '/'},
            {'label': 'Jobs', 'link': '/jobs'},
            {'label': 'JOB_123', 'link': '/jobs/JOB_123'},
            {'label': 'Results'}
        ])
    
    Tips:
    - Last item should not have a link (it's the current page)
    - Use descriptive labels for better UX
    - Breadcrumbs automatically add separators (>)
    """
    logger.debug("Creating breadcrumbs with %d items", len(items))
    
    if container:
        breadcrumb_container = container
    else:
        breadcrumb_container = ui.row().classes('items-center gap-2 mb-4 text-sm')
    
    with breadcrumb_container:
        for i, item in enumerate(items):
            label = item.get('label', '')
            link = item.get('link')
            
            if link:
                # Add link with hover effect
                ui.link(label, link).classes('text-blue-600 hover:underline')
            else:
                # Current page (no link)
                ui.label(label).classes('text-gray-600 font-semibold')
            
            # Add separator (>) except for last item
            if i < len(items) - 1:
                ui.label('>').classes('text-gray-400 mx-1')
    
    logger.debug("Breadcrumbs created successfully")
    return breadcrumb_container


def create_job_breadcrumbs(job_id: str, current_page: str = 'Results'):
    """
    Create breadcrumbs for job-related pages.
    
    Convenience function for creating job breadcrumbs with common navigation.
    
    Args:
        job_id (str): Job unique identifier
        current_page (str): Current page label (e.g., 'Results', 'Details', 'Submit')
    
    Returns:
        ui.element: Breadcrumb container
    
    Examples:
        # Results page
        create_job_breadcrumbs('job-123', 'Results')
        
        # Details page
        create_job_breadcrumbs('job-123', 'Details')
    """
    items = [
        {'label': 'Jobs', 'link': '/jobs'},
        {'label': f'Job {job_id[:8]}...', 'link': f'/jobs/{job_id}'},
        {'label': current_page}
    ]
    return create_breadcrumbs(items)

