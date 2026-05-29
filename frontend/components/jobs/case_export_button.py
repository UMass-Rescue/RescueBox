"""One-click export of a completed job as CASE-style JSON-LD."""

from __future__ import annotations

import logging
from typing import Any, Dict

from nicegui import ui

from frontend.design_tokens import Design

logger = logging.getLogger(__name__)


def render_case_export_button(job_fields: Dict[str, Any]) -> None:
    """
    Add a button that downloads ``job-{uid}.jsonld`` built from the current job record.

    Only meaningful when status is completed and the job dict is available.
    """
    uid = job_fields.get("uid") or ""
    status = str(job_fields.get("status", "")).lower()

    if status != "completed" or not uid:
        return

    def _download() -> None:
        try:
            from case_export.persist import build_jsonld_bytes_from_job_dict

            data = build_jsonld_bytes_from_job_dict(job_fields)
            ui.download(data, f"rescuebox-job-{uid}.jsonld")
        except Exception as e:
            logger.exception("CASE export failed: %s", e)
            ui.notify(f"Export failed: {e}", type="negative", classes="rb-notify-505759")

    ui.button(
        "Export CASE JSON-LD",
        icon="download",
        on_click=_download,
    ).classes(Design.BTN_MEDIUM_GRAY).props("dense").tooltip(
        "Download a JSON-LD fragment (UCO-oriented) for this job"
    )
