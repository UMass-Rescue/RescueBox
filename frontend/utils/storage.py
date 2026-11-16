"""Session storage and active case context coordination.

This module acts as a unified coordinator re-exporting pure session state accessors
from `frontend.utils.session` and active case record resolution from
`frontend.utils.case_context`.
"""

from __future__ import annotations

from typing import Any

from .case_context import get_active_case
from .session import (
    DEFAULT_PREFERENCES,
    _client_get,
    _client_pop,
    _client_set,
    _general_get,
    _general_set,
    _ignore_storage_errors,
    _runs_under_pytest,
    _test_fallback_storage,
    _user_get,
    _user_pop,
    _user_set,
    clear_active_case_id,
    clear_conversation_to_load,
    clear_explicit_user_id,
    clear_form_draft,
    ensure_explicit_user_id_for_tests,
    get_active_case_id,
    get_conversation_to_load,
    get_current_conversation_id,
    get_draft_message,
    get_explicit_user_id,
    get_form_draft,
    get_user_id,
    get_user_id_for_jobs,
    get_user_preference,
    get_user_preferences,
    read_user_storage_key,
    release_explicit_user_id_claim,
    reset_test_storage,
    reset_user_preferences,
    set_active_case_id,
    set_conversation_to_load,
    set_current_conversation_id,
    set_draft_message,
    set_explicit_user_id,
    set_form_draft,
    set_user_preference,
    set_user_preferences,
    try_claim_explicit_user_id,
)

# Tests may set this; ``session._current_app()`` prefers it when not None.
app: Any = None

__all__ = [
    "DEFAULT_PREFERENCES",
    "app",
    "_client_get",
    "_client_pop",
    "_client_set",
    "_general_get",
    "_general_set",
    "_ignore_storage_errors",
    "_runs_under_pytest",
    "_test_fallback_storage",
    "_user_get",
    "_user_pop",
    "_user_set",
    "clear_active_case_id",
    "clear_conversation_to_load",
    "clear_explicit_user_id",
    "clear_form_draft",
    "ensure_explicit_user_id_for_tests",
    "get_active_case",
    "get_active_case_id",
    "get_conversation_to_load",
    "get_current_conversation_id",
    "get_draft_message",
    "get_explicit_user_id",
    "get_form_draft",
    "get_user_id",
    "get_user_id_for_jobs",
    "get_user_preference",
    "get_user_preferences",
    "read_user_storage_key",
    "release_explicit_user_id_claim",
    "reset_test_storage",
    "reset_user_preferences",
    "set_active_case_id",
    "set_conversation_to_load",
    "set_current_conversation_id",
    "set_draft_message",
    "set_explicit_user_id",
    "set_form_draft",
    "set_user_preference",
    "set_user_preferences",
    "try_claim_explicit_user_id",
]
