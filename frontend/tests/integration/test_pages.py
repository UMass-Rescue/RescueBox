"""
Integration tests for pages using NiceGUI User fixture (USES MOCKS)

NOTE: This file uses mocks for API clients.
For tests with real API dependencies, see test_pages_integration.py

This file is kept for fast unit-style testing of page UI logic.
"""

import pytest
import asyncio
from nicegui.testing import User  # type: ignore
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from frontend.tests.integration.chatbot_ui_helpers import (
    assert_chatbot_header_visible,
    find_chat_textarea,
    open_chatbot_and_wait_for_ready,
)


class TestIndexPage:
    """Tests for index/home page"""
    
    @pytest.mark.asyncio
    async def test_index_page_loads(self, user: User):
        """Test index page loads correctly"""
        await user.open('/')
        await user.should_see('Welcome to RescueBox')
        await user.should_see('Browse Plugins')
        await user.should_see('Open Assistant')
    
    @pytest.mark.asyncio
    async def test_index_page_navigation(self, user: User):
        """Test navigation buttons on index page"""
        await user.open('/')
        
        # Check that navigation links exist
        # (ui.open is called, not actual navigation in test environment)
        browse_button = user.find('Browse Plugins')
        assert browse_button is not None
        
        assistant_button = user.find('Open Assistant')
        assert assistant_button is not None


class TestChatbotPage:
    """Tests for chatbot page (before models tests to avoid NiceGUI client state issues)."""

    @pytest.mark.asyncio
    async def test_chatbot_page_loads(self, user: User):
        """Test chatbot page loads correctly"""
        await open_chatbot_and_wait_for_ready(user)
        await assert_chatbot_header_visible(user)
        try:
            await user.should_see('Type your request')
        except AssertionError:
            await user.should_see('Type in a rescuebox')
        await user.should_see('Send')
        await user.should_see('New Conversation')

    @pytest.mark.asyncio
    async def test_chatbot_creates_conversation(self, user: User):
        """Test that chatbot creates conversation on load"""
        from frontend.utils.nicegui_storage import get_current_conversation_id
        from frontend.database import get_chat_history_db

        await user.open('/chatbot')
        await asyncio.sleep(0.2)

        # Wait a moment for async initialization
        await asyncio.sleep(0.1)

        # Check that conversation ID is stored
        conv_id = get_current_conversation_id()
        assert conv_id is not None

        # Verify conversation exists in database
        chat_history_db = get_chat_history_db()
        conversation = await chat_history_db.get_conversation(conv_id)
        assert conversation is not None

    @pytest.mark.asyncio
    async def test_chatbot_help_command(self, user: User):
        """Test help command in chatbot"""
        await open_chatbot_and_wait_for_ready(user)
        textarea = find_chat_textarea(user)
        textarea.type('/help')

        # Click send button
        send_button = user.find('Send')
        send_button.click()

        # Should see help content
        await user.should_see('RescueBox Assistant')
        await user.should_see('Shortcut Commands')

    @pytest.mark.asyncio
    async def test_chatbot_tool_picker_command(self, user: User):
        """Test tool picker command"""
        await open_chatbot_and_wait_for_ready(user)
        textarea = find_chat_textarea(user)
        textarea.type('/models')

        # Click send button
        send_button = user.find('Send')
        send_button.click()

        # Tool picker UI (see ToolPicker / show_tool_picker_dialog)
        await user.should_see('Plugin Selector')
        await user.should_see('Click on a plugin')

    @pytest.mark.asyncio
    async def test_chatbot_slash_command(self, user: User):
        """Test slash command flow"""

        # Mock schema response
        mock_schema_response = AsyncMock()
        mock_schema_response.json.return_value = {
            'inputs': [{
                'key': 'input_dir',
                'label': 'Input Directory',
                'subtitle': 'Directory containing audio files',
                'inputType': 'directory'
            }],
            'parameters': []
        }
        mock_schema_response.raise_for_status = AsyncMock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.get.return_value = mock_schema_response
            mock_client.aclose = AsyncMock()

            await open_chatbot_and_wait_for_ready(user)
            textarea = find_chat_textarea(user)
            textarea.type('/transcribe')

            # Click send button
            send_button = user.find('Send')
            send_button.click()

            # Wait briefly for form generation / async processing
            await asyncio.sleep(0.1)

            # Should see form or tool selection (form generation happens asynchronously)

        # Type and send message (prepend a space to avoid merging with previous content)
        textarea = find_chat_textarea(user)
        textarea.type(' Find faces in my images')

        user.find('Send').click()

        # Should see tool selection message and the selected endpoint
        await user.should_see('Selected Tool')
        await user.should_see('audio/transcribe')

        # Should eventually see form (after schema is loaded)
        # Note: This is async, so may need wait or better async handling


