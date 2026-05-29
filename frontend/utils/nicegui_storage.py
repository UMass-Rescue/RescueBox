"""
NiceGUI Storage Utilities

This module provides utilities for integrating NiceGUI's storage system
with the chat history and job management features.

NiceGUI Storage Types:
- app.storage.user: User-specific, persists across sessions
- app.storage.client: Client-side, cleared when browser cache cleared
- app.storage.general: Shared across all users

Usage:
    from frontend.utils.nicegui_storage import (
        get_current_conversation_id,
        set_current_conversation_id,
        get_user_id,
        get_user_id_for_jobs,
        get_client_ip
    )
    
    # Get NiceGUI user ID (session-based)
    user_id = get_user_id()
    
    # Get user ID for jobs (IP-based when available, persists across sessions)
    user_id = get_user_id_for_jobs()
    
    # Manage current conversation
    conv_id = get_current_conversation_id()
    set_current_conversation_id(new_conv_id)
"""

import logging
import threading
from pathlib import Path
from typing import Literal, Optional
from nicegui import app, ui

from frontend.constants import is_valid_explicit_user_id

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Lock for demo folder assignment (avoids race when multiple sessions request at once)
_demo_folder_lock = threading.Lock()

# Serialize explicit User ID registration across all clients (one claim at a time)
_explicit_user_id_registry_lock = threading.Lock()
# Process-wide set of claimed demo-format IDs (shared across NiceGUI sessions)
_CLAIMED_EXPLICIT_USER_IDS_KEY = "claimed_explicit_user_ids"

# Fallback storage used by tests when NiceGUI's app.storage isn't available
_test_fallback_storage: dict = {}


def _runs_under_pytest() -> bool:
    try:
        import os

        return "PYTEST_CURRENT_TEST" in os.environ or "PYTEST_XDIST_WORKER" in os.environ
    except Exception:
        return False


def _defer_browser_mutation(fn) -> None:
    """Run ``fn`` after the current response cycle so ``app.storage.browser`` can be updated."""
    if _runs_under_pytest():
        fn()
        return
    try:
        ui.timer(0, fn, once=True)
    except Exception:
        fn()

def get_client_ip() -> Optional[str]:
    """
    Get the client IP address from the current NiceGUI request context.

    Uses context.client.ip when available (after WebSocket connection).
    Jobs are associated with this IP so they persist across session changes
    when users return from the same machine (e.g. same LAN/DHCP).

    Returns:
        Optional[str]: Client IP if available, None otherwise
    """
    try:
        from nicegui import context
        client = getattr(context, "client", None)
        if client is not None:
            ip = getattr(client, "ip", None)
            if ip:
                return str(ip).strip()
    except Exception as e:
        err_msg = str(e)
        if "UI context" not in err_msg and "ui context" not in err_msg.lower():
            logger.debug("Could not get client IP: %s", e)
    return None


# Storage key for explicit user ID (prompted on each new session)
_EXPLICIT_USER_ID_KEY = "explicit_job_user_id"


def _read_raw_explicit_user_id() -> Optional[str]:
    """Return stored ID without validation (used before clear; avoids get→clear recursion).

    Prefer ``app.storage.user`` (session) — it is updated synchronously on save and is always
    readable in the same request. Fall back to ``app.storage.browser`` (cookie) and copy into
    ``user`` when only the cookie is set (e.g. returning visitor).
    """
    try:
        val = app.storage.user.get(_EXPLICIT_USER_ID_KEY)
        if val and isinstance(val, str) and val.strip():
            return val.strip()
    except Exception:
        pass
    try:
        val = app.storage.browser.get(_EXPLICIT_USER_ID_KEY)
        if val and isinstance(val, str) and val.strip():
            s = val.strip()
            try:
                app.storage.user[_EXPLICIT_USER_ID_KEY] = s
            except Exception:
                pass
            return s
    except Exception:
        pass
    fb = _test_fallback_storage.get(_EXPLICIT_USER_ID_KEY)
    if fb and isinstance(fb, str) and fb.strip():
        return fb.strip()
    return None


