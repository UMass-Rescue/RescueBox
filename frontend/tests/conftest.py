"""
Shared test fixtures and configuration for all test modules.

This file contains common fixtures, constants, and utilities used across
all test modules to reduce duplication and ensure consistency.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from nicegui import app
import asyncio

# Test constants
TEST_CONVERSATION_ID = "conv-123"
TEST_USER_ID = "user-456"
TEST_FILE_PATH = "/tmp/test.txt"
TEST_DIR_PATH = "/tmp/test_dir"

# Sample data structures
SAMPLE_CONVERSATION_DATA = {
    "conversation_id": TEST_CONVERSATION_ID,
    "conversation_data": {
        "title": "Test Conversation",
        "created_at": "2024-01-01T10:00:00",
    },
}

SAMPLE_RESPONSE_BODY = {
    "task_id": "task-123",
    "status": "completed",
    "result": {
        "type": "file",
        "data": {"filename": "output.txt", "content": "Test content"},
    },
}


@pytest.fixture
def temp_directory(tmp_path):
    """Create a temporary directory for testing."""
    return tmp_path


@pytest.fixture
def sample_file(temp_directory):
    """Create a sample file for testing."""
    file_path = temp_directory / "sample.txt"
    file_path.write_text("Sample file content")
    return str(file_path)


@pytest.fixture
def sample_directory(temp_directory):
    """Create a sample directory with files for testing."""
    test_dir = temp_directory / "test_data"
    test_dir.mkdir()

    # Create some sample files
    (test_dir / "file1.txt").write_text("Content 1")
    (test_dir / "file2.txt").write_text("Content 2")

    return str(test_dir)


@pytest.fixture
def mock_api_client():
    """Mock API client for testing."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock()
    mock_client.post = AsyncMock()
    return mock_client


@pytest.fixture
def mock_database():
    """Mock database with async methods."""
    mock_db = MagicMock()
    mock_db.get_conversation = AsyncMock(
        return_value={"title": "Test Conversation", "created_at": "2024-01-01"}
    )
    mock_db.get_messages = AsyncMock(
        return_value=[{"role": "user", "content": "Hello"}]
    )
    mock_db.save_message = AsyncMock()
    return mock_db


@pytest.fixture
def mock_chatbot():
    """Mock chatbot instance."""
    chatbot = MagicMock()
    chatbot.state_manager = MagicMock()
    chatbot.state_manager.conversation_id = TEST_CONVERSATION_ID
    chatbot.state_manager.messages = []
    return chatbot


@pytest.fixture
def mock_ui():
    """Mock NiceGUI ui module for testing."""
    with patch("frontend.components.shared.ui") as mock_ui:
        # Mock common UI elements
        mock_container = MagicMock()
        mock_ui.column.return_value = mock_container
        mock_ui.row = MagicMock()
        mock_ui.label = MagicMock()
        mock_ui.button = MagicMock()
        mock_ui.card = MagicMock()
        mock_ui.icon = MagicMock()
        yield mock_ui


@pytest.fixture
def sample_task_schema():
    """Create sample task schema for testing."""
    from rb.api.models import (
        TaskSchema,
        InputSchema,
        ParameterSchema,
        InputType,
        RangedFloatParameterDescriptor,
        FloatRangeDescriptor,
        EnumParameterDescriptor,
        EnumVal,
    )

    return TaskSchema(
        inputs=[
            InputSchema(
                key="input_dir", label="Input Directory", inputType=InputType.DIRECTORY
            ),
            InputSchema(key="prompt", label="Prompt", inputType=InputType.TEXT),
        ],
        parameters=[
            ParameterSchema(
                key="confidence",
                label="Confidence",
                value=RangedFloatParameterDescriptor(
                    range=FloatRangeDescriptor(min=0.0, max=1.0), default=0.8
                ),
            ),
            ParameterSchema(
                key="mode",
                label="Processing Mode",
                value=EnumParameterDescriptor(
                    enumVals=[
                        EnumVal(key="fast", value="fast", label="Fast"),
                        EnumVal(key="accurate", value="accurate", label="Accurate"),
                    ],
                    default="fast",
                ),
            ),
        ],
    )


