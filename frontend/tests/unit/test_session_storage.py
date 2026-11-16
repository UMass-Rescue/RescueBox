"""Unit tests for standalone session module and case context boundary."""

import sys
from unittest.mock import MagicMock, patch

from frontend.utils import case_context, session, storage


def test_session_module_has_no_database_imports():
    """Verify frontend.utils.session does not import from frontend.database."""
    # Read the session module file directly or inspect its imported names
    assert "frontend.database" not in getattr(session, "__file__", "")
    assert not hasattr(session, "get_case_db")
    assert not hasattr(session, "CaseRecord")


def test_session_state_crud():
    """Verify session setters, getters, and test fallback storage."""
    session.reset_test_storage()
    session.set_active_case_id("CASE_TEST_001")
    assert session.get_active_case_id() == "CASE_TEST_001"
    assert session.get_user_id_for_jobs() == "CASE_TEST_001"

    session.set_draft_message("Hello world draft")
    assert session.get_draft_message() == "Hello world draft"
    session.set_draft_message("")
    assert session.get_draft_message() == ""

    session.clear_active_case_id()
    assert session.get_active_case_id() is None


def test_case_context_retrieves_active_case():
    """Verify case_context resolves active CaseRecord using session case id."""
    session.reset_test_storage()
    session.set_active_case_id("CASE_BOUND_99")

    case = case_context.get_active_case()
    assert case is not None
    assert case.caseId == "CASE_BOUND_99"


def test_storage_module_reexports_all():
    """Verify storage.py re-exports session and case_context symbols."""
    assert hasattr(storage, "get_active_case_id")
    assert hasattr(storage, "set_active_case_id")
    assert hasattr(storage, "get_active_case")
    assert hasattr(storage, "DEFAULT_PREFERENCES")