def _get_claimed_explicit_user_ids() -> dict[str, bool]:
    """Registry is dict[str, True] in app.storage.general (JSON-friendly set)."""
    try:
        raw = app.storage.general.get(_CLAIMED_EXPLICIT_USER_IDS_KEY)
        if isinstance(raw, dict):
            return {k: True for k in raw if isinstance(k, str)}
        if isinstance(raw, list):
            return {str(x): True for x in raw if isinstance(x, str)}
    except Exception:
        pass
    return {}


def _set_claimed_explicit_user_ids(claimed: dict[str, bool]) -> None:
    try:
        app.storage.general[_CLAIMED_EXPLICIT_USER_IDS_KEY] = claimed
    except Exception as e:
        logger.warning("Could not persist claimed explicit user IDs: %s", e)


def try_claim_explicit_user_id(value: str) -> Literal["ok", "taken", "invalid"]:
    """
    Register an explicit User ID globally for this process if it is not already claimed.

    Call before set_explicit_user_id. Serialized with _explicit_user_id_registry_lock.
    Returns ``invalid`` if the string does not pass is_valid_explicit_user_id.
    """
    if not value or not isinstance(value, str):
        return "invalid"
    v = value.strip()
    if not is_valid_explicit_user_id(v):
        return "invalid"
    with _explicit_user_id_registry_lock:
        claimed = _get_claimed_explicit_user_ids()
        if v in claimed:
            return "taken"
        claimed[v] = True
        _set_claimed_explicit_user_ids(claimed)
    return "ok"


def release_explicit_user_id_claim(value: Optional[str]) -> None:
    """Remove an explicit User ID from the global registry (e.g. when the user clears / changes ID)."""
    if not value or not isinstance(value, str):
        return
    v = value.strip()
    if not is_valid_explicit_user_id(v):
        return
    with _explicit_user_id_registry_lock:
        claimed = _get_claimed_explicit_user_ids()
        if v in claimed:
            del claimed[v]
            _set_claimed_explicit_user_ids(claimed)


def get_explicit_user_id() -> Optional[str]:
    """
    Get the user-entered ID for job/history association (from startup dialog).
    Returns None when not yet set or when stored value is not a valid demo ID.

    Stored in ``app.storage.user`` and mirrored to ``app.storage.browser`` (see :func:`_read_raw_explicit_user_id`).
    """
    raw = _read_raw_explicit_user_id()
    if not raw:
        return None
    if is_valid_explicit_user_id(raw):
        return raw
    clear_explicit_user_id()
    return None


def set_explicit_user_id(value: str) -> None:
    """
    Store the user-entered ID for job/history association.

    Writes ``app.storage.user`` synchronously (always allowed in handlers). Mirrors to
    ``app.storage.browser`` on the next tick — browser mutation can intermittently fail with
    “response … already been built”; session storage still holds the ID.
    """
    if not value or not isinstance(value, str):
        return
    v = value.strip()
    if not is_valid_explicit_user_id(v):
        return

    try:
        app.storage.user[_EXPLICIT_USER_ID_KEY] = v
        logger.info("Stored explicit user ID in app.storage.user")
    except Exception as e:
        logger.warning("Failed to store explicit user ID in user storage: %s", e)

    try:
        if _runs_under_pytest():
            _test_fallback_storage[_EXPLICIT_USER_ID_KEY] = v
    except Exception:
        pass

    def _mirror_to_browser() -> None:
        try:
            app.storage.browser[_EXPLICIT_USER_ID_KEY] = v
            logger.debug("Mirrored explicit user ID to browser storage")
        except Exception as e:
            logger.debug(
                "Could not mirror explicit user ID to browser storage (session copy still set): %s",
                e,
            )

    _defer_browser_mutation(_mirror_to_browser)


