"""Tests for chat_layout_context, safe_ui, and MessageSendParams wiring."""

import unittest

from frontend.pages.chatbot.utils.chat_layout_context import resolve_chat_container
from frontend.pages.chatbot.utils.safe_ui import is_ephemeral_ui_error, safe_ui_call


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
    def test_swallows_ephemeral(self):
        def boom():
            raise RuntimeError("client deleted")

        self.assertIsNone(safe_ui_call(boom))

    def test_reraises_other(self):
        def boom():
            raise ValueError("x")

        with self.assertRaises(ValueError):
            safe_ui_call(boom)


class TestResolveChatContainer(unittest.TestCase):
    def test_explicit_wins_by_default(self):
        class _El:
            pass

        a, b = _El(), _El()
        self.assertIs(resolve_chat_container(a), a)
        self.assertIs(resolve_chat_container(b), b)


if __name__ == "__main__":
    unittest.main()