@pytest.fixture
def sample_response_body():
    """Create sample response body for testing."""
    from rb.api.models import ResponseBody, FileResponse, FileType

    # Create a FileResponse first
    file_response = FileResponse(
        filename="output.txt",
        content="Test content",
        file_type=FileType.TEXT,
        path="/tmp/output.txt",
        title="Output Image",
    )

    # Create ResponseBody with the file response as the root value
    # ResponseBody appears to be a RootModel that takes the root object as a positional arg
    return ResponseBody(file_response)


@pytest.fixture
def sample_files():
    """Create sample file paths for testing."""
    return {
        "text_file": "/tmp/sample.txt",
        "image_file": "/tmp/sample.jpg",
        "audio_file": "/tmp/sample.mp3",
        "directory": "/tmp/sample_dir",
    }


@pytest_asyncio.fixture
async def user():
    """NiceGUI User fixture for integration testing."""
    import httpx
    from nicegui.testing import User
    from nicegui import ui

    # Ensure NiceGUI core has a running loop so background tasks can be created
    # during tests (nicegui.background_tasks.create asserts core.loop is set).
    import asyncio as _asyncio
    from nicegui import core as nice_core

    # Use the running loop if available, otherwise get the default event loop.
    try:
        nice_core.loop = _asyncio.get_running_loop()
    except RuntimeError:
        nice_core.loop = _asyncio.get_event_loop()
    # Also set the loop on the background_tasks module's core reference
    try:
        from nicegui import background_tasks as _bg

        _bg.core.loop = nice_core.loop
    except Exception:
        # non-critical; if background_tasks isn't importable here, it'll be set later
        pass
    # Ensure background_tasks.create sets core.loop if it's still None during calls
    try:
        from nicegui import background_tasks as _bg_tasks

        _orig_bg_create = _bg_tasks.create

        def _wrapped_bg_create(
            coroutine, *, name: str = "unnamed task", handle_exceptions: bool = True
        ):
            import asyncio as _asyncio_local

            try:
                if _bg_tasks.core.loop is None:
                    try:
                        _bg_tasks.core.loop = _asyncio_local.get_running_loop()
                    except RuntimeError:
                        _bg_tasks.core.loop = _asyncio_local.get_event_loop()
            except Exception:
                # If anything goes wrong, fall back to original behavior
                pass
            return _orig_bg_create(
                coroutine, name=name, handle_exceptions=handle_exceptions
            )

        _bg_tasks.create = _wrapped_bg_create
    except Exception:
        pass

    # Ensure app.config has required attributes to avoid AttributeErrors during page resolution
    if not hasattr(app.config, "title"):
        app.config.title = "RescueBox"
    if not hasattr(app.config, "viewport"):
        app.config.viewport = "width=device-width, initial-scale=1"
    if not hasattr(app.config, "favicon"):
        app.config.favicon = None
    if not hasattr(app.config, "dark"):
        app.config.dark = None
    if not hasattr(app.config, "language"):
        app.config.language = "en-US"
    if not hasattr(app.config, "tailwind"):
        app.config.tailwind = True
    if not hasattr(app.config, "quasar_config"):
        app.config.quasar_config = {}
    if not hasattr(app.config, "prod_js"):
        app.config.prod_js = True

    # Initialize NiceGUI app context properly
    # Import the main module to ensure all pages are registered
    try:
        import importlib

        importlib.import_module("frontend.main")
    except ImportError:
        pass

    # Provide fake storage objects for tests so get_user_id and other storage helpers work
    class _FakeUserStorage(dict):
        def __init__(self):
            super().__init__()
            # provide a predictable test id that tests expect to start with 'test-user'
            self.id = "test-user-1"

        def get(self, key, default=None):
            return super().get(key, default)

    try:
        app.storage.user = _FakeUserStorage()
        app.storage.client = {}
        app.storage.general = {}
    except Exception:
        # If app.storage is not available for some reason, ignore — tests will handle missing storage
        pass
    # Ensure ui.ref exists for older NiceGUI APIs used in form builders
    try:
        if not hasattr(ui, "ref"):

            def _simple_ref(initial=None):
                class _Ref:
                    def __init__(self, v):
                        self.value = v

                return _Ref(initial)

            ui.ref = _simple_ref
    except Exception:
        pass
    # Patch get_user_id and get_user_id_for_jobs to provide stable test ids when storage/IP unavailable.
    try:
        import frontend.utils as _ngs

        _orig_get_user_id = _ngs.get_user_id
        _orig_get_user_id_for_jobs = _ngs.get_user_id_for_jobs

        def _test_get_user_id():
            try:
                val = _orig_get_user_id()
                if val:
                    return val
            except Exception:
                pass
            return "test-user-1"

        def _test_get_user_id_for_jobs():
            try:
                val = _orig_get_user_id_for_jobs()
                if val:
                    return val
            except Exception:
                pass
            return "user-rb_demo_0408_00"

        def _test_ensure_user_id():
            _ngs.set_explicit_user_id("rb_demo_0408_00")
            return "rb_demo_0408_00"

        _ngs.get_user_id = _test_get_user_id
        _ngs.get_user_id_for_jobs = _test_get_user_id_for_jobs
        _ngs.ensure_user_id = _test_ensure_user_id
    except Exception:
        pass
    # Ensure rb.api.models.FileType has TXT alias for compatibility with older tests
    try:
        import rb.api.models as _rbm

        if hasattr(_rbm, "FileType") and not hasattr(_rbm.FileType, "TXT"):
            setattr(_rbm.FileType, "TXT", getattr(_rbm.FileType, "TEXT", None))
    except Exception:
        pass

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        _user = User(client)

        # Add a convenience click method expected by some integration tests:
        async def _click(el, *args, **kwargs):
            import asyncio as _asyncio

            fn = getattr(el, "click", None)
            if fn:
                res = fn(*args, **kwargs)
                if _asyncio.iscoroutine(res):
                    await res
                return res
            trig = getattr(el, "trigger", None)
            if trig:
                res = trig("click")
                if _asyncio.iscoroutine(res):
                    await res
                return res
            raise AttributeError("Element not clickable")

        setattr(_user, "click", _click)
        # Expose the NiceGUI app object on the User fixture for tests that register pages via user.app.page
        try:
            # Expose the NiceGUI ui module on the User fixture so tests can register pages via user.app.page
            from nicegui import ui as _nicegui_ui

            setattr(_user, "app", _nicegui_ui)
        except Exception:
            pass
        yield _user