class TestModelsPage:
    """Tests for models listing page"""
    
    @pytest.mark.asyncio
    async def test_models_page_loads(self, user: User, mock_api_client):
        """Test models page loads with mocked API"""
        # Setup mock API response
        mock_response = AsyncMock()
        mock_response.json.return_value = [
            {
                'uid': 'model-123',
                'name': 'Test Model',
                'version': '1.0.0',
                'author': 'Test Author',
                'gpu': False
            }
        ]
        mock_response.raise_for_status = AsyncMock()
        mock_response.status_code = 200
        
        mock_api_client.get.return_value = mock_response
        
        # Mock servers endpoint
        mock_servers_response = AsyncMock()
        mock_servers_response.json.return_value = []
        mock_servers_response.raise_for_status = AsyncMock()
        mock_servers_response.status_code = 200
        
        # Setup side_effect for multiple GET calls
        mock_api_client.get.side_effect = [
            mock_response,  # /models
            mock_servers_response,  # /servers
        ]
        
        await user.open('/models')
        await user.should_see('Available Plugins')
        
    
    @pytest.mark.asyncio
    async def test_models_page_displays_models(self, user: User, mock_api_client):
        """Test models page displays model cards"""
        # Setup mock responses
        mock_models_response = AsyncMock()
        mock_models_response.json.return_value = [
            {
                'uid': 'model-123',
                'name': 'Face Detection',
                'version': '2.0.0',
                'author': 'RescueBox Team',
                'gpu': True
            }
        ]
        mock_models_response.raise_for_status = AsyncMock()
        mock_models_response.status_code = 200
        
        mock_servers_response = AsyncMock()
        mock_servers_response.json.return_value = []
        mock_servers_response.raise_for_status = AsyncMock()
        mock_servers_response.status_code = 200
        
        mock_api_client.get.side_effect = [
            mock_models_response,
            mock_servers_response,
        ]
        
        await user.open('/models')
        
        # Should see at least one model card with a README button and version label
        await user.should_see('README')
        await user.should_see('v')


class TestJobsPage:
    """Tests for jobs listing page"""
    
    @pytest.mark.asyncio
    async def test_jobs_page_loads(self, user: User):
        """Test jobs page loads correctly"""
        # Import the module directly (jobs_page is a route handler, not directly importable)
        # The route is registered via @ui.page decorator, so we just test the route
        await user.open('/jobs')
        
        # Should see jobs page content
        await user.should_see('Jobs')
        await user.should_see('Jobs')
        await user.should_see('Refresh')
    
    @pytest.mark.asyncio
    async def test_jobs_page_displays_jobs(self, user: User, mock_api_client):
        """Test jobs page displays job rows (jobs load from SQLite; API is mocked for model names)."""
        mock_model_response = MagicMock()
        mock_model_response.status_code = 200
        mock_model_response.json = Mock(return_value={'uid': 'model-123', 'name': 'Test Model'})
        mock_api_client.get = AsyncMock(return_value=mock_model_response)

        mock_db = MagicMock()
        mock_db.get_all_jobs = AsyncMock(
            return_value=[
                {
                    'uid': 'job-123',
                    'modelUid': 'model-123',
                    'status': 'Completed',
                    'startTime': '2024-01-01T10:00:00Z',
                    'endTime': '2024-01-01T10:05:00Z',
                    'request': {},
                    'taskSchema': {},
                }
            ]
        )

        with patch('frontend.database.get_job_db', return_value=mock_db):
            with patch('frontend.pages.jobs.jobs.api_client', mock_api_client):
                await user.open('/jobs')

        await user.should_see('Completed')
        await user.should_see('View')


class TestLogsPage:
    """Tests for logs page"""

    @pytest.mark.asyncio
    async def test_logs_page_loads(self, user: User):
        """Test logs page loads correctly"""
        await user.open('/logs')

        # Should see logs page content
        await user.should_see('Application Logs')
        await user.should_see('Refresh')
        await user.should_see('Log file:')