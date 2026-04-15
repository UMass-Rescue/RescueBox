"""
Backward-compatible ``/licenses`` URL: redirect to ``/about`` (preserves ``?doc=``).
"""

from __future__ import annotations

from urllib.parse import quote

from nicegui import ui
from starlette.requests import Request
from starlette.responses import RedirectResponse


@ui.page("/licenses")
async def licenses_redirect_to_about(request: Request):
    doc = request.query_params.get("doc")
    if doc:
        return RedirectResponse(
            url=f"/about?doc={quote(doc, safe='')}",
            status_code=307,
        )
    return RedirectResponse(url="/about", status_code=307)
