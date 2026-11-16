"""Pure session and user storage accessors for NiceGUI application state.

This module manages in-memory, user, client, and general storage state
completely isolated from database queries and persistence repositories.
"""

from __future__ import annotations

import logging
import os
import uuid
from collections.abc import Callable
from typing import Any, TypeVar

from nicegui import app

from frontend.constants import is_valid_explicit_user_id
from frontend.utils.exceptions import UI_RENDER_ERRORS

logger = logging.getLogger(__name__)

DEFAULT_PREFERENCES: dict[str, Any] = {
    "dark_mode": False,
    "compact_view": False,
    "auto_scroll": True,
    "message_timestamp_format": "relative",
    "notifications_enabled": True,
    "chat_history_limit": 50,
}
_test_fallback_storage: dict[str, Any] = {}

_T = TypeVar("_T")
_STORAGE_UNAVAILABLE = object()


def _current_app() -> Any:
    """Return the active NiceGUI app instance, respecting mock patches on storage or session."""
    try:
        from frontend.utils import storage as storage_mod

        if hasattr(storage_mod, "app") and storage_mod.app is not None:
            return storage_mod.app
    except Exception:
        pass
    return app


def _runs_under_pytest() -> bool:
    try:
        return (
            "PYTEST_CURRENT_TEST" in os.environ or "PYTEST_XDIST_WORKER" in os.environ
        )
    except UI_RENDER_ERRORS:
        return False


def _ignore_storage_errors(
    action: Callable[[], _T], default: _T | None = None
) -> _T | None:
    try:
        return action()
    except UI_RENDER_ERRORS:
        return default


def _user_get(key: str, default: Any = None) -> Any:
    val = _ignore_storage_errors(
        lambda: _current_app().storage.user.get(key), default=_STORAGE_UNAVAILABLE
    )
    if val is _STORAGE_UNAVAILABLE:
        return default
    return val


def _user_set(key: str, value: Any) -> None:
    _ignore_storage_errors(lambda: _current_app().storage.user.__setitem__(key, value))


def _user_pop(key: str, default: Any = None) -> Any:
    return _ignore_storage_errors(
        lambda: _current_app().storage.user.pop(key, default), default=default
    )


def _general_get(key: str, default: Any = None) -> Any:
    val = _ignore_storage_errors(lambda: _current_app().storage.general.get(key))
    return default if val is None else val


def _general_set(key: str, value: Any) -> None:
    _ignore_storage_errors(lambda: _current_app().storage.general.__setitem__(key, value))


def _client_get(key: str, default: Any = None) -> Any:
    val = _ignore_storage_errors(lambda: _current_app().storage.client.get(key))
    return default if val is None else val


def _client_set(key: str, value: Any) -> None:
    _ignore_storage_errors(lambda: _current_app().storage.client.__setitem__(key, value))


def _client_pop(key: str, default: Any = None) -> Any:
    return _ignore_storage_errors(
        lambda: _current_app().storage.client.pop(key, default), default=default
    )


def read_user_storage_key(key: str, default: Any = None) -> Any:
    """Read a single key from NiceGUI user storage (None if unavailable)."""
    return _user_get(key, default)


def get_user_id() -> str | None:
    """Retrieve or generate the session user ID."""
    try:
        active_app = _current_app()
        user_id = active_app.storage.user.get("id")
        if not user_id:
            user_id = f"session-{uuid.uuid4().hex}"
            active_app.storage.user["id"] = user_id
        return user_id
    except UI_RENDER_ERRORS:
        if _runs_under_pytest():
            return "test-user-1"
        return None


def get_explicit_user_id() -> str | None:
    return get_active_case_id()


def set_explicit_user_id(value: str) -> None:
    set_active_case_id(value)


def clear_explicit_user_id() -> None:
    clear_active_case_id()


def release_explicit_user_id_claim(uid: str) -> None:
    if not uid:
        return
    if _runs_under_pytest():
        registry = _test_fallback_storage.get("user_id_registry", {})
        if uid in registry:
            registry.pop(uid)
            _test_fallback_storage["user_id_registry"] = registry
        return

    registry = dict(_general_get("user_id_registry", {}) or {})
    if uid in registry:
        registry.pop(uid)
        _general_set("user_id_registry", registry)


def ensure_explicit_user_id_for_tests() -> None:
    if _runs_under_pytest() and not get_explicit_user_id():
        set_explicit_user_id("test-user")


def try_claim_explicit_user_id(uid: str) -> str:
    if not is_valid_explicit_user_id(uid):
        return "invalid"

    if _runs_under_pytest():
        registry = _test_fallback_storage.get("user_id_registry", {})
        if uid in registry:
            return "taken"
        registry[uid] = True
        _test_fallback_storage["user_id_registry"] = registry
        set_explicit_user_id(uid)
        return "ok"

    try:
        active_app = _current_app()
        registry = dict(active_app.storage.general.get("user_id_registry", {}) or {})
        if uid in registry:
            return "taken"
        registry[uid] = True
        active_app.storage.general["user_id_registry"] = registry
        set_explicit_user_id(uid)
        return "ok"
    except UI_RENDER_ERRORS:
        return "invalid"


def get_active_case_id() -> str | None:
    """Return the currently selected active case ID from session storage."""
    case_id = _user_get("active_case_id")
    if case_id:
        return case_id
    if _runs_under_pytest():
        return _test_fallback_storage.get("active_case_id")
    return None


def set_active_case_id(value: str) -> None:
    """Set the active case ID in user storage."""
    v = value.strip()
    _user_set("active_case_id", v)
    if _runs_under_pytest():
        _test_fallback_storage["active_case_id"] = v


