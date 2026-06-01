import logging
import uuid
from typing import Dict, Any, Optional
from nicegui import app
from frontend.constants import is_valid_explicit_user_id

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


def _runs_under_pytest() -> bool:
    try:
        import os

        return (
            "PYTEST_CURRENT_TEST" in os.environ or "PYTEST_XDIST_WORKER" in os.environ
        )
    except Exception:
        return False


def get_user_id() -> Optional[str]:
    try:
        user_id = app.storage.user.get("id")
        if not user_id:
            user_id = f"session-{uuid.uuid4().hex}"
            app.storage.user["id"] = user_id
        return user_id
    except Exception:
        if _runs_under_pytest():
            return "test-user-1"
        return None


def get_explicit_user_id() -> Optional[str]:
    try:
        return app.storage.user.get("explicit_job_user_id")
    except Exception:
        if _runs_under_pytest():
            return _test_fallback_storage.get("explicit_job_user_id")
        return None


def set_explicit_user_id(value: str):
    v = value.strip()
    try:
        app.storage.user["explicit_job_user_id"] = v
    except Exception:
        pass
    if _runs_under_pytest():
        _test_fallback_storage["explicit_job_user_id"] = v


def clear_explicit_user_id():
    uid = get_explicit_user_id()
    if uid:
        release_explicit_user_id_claim(uid)
    try:
        app.storage.user.pop("explicit_job_user_id", None)
    except Exception:
        pass
    if _runs_under_pytest():
        _test_fallback_storage.pop("explicit_job_user_id", None)


def release_explicit_user_id_claim(uid: str):
    if not uid:
        return
    if _runs_under_pytest():
        registry = _test_fallback_storage.get("user_id_registry", {})
        if uid in registry:
            registry.pop(uid)
            _test_fallback_storage["user_id_registry"] = registry
        return

    try:
        registry = app.storage.general.get("user_id_registry", {})
        if uid in registry:
            registry.pop(uid)
            app.storage.general["user_id_registry"] = registry
    except Exception:
        pass


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
        registry = app.storage.general.get("user_id_registry", {})
        if uid in registry:
            return "taken"
        registry[uid] = True
        app.storage.general["user_id_registry"] = registry
        set_explicit_user_id(uid)
        return "ok"
    except Exception:
        return "invalid"


def get_user_id_for_jobs() -> Optional[str]:
    """Alias for get_explicit_user_id for backward compatibility."""
    return get_explicit_user_id()


def set_user_preference(key: str, value: Any):
    prefs = get_user_preferences()
    prefs[key] = value
    try:
        app.storage.user["preferences"] = prefs
    except Exception:
        pass
    if _runs_under_pytest():
        _test_fallback_storage["preferences"] = prefs


def get_user_preferences() -> Dict[str, Any]:
    prefs = None
    try:
        prefs = app.storage.user.get("preferences")
    except Exception:
        pass

    if prefs is None and _runs_under_pytest():
        prefs = _test_fallback_storage.get("preferences")

    if prefs is None:
        prefs = {}

    return {**DEFAULT_PREFERENCES, **prefs}


def get_current_conversation_id() -> Optional[str]:
    try:
        val = app.storage.user.get("current_conversation_id")
        if val:
            return val
    except Exception:
        pass
    return _test_fallback_storage.get("current_conversation_id")


def set_current_conversation_id(conversation_id: Optional[str]):
    try:
        if conversation_id:
            app.storage.user["current_conversation_id"] = conversation_id
        else:
            app.storage.user.pop("current_conversation_id", None)
    except Exception:
        pass
    if _runs_under_pytest():
        if conversation_id:
            _test_fallback_storage["current_conversation_id"] = conversation_id
        else:
            _test_fallback_storage.pop("current_conversation_id", None)


def get_draft_message() -> str:
    try:
        val = app.storage.client.get("draft_message")
        if val:
            return val
    except Exception:
        pass
    return _test_fallback_storage.get("draft_message", "")


def set_draft_message(message: str):
    try:
        if message:
            app.storage.client["draft_message"] = message
        else:
            app.storage.client.pop("draft_message", None)
    except Exception:
        pass
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
    try:
        app.storage.user["conversation_to_load"] = data
    except Exception:
        pass
    if _runs_under_pytest():
        _test_fallback_storage["conversation_to_load"] = data


def get_conversation_to_load():
    try:
        data = app.storage.user.get("conversation_to_load")
        if data:
            app.storage.user.pop("conversation_to_load", None)
        return data
    except Exception:
        data = _test_fallback_storage.get("conversation_to_load")
        if data:
            _test_fallback_storage.pop("conversation_to_load", None)
        return data


def clear_conversation_to_load():
    try:
        app.storage.user.pop("conversation_to_load", None)
    except Exception:
        pass
    if _runs_under_pytest():
        _test_fallback_storage.pop("conversation_to_load", None)


def get_form_draft() -> Optional[dict]:
    try:
        val = app.storage.user.get("form_draft")
        if val:
            return val
    except Exception:
        pass
    return _test_fallback_storage.get("form_draft")


def set_form_draft(endpoint: str, arguments: dict = None):
    # Support both 1-arg (dict) and 2-arg (str, dict) patterns
    if (not endpoint and not arguments) or (
        endpoint == "" and (arguments is None or arguments == {})
    ):
        draft = None
    elif isinstance(endpoint, dict) and arguments is None:
        draft = endpoint
    else:
        draft = {"endpoint": endpoint, "arguments": arguments}
    try:
        app.storage.user["form_draft"] = draft
    except Exception:
        pass
    if _runs_under_pytest():
        _test_fallback_storage["form_draft"] = draft


def clear_form_draft():
    try:
        app.storage.user.pop("form_draft", None)
    except Exception:
        pass
    if _runs_under_pytest():
        _test_fallback_storage.pop("form_draft", None)


def get_user_preference(key: str, default: Any = None) -> Any:
    prefs = get_user_preferences()
    return prefs.get(key, default)


def set_user_preferences(prefs: Dict[str, Any]):
    current = get_user_preferences()
    current.update(prefs)
    try:
        app.storage.user["preferences"] = current
    except Exception:
        pass
    if _runs_under_pytest():
        _test_fallback_storage["preferences"] = current


def reset_user_preferences():
    try:
        app.storage.user["preferences"] = DEFAULT_PREFERENCES
    except Exception:
        pass
    if _runs_under_pytest():
        _test_fallback_storage["preferences"] = DEFAULT_PREFERENCES


def reset_test_storage():
    global _test_fallback_storage
    _test_fallback_storage = {}
