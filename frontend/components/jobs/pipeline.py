from __future__ import annotations

from typing import Optional

from nicegui import ui


def short_endpoint_label(endpoint: Optional[str]) -> str:
    if not endpoint:
        return "?"
    parts = [p for p in endpoint.strip().split("/") if p]
    return (parts[-1] if parts else endpoint)[:28]


def render_pipeline_run_banner(
    *,
    root_job_id: str,
    current_job_id: str,
    steps: list[dict[str, str]],
) -> None:
    """
    Render a single-row stepper: Pipeline · run link · 1. step → 2. step …

    ``steps`` items: ``{"job_id": str, "endpoint": str}`` in pipeline order.
    """
    if len(steps) < 2:
        return
    with ui.row().classes(
        "w-full flex-wrap items-center gap-x-1 gap-y-2 mb-4 px-3 py-2 rounded-lg "
        "bg-[#505759] border border-[#3d4442]"
    ):
        ui.label("Pipeline").classes(
            "text-xs font-semibold uppercase tracking-wide text-white shrink-0"
        )
        ui.link(
            f"Run {root_job_id[:11]}…",
            f"/jobs/{root_job_id}",
        ).classes(
            "text-xs font-mono text-white/90 hover:underline shrink-0"
        ).tooltip(root_job_id)
        ui.label("·").classes("text-white/50 shrink-0")
        for i, step in enumerate(steps):
            if i:
                ui.icon("chevron_right", size="xs").classes("text-white/55 shrink-0")
            ep = short_endpoint_label(step.get("endpoint"))
            jid = (step.get("job_id") or "").strip()
            label = f"{i + 1}. {ep}"
            if jid == current_job_id:
                ui.label(label).classes(
                    "text-sm font-semibold text-white shrink-0"
                ).tooltip(jid)
            else:
                ui.link(label, f"/jobs/{jid}").classes(
                    "text-sm text-white/90 hover:underline shrink-0"
                ).tooltip(jid)
