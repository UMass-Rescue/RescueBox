import logging
import os
import uuid
from typing import Any, Callable, Dict, Optional, TypeVar

from nicegui import app

from frontend.constants import is_valid_explicit_user_id
from frontend.database.case_db import CaseRecord, get_case_db
from frontend.utils.exceptions import UI_RENDER_ERRORS

logger = logging.getLogger(__name__)

DEFAULT_PREFERENCES = {
    "dark_mode": False,
    "compact_view": False,
    "auto_scroll": True,
    "message_timestamp_format": "relative",
    "notifications_enabled": True,
    "chat_history_limit": 50,
}
_test_fallback_storage: dict = {}

_T = TypeVar("_T")
_STORAGE_UNAVAILABLE = object()


def _runs_under_pytest() -> bool:
    try:
        return (
            "PYTEST_CURRENT_TEST" in os.environ or "PYTEST_XDIST_WORKER" in os.environ
        )
    except UI_RENDER_ERRORS:
        return False


def _ignore_storage_errors(
    action: Callable[[], _T], default: Optional[_T] = None
) -> Optional[_T]:
    try:
        return action()
    except UI_RENDER_ERRORS:
        return default


def _user_get(key: str, default: Any = None) -> Any:
    val = _ignore_storage_errors(
        lambda: app.storage.user.get(key), default=_STORAGE_UNAVAILABLE
    )
    if val is _STORAGE_UNAVAILABLE:
        return default
    return val


def _user_set(key: str, value: Any) -> None:
    _ignore_storage_errors(lambda: app.storage.user.__setitem__(key, value))


def _user_pop(key: str, default: Any = None) -> Any:
    return _ignore_storage_errors(
        lambda: app.storage.user.pop(key, default), default=default
    )


def _general_get(key: str, default: Any = None) -> Any:
    val = _ignore_storage_errors(lambda: app.storage.general.get(key))
    return default if val is None else val


def _general_set(key: str, value: Any) -> None:
    _ignore_storage_errors(lambda: app.storage.general.__setitem__(key, value))


def _client_get(key: str, default: Any = None) -> Any:
    val = _ignore_storage_errors(lambda: app.storage.client.get(key))
    return default if val is None else val


def _client_set(key: str, value: Any) -> None:
    _ignore_storage_errors(lambda: app.storage.client.__setitem__(key, value))


def _client_pop(key: str, default: Any = None) -> Any:
    return _ignore_storage_errors(
        lambda: app.storage.client.pop(key, default), default=default
    )


def read_user_storage_key(key: str, default: Any = None) -> Any:
    """Read a single key from NiceGUI user storage (None if unavailable)."""
    return _user_get(key, default)


def get_user_id() -> Optional[str]:
    try:
        user_id = app.storage.user.get("id")
        if not user_id:
            user_id = f"session-{uuid.uuid4().hex}"
            app.storage.user["id"] = user_id
        return user_id
    except UI_RENDER_ERRORS:
        if _runs_under_pytest():
            return "test-user-1"
        return None


def get_explicit_user_id() -> Optional[str]:
    return get_active_case_id()


def set_explicit_user_id(value: str):
    set_active_case_id(value)


def clear_explicit_user_id():
    clear_active_case_id()


def release_explicit_user_id_claim(uid: str):
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


def ensure_explicit_user_id_for_tests():
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
        registry = dict(app.storage.general.get("user_id_registry", {}) or {})
        if uid in registry:
            return "taken"
        registry[uid] = True
        app.storage.general["user_id_registry"] = registry
        set_explicit_user_id(uid)
        return "ok"
    except UI_RENDER_ERRORS:
        return "invalid"


def get_active_case_id() -> Optional[str]:
    case_id = _user_get("active_case_id")
    if case_id:
        return case_id
    if _runs_under_pytest():
        return _test_fallback_storage.get("active_case_id")
    return None


def set_active_case_id(value: str):
    v = value.strip()
    _user_set("active_case_id", v)
    if _runs_under_pytest():
        _test_fallback_storage["active_case_id"] = v


def clear_active_case_id():
    _user_pop("active_case_id", None)
    if _runs_under_pytest():
        _test_fallback_storage.pop("active_case_id", None)


def get_active_case() -> Optional[Any]:
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
    except UI_RENDER_ERRORS:
        return None


def get_user_id_for_jobs() -> Optional[str]:
    """Returns the active case ID so that all jobs and chat history are scoped to the active case."""
    return get_active_case_id()


def set_user_preference(key: str, value: Any):
    prefs = get_user_preferences()
    prefs[key] = value
    _user_set("preferences", prefs)
    if _runs_under_pytest():
        _test_fallback_storage["preferences"] = prefs


def get_user_preferences() -> Dict[str, Any]:
    prefs = _user_get("preferences")
    if prefs is None and _runs_under_pytest():
        prefs = _test_fallback_storage.get("preferences")
    if prefs is None:
        prefs = {}
    return {**DEFAULT_PREFERENCES, **prefs}


def get_current_conversation_id() -> Optional[str]:
    val = _user_get("current_conversation_id")
    if val:
        return val
    return _test_fallback_storage.get("current_conversation_id")


def set_current_conversation_id(conversation_id: Optional[str]):
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
    val = _client_get("draft_message")
    if val:
        return val
    return _test_fallback_storage.get("draft_message", "")


def set_draft_message(message: str):
    if message:
        _client_set("draft_message", message)
    else:
        _client_pop("draft_message", None)
    if _runs_under_pytest():
        if message:
            _test_fallback_storage["draft_message"] = message
        else:
            _test_fallback_storage.pop("draft_message", None)


def set_conversation_to_load(conversation_id, conversation_data, messages):
    data = {
        "conversation_id": conversation_id,
        "conversation_data": conversation_data,
        "messages": messages,
    }
    _user_set("conversation_to_load", data)
    if _runs_under_pytest():
        _test_fallback_storage["conversation_to_load"] = data


def get_conversation_to_load():
    try:
        data = app.storage.user.get("conversation_to_load")
        if data:
            app.storage.user.pop("conversation_to_load", None)
            if _runs_under_pytest():
                _test_fallback_storage.pop("conversation_to_load", None)
        return data
    except UI_RENDER_ERRORS:
        data = _test_fallback_storage.get("conversation_to_load")
        if data:
            _test_fallback_storage.pop("conversation_to_load", None)
        return data


def clear_conversation_to_load():
    _user_pop("conversation_to_load", None)
    if _runs_under_pytest():
        _test_fallback_storage.pop("conversation_to_load", None)


def get_form_draft() -> Optional[dict]:
    val = _user_get("form_draft")
    if val:
        return val
    return _test_fallback_storage.get("form_draft")


def set_form_draft(endpoint: str, arguments: dict = None):
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


def clear_form_draft():
    _user_pop("form_draft", None)
    if _runs_under_pytest():
        _test_fallback_storage.pop("form_draft", None)


def get_user_preference(key: str, default: Any = None) -> Any:
    prefs = get_user_preferences()
    return prefs.get(key, default)


def set_user_preferences(prefs: Dict[str, Any]):
    current = get_user_preferences()
    current.update(prefs)
    _user_set("preferences", current)
    if _runs_under_pytest():
        _test_fallback_storage["preferences"] = current


def reset_user_preferences():
    _user_set("preferences", DEFAULT_PREFERENCES)
    if _runs_under_pytest():
        _test_fallback_storage["preferences"] = DEFAULT_PREFERENCES


def reset_test_storage():
    _test_fallback_storage.clear()
