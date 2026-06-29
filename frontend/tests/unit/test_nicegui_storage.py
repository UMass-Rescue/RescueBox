"""
Integration tests for NiceGUI storage utilities.

NOTE: These tests require a running NiceGUI server and are marked as integration tests.
They test the actual NiceGUI storage functionality in a browser-like environment using
the NiceGUI User fixture. Run with: pytest -m integration

These tests validate that storage operations work correctly in the full NiceGUI
application context, including user sessions, browser storage, and server-side state.
"""

import pytest
from nicegui.testing import User  # type: ignore

# Test constants
TEST_CONVERSATION_ID = "test-conversation-123"
TEST_USER_ID_PREFIX = "test-user"
TEST_DRAFT_MESSAGE = "This is a test draft message"
TEST_DRAFT_DATA = {"field1": "value1", "field2": "value2"}


class TestNiceGUIStorage:
    """Integration tests for NiceGUI storage utilities.

    These tests validate the full NiceGUI storage functionality including:
    - User identification and session management
    - Conversation state persistence across requests
    - Draft message storage and retrieval
    - Form data preservation during user interactions

    All tests require a running NiceGUI server instance.
    """

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_user_id(self, user: User):
        """Test user ID generation and retrieval.

        Verifies that each user session gets a unique identifier
        that persists across page requests and can be used for
        user-specific data storage and session management.
        """
        from nicegui import ui
        from frontend.utils import get_user_id

        @ui.page("/test")
        async def test_page():
            user_id = get_user_id()
            assert user_id is not None
            assert isinstance(user_id, str)
            # NiceGUI may supply a client id; our storage fallback uses session-{uuid}.
            assert user_id.startswith(TEST_USER_ID_PREFIX) or user_id.startswith(
                "session-"
            )

        await user.open("/test")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_current_conversation_id_none(self, user: User):
        """Test conversation ID retrieval when no conversation is active.

        Validates that the system correctly handles requests for current
        conversation when no conversation has been set, returning either
        None or a valid string identifier.
        """
        from frontend.utils import get_current_conversation_id
        from nicegui import ui

        @ui.page("/test")
        async def test_page():
            conv_id = get_current_conversation_id()
            # Should return None if not set, or a valid string if set elsewhere
            assert conv_id is None or isinstance(conv_id, str)

        await user.open("/test")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_set_and_get_current_conversation_id(self, user: User):
        """Test conversation ID storage and retrieval.

        Ensures that conversation context persists across page interactions,
        allowing users to maintain their current conversation state as they
        navigate through different parts of the application.
        """
        from frontend.utils import (
            set_current_conversation_id,
            get_current_conversation_id,
        )
        from nicegui import ui

        @ui.page("/test")
        async def test_page():
            # Set conversation ID in storage
            set_current_conversation_id(TEST_CONVERSATION_ID)

            # Verify it can be retrieved correctly
            conv_id = get_current_conversation_id()
            assert conv_id == TEST_CONVERSATION_ID

        await user.open("/test")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_clear_current_conversation_id(self, user: User):
        """Test conversation ID clearing functionality.

        Validates that conversation context can be properly cleared,
        allowing users to start fresh conversations or reset their
        current session state as needed.
        """
        from frontend.utils import (
            set_current_conversation_id,
            get_current_conversation_id,
        )
        from nicegui import ui

        @ui.page("/test")
        async def test_page():
            # Set and verify conversation ID exists
            set_current_conversation_id(TEST_CONVERSATION_ID)
            assert get_current_conversation_id() == TEST_CONVERSATION_ID

            # Clear conversation context
            set_current_conversation_id(None)
            conv_id = get_current_conversation_id()
            assert conv_id is None

        await user.open("/test")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_draft_message_empty(self, user: User):
        """Test getting draft message when none exists"""
        from frontend.utils import get_draft_message

        from nicegui import ui

        @ui.page("/test")
        async def test_page():
            draft = get_draft_message()
            assert draft == ""

        await user.open("/test")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_set_and_get_draft_message(self, user: User):
        """Test setting and getting draft message"""
        from frontend.utils import set_draft_message, get_draft_message

        test_draft = "This is a draft message"

        from nicegui import ui

        @ui.page("/test")
        async def test_page():
            # Set draft
            set_draft_message(test_draft)

            # Get it back
            draft = get_draft_message()
            assert draft == test_draft

        await user.open("/test")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_clear_draft_message(self, user: User):
        """Test clearing draft message"""
        from frontend.utils import set_draft_message, get_draft_message

        from nicegui import ui

        @ui.page("/test")
        async def test_page():
            # Set draft
            set_draft_message("test draft")
            assert get_draft_message() == "test draft"

            # Clear it
            set_draft_message("")
            assert get_draft_message() == ""

        await user.open("/test")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_form_draft_none(self, user: User):
        """Test getting form draft when none exists"""
        from frontend.utils import get_form_draft

        from nicegui import ui

        @ui.page("/test")
        async def test_page():
            draft = get_form_draft()
            assert draft is None

        await user.open("/test")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_set_and_get_form_draft(self, user: User):
        """Test setting and getting form draft"""
        from frontend.utils import set_form_draft, get_form_draft

        test_endpoint = "face-detection/findface"
        test_arguments = {"input_dir": "/tmp/images"}

        from nicegui import ui

        @ui.page("/test")
        async def test_page():
            # Set form draft
            set_form_draft(test_endpoint, test_arguments)

            # Get it back
            draft = get_form_draft()
            assert draft is not None
            assert draft["endpoint"] == test_endpoint
            assert draft["arguments"] == test_arguments

        await user.open("/test")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_clear_form_draft(self, user: User):
        """Test clearing form draft"""
        from frontend.utils import set_form_draft, get_form_draft

        from nicegui import ui

        @ui.page("/test")
        async def test_page():
            # Set draft
            set_form_draft("audio/transcribe", {"key": "value"})
            assert get_form_draft() is not None

            # Clear it (set with empty values)
            set_form_draft("", {})
            draft = get_form_draft()
            assert draft is None

        await user.open("/test")


