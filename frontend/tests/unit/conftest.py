"""
Shared test fixtures and configuration for all test modules.

This file contains common fixtures, constants, and utilities used across
all test modules to reduce duplication and ensure consistency.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from nicegui import app

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


@pytest.fixture(autouse=True)
def reset_storage_registry():
    """Automatically reset the test fallback storage between tests."""
    from frontend.utils.storage import reset_test_storage

    reset_test_storage()


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
        pass
    except Exception:
        pass

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield User(client)


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
