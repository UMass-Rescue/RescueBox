"""Response normalization and batch-item extraction helpers."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from rb.api.models import BatchFileResponse, FileResponse, ResponseBody

from frontend.chatbot.exceptions import CHATBOT_ERRORS
from frontend.utils.validators import validate_response_body

logger = logging.getLogger(__name__)


def coerce_pipeline_response(raw: Any) -> Any:
    """Normalize API payloads into ``ResponseBody`` where possible."""
    if isinstance(raw, ResponseBody):
        return raw
    if not isinstance(raw, dict):
        return raw
    validated = validate_response_body(raw)
    if isinstance(validated, ResponseBody):
        return validated
    inner = raw.get("root")
    if isinstance(inner, dict):
        validated_inner = validate_response_body(inner)
        if isinstance(validated_inner, ResponseBody):
            return validated_inner
        try:
            return ResponseBody(root=BatchFileResponse.model_validate(inner))
        except CHATBOT_ERRORS:
            pass
    try:
        return ResponseBody(**raw)
    except CHATBOT_ERRORS as e:
        logger.warning(
            "coerce_pipeline_response: could not build ResponseBody (%s); keys=%s",
            e,
            list(raw.keys())[:24],
        )
        return raw


def extract_batch_file_items(response_body: Any) -> list[dict[str, Any]]:
    """
    Extract ``path``/``metadata`` from each row in a batch-file shaped payload.

    Accepts ``ResponseBody`` or plain dict.
    """
    try:
        root: Any = None
        if isinstance(response_body, ResponseBody):
            root = response_body.root
        elif isinstance(response_body, dict):
            root = response_body.get("root", response_body)

        files: list[Any] = []
        if isinstance(root, BatchFileResponse) and root.files:
            files = list(root.files)
        elif isinstance(root, dict) and root.get("output_type") == "batchfile":
            files = list(root.get("files") or [])

        if not files:
            return []

        items: list[dict[str, Any]] = []
        for fr in files:
            if isinstance(fr, FileResponse):
                items.append(
                    {
                        "path": Path(fr.path).as_posix(),
                        "metadata": dict(fr.metadata) if fr.metadata else {},
                    }
                )
            elif isinstance(fr, dict):
                path = fr.get("path")
                if not path:
                    continue
                meta = fr.get("metadata")
                items.append(
                    {
                        "path": Path(path).as_posix(),
                        "metadata": dict(meta) if isinstance(meta, dict) else {},
                    }
                )
            else:
                logger.debug(
                    "extract_batch_file_items: skipping unknown file entry type=%s",
                    type(fr),
                )

        if not items and files:
            logger.warning(
                "extract_batch_file_items: %d file row(s) present but none produced items (first type=%s)",
                len(files),
                type(files[0]),
            )
        return items
    except CHATBOT_ERRORS as e:
        logger.warning("Error extracting batch file items: %s", e)
        return []


def batch_items_have_age_gender_metadata(items: list[dict[str, Any]]) -> bool:
    """True if any batch row has Age/Gender metadata fields."""
    for it in items:
        meta = it.get("metadata") or {}
        for k in meta:
            kl = str(k).lower()
            if kl in ("gender", "age"):
                return True
    return False
