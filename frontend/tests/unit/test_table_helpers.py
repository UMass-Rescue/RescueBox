"""
Unit tests for table helper utilities
"""

import pytest
from nicegui.testing import User
from nicegui import ui
from typing import List, Dict
from pathlib import Path
import sys

# Add backend models to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / 'src' / 'rb-api' / 'rb'))

from frontend.components.results.table_helpers import (
    create_sortable_table,
    create_metadata_table_columns,
    create_file_row_click_handler,
    create_directory_row_click_handler,
)


class TestTableHelpers:
    """Tests for table helper utilities"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_sortable_table(self, user: User):
        """Test creating a sortable table"""
        columns = [
            {'name': 'col1', 'label': 'Column 1', 'field': 'col1', 'align': 'left', 'sortable': True},
            {'name': 'col2', 'label': 'Column 2', 'field': 'col2', 'align': 'left', 'sortable': True},
        ]
        rows = [
            {'col1': 'value1', 'col2': 'value2'},
            {'col1': 'value3', 'col2': 'value4'},
        ]
        
        @ui.page('/test')
        def test_page():
            container = ui.column()
            create_sortable_table(
                container,
                columns,
                rows,
                row_key='col1'
            )
        
        await user.open('/test')
        await user.should_see('Column 1')
        await user.should_see('Column 2')
        await user.should_see('value1')
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_sortable_table_with_tip(self, user: User):
        """Test creating a sortable table with tip message"""
        columns = [{'name': 'col1', 'label': 'Column 1', 'field': 'col1', 'align': 'left', 'sortable': True}]
        rows = [{'col1': 'value1'}]
        
        @ui.page('/test')
        def test_page():
            container = ui.column()
            create_sortable_table(
                container,
                columns,
                rows,
                row_key='col1',
                tip_message='Test tip message'
            )
        
        await user.open('/test')
        await user.should_see('Test tip message')
    
    def test_create_metadata_table_columns(self):
        """Test creating columns with metadata keys"""
        base_columns = [
            {'name': 'path', 'label': 'Path', 'field': 'path', 'align': 'left', 'sortable': True},
            {'name': 'title', 'label': 'Title', 'field': 'title', 'align': 'left', 'sortable': True},
        ]
        metadata_keys = ['Age', 'Gender', 'Bounding Box']
        
        columns = create_metadata_table_columns(base_columns, metadata_keys)
        
        assert len(columns) == 5  # 2 base + 3 metadata
        assert columns[0]['name'] == 'path'
        assert columns[2]['name'] == 'age'
        assert columns[2]['label'] == 'Age'
        assert columns[3]['label'] == 'Gender'
        assert all(col['sortable'] for col in columns)
    
    def test_create_file_row_click_handler(self):
        """Test creating file row click handler"""
        rows = [
            {'path_full': '/path/to/file1.txt', 'filename': 'file1.txt'},
            {'path_full': '/path/to/file2.txt', 'filename': 'file2.txt'},
        ]
        
        clicked_paths = []
        def mock_open_file(path):
            clicked_paths.append(path)
        
        handler = create_file_row_click_handler(rows, mock_open_file)
        
        # Simulate click on first row (index 0)
        class MockEvent:
            def __init__(self):
                self.args = [None, 0]  # row index is second arg
        
        handler(MockEvent())
        assert clicked_paths == ['/path/to/file1.txt']
    
    def test_create_directory_row_click_handler(self):
        """Test creating directory row click handler"""
        rows = [
            {'path_full': '/path/to/dir1', 'path': 'dir1'},
            {'path_full': '/path/to/dir2', 'path': 'dir2'},
        ]
        
        clicked_paths = []
        def mock_open_folder(path):
            clicked_paths.append(path)
        
        handler = create_directory_row_click_handler(rows, mock_open_folder)
        
        # Simulate click on second row (index 1)
        class MockEvent:
            def __init__(self):
                self.args = [None, 1]  # row index is second arg
        
        handler(MockEvent())
        assert len(clicked_paths) == 1
        assert clicked_paths[0] == '/path/to/dir2'
    
    def test_create_file_row_click_handler_fallback_to_path(self):
        """Test file row click handler falls back to 'path' if 'path_full' not present"""
        rows = [
            {'path': '/path/to/file1.txt', 'filename': 'file1.txt'},  # No path_full
        ]
        
        clicked_paths = []
        def mock_open_file(path):
            clicked_paths.append(path)
        
        handler = create_file_row_click_handler(rows, mock_open_file)
        
        class MockEvent:
            def __init__(self):
                self.args = [None, 0]
        
        handler(MockEvent())
        assert clicked_paths == ['/path/to/file1.txt']

