"""Tests for chat_layout_context and safe_ui helpers."""

import unittest
from unittest.mock import MagicMock

import pytest

from frontend.pages.chatbot import (
    is_ephemeral_ui_error,
    resolve_chat_container,
    safe_ui_call,
)
from frontend.utils.ui import _safe_ui_call, safe_ui_call as utils_safe_ui_call
from unittest.mock import patch
from nicegui import context


class TestEphemeralUiError(unittest.TestCase):
    def test_deleted_client(self):
        self.assertTrue(is_ephemeral_ui_error(RuntimeError("The client is deleted")))

    def test_slot_undetermined(self):
        self.assertTrue(
            is_ephemeral_ui_error(RuntimeError("slot cannot be determined"))
        )

    def test_real_error_not_ephemeral(self):
        self.assertFalse(is_ephemeral_ui_error(ValueError("bad input")))


class TestSafeUiCall(unittest.TestCase):
    def test_same_canonical_function(self):
        self.assertIs(safe_ui_call, utils_safe_ui_call)
        self.assertIs(_safe_ui_call, utils_safe_ui_call)

    def test_swallows_ephemeral(self):
        def boom():
            raise RuntimeError("client deleted")

        self.assertIsNone(safe_ui_call(boom))

    def test_reraises_other(self):
        def boom() -> None:
            raise ValueError("x")

        with self.assertRaises(ValueError):
            safe_ui_call(boom)

    def test_returns_value(self):
        def add(a, b):
            return a + b

        self.assertEqual(safe_ui_call(add, 2, 3), 5)

    def test_check_slot_skips_when_no_slot(self):

        called = False

        def fn():
            nonlocal called
            called = True
            return 42

        with patch.object(type(context), "slot_stack", property(lambda self: [])):
            result = safe_ui_call(fn, check_slot=True)
            self.assertIsNone(result)
            self.assertFalse(called)

    def test_check_slot_always_calls_mock(self):
        mock_fn = MagicMock(return_value="mocked")
        result = safe_ui_call(mock_fn, check_slot=True)
        self.assertEqual(result, "mocked")
        mock_fn.assert_called_once()


@pytest.mark.asyncio
async def test_safe_ui_call_async_swallows_ephemeral():
    async def async_boom():
        raise RuntimeError("slot cannot be determined")

    result = await safe_ui_call(async_boom)
    assert result is None


@pytest.mark.asyncio
async def test_safe_ui_call_async_reraises_other():
    async def async_boom():
        raise TypeError("unexpected type")

    with pytest.raises(TypeError):
        await safe_ui_call(async_boom)


class TestResolveChatContainer(unittest.TestCase):
    def test_explicit_wins_by_default(self):
        class _El:
            pass

        a, b = _El(), _El()
        self.assertIs(resolve_chat_container(a), a)
        self.assertIs(resolve_chat_container(b), b)


if __name__ == "__main__":
    unittest.main()
