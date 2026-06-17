"""Breadcrumb navigation."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from nicegui import ui

logger = logging.getLogger(__name__)


def create_breadcrumbs(items: List[Dict[str, Optional[str]]], container=None):
    logger.debug("Creating breadcrumbs with %d items", len(items))

    if container:
        breadcrumb_container = container
    else:
        breadcrumb_container = ui.row().classes("items-center gap-2 mb-4 text-sm")

    with breadcrumb_container:
        for i, item in enumerate(items):
            label = item.get("label", "")
            link = item.get("link")

            if link:
                ui.link(label, link).classes("text-[#881c1c] hover:underline")
            else:
                ui.label(label).classes("text-zinc-600 font-semibold")

            if i < len(items) - 1:
                ui.label(">").classes("text-zinc-400 mx-1")

    logger.debug("Breadcrumbs created successfully")
    return breadcrumb_container


def create_job_breadcrumbs(job_id: str, current_page: str = "Results"):
    items = [
        {"label": "Jobs", "link": "/jobs"},
        {"label": f"Job {job_id[:8]}...", "link": f"/jobs/{job_id}"},
        {"label": current_page},
    ]
    return create_breadcrumbs(items)