def clear_explicit_user_id() -> None:
    """Forget this browser's User ID and free its global claim.

    Why both steps:
    - **Clear storage** — Jobs and chat use ``get_explicit_user_id()`` / ``get_user_id_for_jobs()``;
      wiping browser storage (and any legacy user key) shows the home prompt again.
    - **Release claim** — Registration reserves each demo ID process-wide; without releasing, that ID
      would stay "taken" forever even after this user leaves, blocking everyone else from reusing it.
    """
    raw = _read_raw_explicit_user_id()

    try:
        app.storage.browser.pop(_EXPLICIT_USER_ID_KEY, None)
        logger.debug("Cleared explicit user ID from app.storage.browser")
    except Exception as e:
        logger.debug("Could not clear from browser storage: %s", e)
    try:
        app.storage.user.pop(_EXPLICIT_USER_ID_KEY, None)
    except Exception as e:
        logger.debug("Could not clear legacy user storage key: %s", e)
    try:
        import os
        if "PYTEST_CURRENT_TEST" in os.environ or "PYTEST_XDIST_WORKER" in os.environ:
            _test_fallback_storage.pop(_EXPLICIT_USER_ID_KEY, None)
    except Exception:
        pass

    if raw and is_valid_explicit_user_id(raw):
        release_explicit_user_id_claim(raw)


def ensure_explicit_user_id_for_tests() -> None:
    """
    Under pytest, set a default explicit user ID when unset so pages that read
    storage stay consistent with patched get_user_id_for_jobs.
    """
    try:
        import os
        if "PYTEST_CURRENT_TEST" not in os.environ and "PYTEST_XDIST_WORKER" not in os.environ:
            return
        if get_explicit_user_id():
            return
        for i in range(32):
            vid = f"demo_t{i:02d}"
            if try_claim_explicit_user_id(vid) == "ok":
                set_explicit_user_id(vid)
                return
    except Exception:
        pass


def ensure_user_id() -> Optional[str]:
    """
    Ensure we have an explicit user ID for job/history association.
    If not set, shows a modal dialog and returns None. The dialog callback
    will store the ID and reload the page, so the handler should return
    immediately when None is returned (page will reload on submit).
    Call when an action needs a stable user id (e.g. jobs list, first chat
    send, or job form submit), not on every page load.
    """
    ensure_explicit_user_id_for_tests()

    existing = get_explicit_user_id()
    if existing:
        return existing

    def on_submit():
        val = (input_field.value or "").strip()
        if not val:
            return
        if not is_valid_explicit_user_id(val):
            from frontend.constants import HOME_USER_ID

            ui.notify(HOME_USER_ID["invalid_format"], type="warning", classes="rb-notify-505759")
            return
        claim = try_claim_explicit_user_id(val)
        if claim == "taken":
            from frontend.constants import HOME_USER_ID

            ui.notify(HOME_USER_ID["id_taken"], type="warning", classes="rb-notify-a2aaad")
            return
        if claim != "ok":
            return
        set_explicit_user_id(val)
        dialog.close()
        ui.timer(0.08, lambda: ui.navigate.reload(), once=True)

    def on_keydown(e):
        if getattr(e, "args", None) and e.args.get("key") == "Enter":
            on_submit()

    with ui.dialog() as dialog, ui.card().classes("p-6 min-w-[320px]"):
        ui.label("Enter your User ID").classes("text-lg font-semibold")
        ui.label(
            "Use this to access yourprevious jobs and chat history."
        ).classes("text-zinc-600 mb-4")
        input_field = ui.input(
            "User ID",
            placeholder="???",
        ).classes("w-full")
        input_field.on("keydown", on_keydown)
        with ui.row().classes("mt-4 justify-end gap-2"):
            ui.button("Continue", on_click=on_submit).classes("rb-brand-primary text-white")

    dialog.open()
    return None


def get_user_id_for_jobs() -> Optional[str]:
    """
    Get user ID for job association. Returns explicit user ID from startup dialog only.
    All jobs are associated with this ID; no IP or session fallback.
    """
    explicit = get_explicit_user_id()
    if explicit:
        return f"user-{explicit}"
    return None


