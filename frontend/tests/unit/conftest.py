"""Unit-test-specific fixtures (shared fixtures come from tests/conftest.py)."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def reset_storage_registry():
    """Reset fallback test storage between unit tests."""
    from frontend.utils.storage import reset_test_storage

    reset_test_storage()