# Ensure background task creation is safe under pytest's event loop.
# Some NiceGUI versions assert that core.loop is set when creating background tasks
# during page rendering; tests run under pytest-asyncio's loop and may not set that.
# This autouse fixture patches `nicegui.background_tasks.create` to set core.loop
# to the running loop when needed, then delegates to the original implementation.
@pytest.fixture(autouse=True, scope="session")
def _patch_nicegui_background_tasks():
    try:
        import nicegui.background_tasks as _bg

        _orig_create = _bg.create

        def _wrapped_create(
            coroutine, *, name: str = "unnamed task", handle_exceptions: bool = True
        ):
            # Create tasks on the currently running loop to avoid using a possibly-closed core.loop.
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.get_event_loop()

            # Normalize awaitable/coroutine
            if asyncio.iscoroutine(coroutine):
                real_coroutine = coroutine
            else:

                async def _wrap_awaitable():
                    return await coroutine

                real_coroutine = _wrap_awaitable()

            task = loop.create_task(real_coroutine)

            if handle_exceptions:

                def _handle_done(t: asyncio.Task):
                    try:
                        _ = t.result()
                    except asyncio.CancelledError:
                        pass
                    except Exception:
                        try:
                            import logging

                            logging.getLogger("nicegui").exception(
                                "Background task exception"
                            )
                        except Exception:
                            pass

                task.add_done_callback(_handle_done)

            return task

        _bg.create = _wrapped_create
        yield
    except Exception:
        # If we cannot patch, tests will proceed unmodified
        yield


# Utility functions for tests
def create_mock_message(role, content, message_id=None):
    """Create a mock message for testing."""
    from frontend.database import ChatMessageRecord

    return ChatMessageRecord(
        message_id=message_id or f"msg-{role[:3]}",
        conversation_id=TEST_CONVERSATION_ID,
        role=role,
        content=content,
        timestamp="2024-01-01T10:00:00Z",
    )


def assert_messages_equal(actual, expected):
    """Assert that two message lists are equal."""
    assert len(actual) == len(expected)
    for a, e in zip(actual, expected):
        assert a.role == e.role
        assert a.content == e.content


# Context managers for common mocking patterns
def mock_ui_operations():
    """Context manager to mock UI operations."""
    return patch.multiple("nicegui.ui", notify=MagicMock(), navigate=MagicMock())


def mock_storage_operations():
    """Context manager to mock storage operations."""
    return patch.object(app.storage, "client", {})