def get_user_id() -> Optional[str]:
    """
    Get NiceGUI user ID for current session.
    
    NiceGUI automatically assigns a unique identifier to each user session.
    This ID persists across page refreshes and can be used to link data
    to specific users.
    
    Returns:
        Optional[str]: User ID if available, None otherwise
    
    Tips:
    - User ID is stable within a browser session
    - Different browsers/tabs get different user IDs
    - Use this to filter conversations and data per user
    """
    try:
        storage_user = app.storage.user
        # Prefer attribute access if present (older/newer NiceGUI may expose .id)
        user_id = getattr(storage_user, "id", None)
        if not user_id:
            # Fallback to dict-like access for FilePersistentDict or similar
            try:
                user_id = storage_user.get("id")
            except Exception:
                user_id = None

        if user_id:
            return user_id

        # If no ID exists, generate a persistent one for this client and store it.
        import uuid
        generated_id = f"session-{uuid.uuid4().hex}"
        try:
            # Try to persist the generated id back into storage_user
            try:
                storage_user["id"] = generated_id
            except Exception:
                # Some storage implementations support attribute assignment
                try:
                    setattr(storage_user, "id", generated_id)
                except Exception as e_attr:
                    logger.warning("Failed to persist generated session id via setattr: %s", e_attr)

            logger.debug("Generated and persisted new session id: %s", generated_id)
            return generated_id
        except Exception as e:
            logger.warning("Failed to persist generated session id: %s", e)
            # Fall through to returning None or test fallback below
    except Exception as e:
        err_msg = str(e)
        # "can only be used within a UI context" is expected when called from background
        # tasks, timers, or after request context ends - use debug to avoid noisy warnings
        if 'UI context' in err_msg or 'ui context' in err_msg.lower():
            # logger.debug("User ID unavailable (no UI context): %s", err_msg)
            pass
        else:
            logger.warning("Error getting user ID: %s", e)
        # In test environments (pytest / no ui.run storage_secret), provide a stable test id
        try:
            import os
            if 'PYTEST_CURRENT_TEST' in os.environ or 'PYTEST_XDIST_WORKER' in os.environ:
                return 'test-user-1'
        except Exception:
            pass
        return None


def get_assigned_demo_folder() -> Optional[str]:
    """
    Get the demo folder assigned to this browser session (Option 1 auto-assign).
    Each session gets one folder from the pool (e.g. /home/tester/Documents/demo1..demo5).
    Once assigned, the same folder is returned for this session. Assigned folders
    are removed from the available pool for other sessions.
    """
    try:
        from frontend.config import DEMO_FOLDERS_BASE, DEMO_FOLDER_NAMES
        user_id = get_user_id()
        if not user_id:
            return None
        # Check if this session already has an assignment
        try:
            existing = app.storage.user.get('assigned_demo_folder')
            if existing:
                return existing
        except Exception:
            pass
        # Assign next available folder
        with _demo_folder_lock:
            assignments = dict(app.storage.general.get('demo_folder_assignments', {}))
            assigned_paths = set(assignments.values())
            for name in DEMO_FOLDER_NAMES:
                path = str(DEMO_FOLDERS_BASE / name)
                if path not in assigned_paths:
                    assignments[user_id] = path
                    app.storage.general['demo_folder_assignments'] = assignments
                    app.storage.user['assigned_demo_folder'] = path
                    logger.info("Assigned demo folder %s to session %s", path, user_id[:12])
                    return path
        logger.warning("No demo folders available for session %s", user_id[:12])
        return None
    except Exception as e:
        logger.warning("Error getting assigned demo folder: %s", e)
        return None


def resolve_demo_folder_for_browser() -> Optional[str]:
    """
    Default directory when opening the file/directory browser from plugin forms.

    Uses the session-assigned ``demo1``..``demo10`` folder when available; otherwise
    the first existing folder under :data:`frontend.config.DEMO_FOLDERS_BASE` from
    that name list. Returns ``None`` if nothing matches (caller falls back to cwd).
    """
    try:
        assigned = get_assigned_demo_folder()
        if assigned:
            p = Path(assigned)
            if p.is_dir():
                return str(p.resolve())
        from frontend.config import DEMO_FOLDERS_BASE, DEMO_FOLDER_NAMES

        base = Path(DEMO_FOLDERS_BASE).expanduser()
        for name in DEMO_FOLDER_NAMES:
            cand = base / name
            if cand.is_dir():
                return str(cand.resolve())
        if base.is_dir():
            return str(base.resolve())
    except Exception as e:
        logger.debug("resolve_demo_folder_for_browser: %s", e)
    return None