class TestUserPreferences:
    """Tests for user preferences management"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_user_preferences_defaults(self, user: User):
        """Test getting user preferences with defaults"""
        from frontend.utils import get_user_preferences

        from nicegui import ui

        @ui.page("/test")
        async def test_page():
            prefs = get_user_preferences()

            # Check that all default keys exist
            assert "dark_mode" in prefs
            assert "compact_view" in prefs
            assert "auto_scroll" in prefs
            assert "message_timestamp_format" in prefs
            assert "notifications_enabled" in prefs
            assert "chat_history_limit" in prefs

            # Check default values
            assert prefs["dark_mode"] is False
            assert prefs["auto_scroll"] is True
            assert prefs["message_timestamp_format"] == "relative"

        await user.open("/test")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_set_and_get_user_preference(self, user: User):
        """Test setting and getting a single preference"""
        from frontend.utils import set_user_preference, get_user_preference

        from nicegui import ui

        @ui.page("/test")
        async def test_page():
            # Set preference
            set_user_preference("dark_mode", True)

            # Get it back
            value = get_user_preference("dark_mode")
            assert value is True

        await user.open("/test")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_set_user_preferences_multiple(self, user: User):
        """Test setting multiple preferences at once"""
        from frontend.utils import set_user_preferences, get_user_preferences

        from nicegui import ui

        @ui.page("/test")
        async def test_page():
            # Set multiple preferences
            set_user_preferences(
                {"dark_mode": True, "compact_view": True, "auto_scroll": False}
            )

            # Get all preferences
            prefs = get_user_preferences()
            assert prefs["dark_mode"] is True
            assert prefs["compact_view"] is True
            assert prefs["auto_scroll"] is False

        await user.open("/test")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_user_preference_with_default(self, user: User):
        """Test getting preference with custom default"""
        from frontend.utils import get_user_preference

        from nicegui import ui

        @ui.page("/test")
        async def test_page():
            # Get non-existent preference with default
            value = get_user_preference("nonexistent_key", "default_value")
            assert value == "default_value"

        await user.open("/test")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_reset_user_preferences(self, user: User):
        """Test resetting preferences to defaults"""
        from frontend.utils import (
            set_user_preference,
            reset_user_preferences,
            get_user_preferences,
        )

        from nicegui import ui

        @ui.page("/test")
        async def test_page():
            # Set custom preferences
            set_user_preference("dark_mode", True)
            set_user_preference("auto_scroll", False)

            # Reset to defaults
            reset_user_preferences()

            # Check defaults restored
            prefs = get_user_preferences()
            assert prefs["dark_mode"] is False  # Default value
            assert prefs["auto_scroll"] is True  # Default value

        await user.open("/test")
