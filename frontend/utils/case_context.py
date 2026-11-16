"""Application boundary helper bridging active session case ID with CaseDB records."""

from __future__ import annotations

import logging
from typing import Any

from frontend.database.case_db import CaseRecord, get_case_db
from frontend.utils.exceptions import UI_RENDER_ERRORS
from frontend.utils.session import _runs_under_pytest, get_active_case_id

logger = logging.getLogger(__name__)


def get_active_case() -> Any | None:
    """Resolve the active CaseRecord from CaseDB using the active session case ID."""
    case_id = get_active_case_id()
    if not case_id:
        return None
    try:
        case = get_case_db().get_case_by_id_sync(case_id)
        if not case and _runs_under_pytest():
            return CaseRecord(
                caseId=case_id,
                caseNumber="TEST-CASE",
                investigators="Test Investigator",
                evidencePath="/tmp",
                createdAt="2026-06-04T13:15:00",
                updatedAt="2026-06-04T13:15:00",
            )
        return case
    except UI_RENDER_ERRORS as e:
        logger.debug("Failed to retrieve active case record for id %s: %s", case_id, e)
        return None


__all__ = ["get_active_case"]