def release_demo_folder_for_client(client) -> None:
    """
    Release the demo folder assigned to this client when it is deleted.
    Call from @app.on_delete with client context. Removes the session from
    demo_folder_assignments so the folder becomes available for other sessions.
    """
    try:
        with client:
            user_id = get_user_id()
            if not user_id:
                return
            with _demo_folder_lock:
                assignments = dict(app.storage.general.get('demo_folder_assignments', {}))
                if user_id in assignments:
                    released = assignments.pop(user_id)
                    app.storage.general['demo_folder_assignments'] = assignments
                    logger.debug("Released demo folder %s for deleted session %s", released, user_id[:12])
    except Exception as e:
        logger.warning("Error releasing demo folder for client: %s", e)


def get_current_conversation_id() -> Optional[str]:
    """
    Get current conversation ID from NiceGUI storage.
    
    Retrieves the conversation_id stored in app.storage.user, which persists
    across page refreshes and navigation.
    
    Returns:
        Optional[str]: Current conversation ID if set, None otherwise
    """
    try:
        conversation_id = app.storage.user.get('current_conversation_id')
        if conversation_id:
            logger.debug("Retrieved current conversation ID from storage: %s", conversation_id)
            return conversation_id
        # If storage is available but no value is set, fall back to test storage
        fallback = _test_fallback_storage.get('current_conversation_id')
        if fallback:
            logger.debug("Using fallback current conversation ID from test storage: %s", fallback)
        return fallback
    except Exception as e:
        logger.warning("Error getting current conversation ID: %s", e)
        # Fallback to test storage if available
        return _test_fallback_storage.get('current_conversation_id')


def set_current_conversation_id(conversation_id: Optional[str]):
    """
    Set current conversation ID in NiceGUI storage.
    
    Stores the conversation_id in app.storage.user so it persists across
    page refreshes and navigation.
    
    Args:
        conversation_id (Optional[str]): Conversation ID to store, or None to clear
    
    Tips:
    - Setting to None clears the current conversation
    - This should be updated when creating new conversations
    - Used by ChatbotPage to restore conversation on page reload
    """
    try:
        if conversation_id:
            app.storage.user['current_conversation_id'] = conversation_id
            logger.debug("Stored current conversation ID: %s", conversation_id)
        else:
            # Clear current conversation
            if 'current_conversation_id' in app.storage.user:
                del app.storage.user['current_conversation_id']
            logger.debug("Cleared current conversation ID")
    except Exception as e:
        logger.error("Error setting current conversation ID: %s", e)
        # Fallback for test environment: store in module-level dict
        if conversation_id:
            _test_fallback_storage['current_conversation_id'] = conversation_id
            logger.debug("Fallback stored current conversation ID in test storage: %s", conversation_id)
        else:
            _test_fallback_storage.pop('current_conversation_id', None)
            logger.debug("Fallback cleared current conversation ID in test storage")
        return
    # Also write to fallback storage during test runs so values persist across
    # request-like boundaries used by the NiceGUI test client.
    try:
        import os
        if 'PYTEST_CURRENT_TEST' in os.environ or 'PYTEST_XDIST_WORKER' in os.environ:
            if conversation_id:
                _test_fallback_storage['current_conversation_id'] = conversation_id
            else:
                _test_fallback_storage.pop('current_conversation_id', None)
    except Exception:
        pass


def get_draft_message() -> str:
    """
    Get draft message from client storage.
    
    Retrieves any draft message stored in app.storage.client. Draft messages
    are temporary and cleared when browser cache is cleared.
    
    Returns:
        str: Draft message text, or empty string if none
    """
    try:
        draft = app.storage.client.get('draft_message', '')
        if draft:
            logger.debug("Retrieved draft message (length: %d)", len(draft))
        return draft
    except Exception as e:
        logger.warning("Error getting draft message: %s", e)
        return ''