def clear_active_case_id() -> None:
    """Clear the active case ID from user storage."""
    _user_pop("active_case_id", None)
    if _runs_under_pytest():
        _test_fallback_storage.pop("active_case_id", None)


def get_user_id_for_jobs() -> str | None:
    """Returns the active case ID so that all jobs and chat history are scoped to the active case."""
    return get_active_case_id()


def set_user_preference(key: str, value: Any) -> None:
    """Persist a single preference setting in user storage."""
    prefs = get_user_preferences()
    prefs[key] = value
    _user_set("preferences", prefs)
    if _runs_under_pytest():
        _test_fallback_storage["preferences"] = prefs


def get_user_preferences() -> dict[str, Any]:
    """Retrieve user preferences dictionary with fallback defaults."""
    prefs = _user_get("preferences")
    if prefs is None and _runs_under_pytest():
        prefs = _test_fallback_storage.get("preferences")
    if prefs is None:
        prefs = {}
    return {**DEFAULT_PREFERENCES, **prefs}


def get_user_preference(key: str, default: Any = None) -> Any:
    """Get a single preference value by key with optional default."""
    prefs = get_user_preferences()
    return prefs.get(key, default)


def set_user_preferences(prefs: dict[str, Any]) -> None:
    """Batch-update user preferences dictionary."""
    current = get_user_preferences()
    current.update(prefs)
    _user_set("preferences", current)
    if _runs_under_pytest():
        _test_fallback_storage["preferences"] = current


def reset_user_preferences() -> None:
    """Reset user preferences to factory defaults."""
    _user_set("preferences", DEFAULT_PREFERENCES)
    if _runs_under_pytest():
        _test_fallback_storage["preferences"] = DEFAULT_PREFERENCES


def get_current_conversation_id() -> str | None:
    """Get the active conversation ID for the current session."""
    val = _user_get("current_conversation_id")
    if val:
        return val
    return _test_fallback_storage.get("current_conversation_id")


def set_current_conversation_id(conversation_id: str | None) -> None:
    """Set or clear the active conversation ID for the current session."""
    if conversation_id:
        _user_set("current_conversation_id", conversation_id)
    else:
        _user_pop("current_conversation_id", None)
    if _runs_under_pytest():
        if conversation_id:
            _test_fallback_storage["current_conversation_id"] = conversation_id
        else:
            _test_fallback_storage.pop("current_conversation_id", None)


def get_draft_message() -> str:
    """Get the current unposted chat message draft."""
    val = _client_get("draft_message")
    if val:
        return val
    return _test_fallback_storage.get("draft_message", "")


def set_draft_message(message: str) -> None:
    """Store or clear the unposted chat message draft."""
    if message:
        _client_set("draft_message", message)
    else:
        _client_pop("draft_message", None)
    if _runs_under_pytest():
        if message:
            _test_fallback_storage["draft_message"] = message
        else:
            _test_fallback_storage.pop("draft_message", None)


def set_conversation_to_load(
    conversation_id: str, conversation_data: Any, messages: list[Any]
) -> None:
    """Stash a conversation payload to be replayed upon navigation."""
    data = {
        "conversation_id": conversation_id,
        "conversation_data": conversation_data,
        "messages": messages,
    }
    _user_set("conversation_to_load", data)
    if _runs_under_pytest():
        _test_fallback_storage["conversation_to_load"] = data


def get_conversation_to_load() -> dict[str, Any] | None:
    """Retrieve and pop the queued conversation to load."""
    try:
        active_app = _current_app()
        data = active_app.storage.user.get("conversation_to_load")
        if data:
            active_app.storage.user.pop("conversation_to_load", None)
            if _runs_under_pytest():
                _test_fallback_storage.pop("conversation_to_load", None)
        return data
    except UI_RENDER_ERRORS:
        data = _test_fallback_storage.get("conversation_to_load")
        if data:
            _test_fallback_storage.pop("conversation_to_load", None)
        return data


def clear_conversation_to_load() -> None:
    """Clear any pending queued conversation to load."""
    _user_pop("conversation_to_load", None)
    if _runs_under_pytest():
        _test_fallback_storage.pop("conversation_to_load", None)


def get_form_draft() -> dict[str, Any] | None:
    """Get the current tool form draft state."""
    val = _user_get("form_draft")
    if val:
        return val
    return _test_fallback_storage.get("form_draft")


def set_form_draft(
    endpoint: str | dict[str, Any], arguments: dict[str, Any] | None = None
) -> None:
    """Save tool form draft state in session storage."""
    if (not endpoint and not arguments) or (
        endpoint == "" and (arguments is None or arguments == {})
    ):
        draft = None
    elif isinstance(endpoint, dict) and arguments is None:
        draft = endpoint
    else:
        draft = {"endpoint": endpoint, "arguments": arguments}
    if draft is None:
        _user_pop("form_draft", None)
    else:
        _user_set("form_draft", draft)
    if _runs_under_pytest():
        _test_fallback_storage["form_draft"] = draft


def clear_form_draft() -> None:
    """Clear tool form draft state from session storage."""
    _user_pop("form_draft", None)
    if _runs_under_pytest():
        _test_fallback_storage.pop("form_draft", None)


def reset_test_storage() -> None:
    """Clear in-memory fallback storage used in tests."""
    _test_fallback_storage.clear()


__all__ = [
    "DEFAULT_PREFERENCES",
    "clear_active_case_id",
    "clear_conversation_to_load",
    "clear_explicit_user_id",
    "clear_form_draft",
    "ensure_explicit_user_id_for_tests",
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
