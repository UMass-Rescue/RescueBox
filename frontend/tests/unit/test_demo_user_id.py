"""Unit tests for demo User ID format validation."""

import pytest

from frontend.constants import (
    DEMO_USER_ID_PREFIX,
    is_valid_explicit_user_id,
)


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, False),
        ("", False),
        ("wrong", False),
        (DEMO_USER_ID_PREFIX, False),
        (DEMO_USER_ID_PREFIX + "x", False),
        (DEMO_USER_ID_PREFIX + "abc", False),
        (DEMO_USER_ID_PREFIX + "ab", True),
        (DEMO_USER_ID_PREFIX + "7!", True),
        (" " + DEMO_USER_ID_PREFIX + "ab", True),
    ],
)
def test_is_valid_explicit_user_id(value, expected):
    assert is_valid_explicit_user_id(value) is expected