def set_draft_message(message: str):
    """
    Store draft message in client storage.
    
    Saves a draft message in app.storage.client for temporary persistence.
    
    Args:
        message (str): Draft message text to store
    
    Tips:
    - Use this to preserve message drafts as user types
    - Draft is cleared when browser cache is cleared
    - Consider clearing draft after successful message send
    """
    try:
        if message:
            app.storage.client['draft_message'] = message
            logger.debug("Stored draft message (length: %d)", len(message))
        else:
            # Clear draft
            if 'draft_message' in app.storage.client:
                del app.storage.client['draft_message']
            logger.debug("Cleared draft message")
    except Exception as e:
        logger.warning("Error setting draft message: %s", e)


def get_form_draft() -> Optional[dict]:
    """
    Get form draft data from client storage.
    
    Retrieves any draft form data stored in app.storage.client.
    
    Returns:
        Optional[dict]: Form draft data, or None if none
    """
    try:
        draft = app.storage.client.get('form_draft')
        if draft:
            logger.debug("Retrieved form draft: %s", draft.get('endpoint', 'unknown'))
        return draft
    except Exception as e:
        logger.warning("Error getting form draft: %s", e)
        return None


def set_form_draft(endpoint: str, arguments: dict):
    """
    Store form draft data in client storage.
    
    Saves form draft (endpoint and arguments) in app.storage.client.
    
    Args:
        endpoint (str): API endpoint name
        arguments (dict): Form arguments
    
    Tips:
    - Use this to preserve form state as user fills it out
    - Clear draft after successful form submission
    - Useful for restoring forms after accidental navigation
    """
    try:
        if endpoint and arguments:
            app.storage.client['form_draft'] = {
                'endpoint': endpoint,
                'arguments': arguments
            }
            logger.debug("Stored form draft for endpoint: %s", endpoint)
        else:
            # Clear draft
            if 'form_draft' in app.storage.client:
                del app.storage.client['form_draft']
            logger.debug("Cleared form draft")
    except Exception as e:
        logger.warning("Error setting form draft: %s", e)


def set_conversation_to_load(conversation_id: str, conversation_data: dict, messages: list):
    """
    Store conversation data for loading into the chat.

    This temporarily stores conversation data in client storage so it can be
    loaded by the chatbot page when it initializes.

    Args:
        conversation_id: Unique conversation identifier
        conversation_data: Conversation metadata dictionary
        messages: List of message dictionaries

    Returns:
        None
    """
    logger.debug("Storing conversation for loading: %s", conversation_id)
    app.storage.user['conversation_to_load'] = {
        'conversation_id': conversation_id,
        'conversation_data': conversation_data,
        'messages': messages
    }


def get_conversation_to_load():
    """
    Retrieve stored conversation data for loading.

    Gets and clears the stored conversation data that was set for loading.

    Returns:
        Optional[dict]: Conversation data with keys:
            - 'conversation_id': str
            - 'conversation_data': dict
            - 'messages': list
        Returns None if no conversation is stored for loading
    """
    try:
        conversation_data = app.storage.user.get('conversation_to_load')
        if conversation_data:
            # Clear the stored data after retrieving
            try:
                del app.storage.user['conversation_to_load']
            except Exception:
                pass
            logger.debug("Retrieved conversation for loading: %s", conversation_data.get('conversation_id'))
            return conversation_data
    except Exception as e:
        logger.warning("app.storage.user not available, falling back to test storage: %s", e)
        # Try fallback storage
        conv = _test_fallback_storage.get('conversation_to_load')
        if conv:
            # remove after returning
            _test_fallback_storage.pop('conversation_to_load', None)
            logger.debug("Retrieved conversation for loading from fallback: %s", conv.get('conversation_id'))
            return conv
    return None


def clear_conversation_to_load():
    """
    Clear any stored conversation data for loading.

    Returns:
        None
    """
    if 'conversation_to_load' in app.storage.user:
        del app.storage.user['conversation_to_load']
        logger.debug("Cleared stored conversation data")

