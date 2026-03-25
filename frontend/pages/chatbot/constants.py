"""
Chatbot Constants

This module contains configuration constants used across the chatbot components.
"""

# Configuration constants
class FormConfig:
    """Configuration constants for form styling and behavior."""

    # Card styling
    TOOL_PICKER_CLASSES = (
        'w-full max-w-md min-w-0 mx-auto bg-gradient-to-br from-purple-50 to-violet-100 '
        'border-2 border-purple-500 shadow-md rounded-xl text-base'
    )
    ANALYSIS_PICKER_CLASSES = 'w-full max-w-md bg-green-50 border-2 border-green-500 text-sm'
    SUCCESS_CARD_CLASSES = 'w-full max-w-md bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-400 shadow-lg rounded-xl overflow-hidden text-sm'
    RESULT_DETAIL_CLASSES = 'w-full max-w-2xl max-h-[70vh] bg-white rounded-xl shadow-xl overflow-hidden text-sm'

    # Icon mapping for result types
    RESULT_ICONS = {
        'file': 'insert_drive_file',
        'directory': 'folder',
        'batchfile': 'folder_shared',
        'batchtext': 'library_books',
        'text': 'article',
        'markdown': 'description',
    }

    # Title templates for result types
    RESULT_TITLES = {
        'file': 'File Result ({count} item{plural})',
        'directory': 'Directory Result ({count} item{plural})',
        'batchfile': 'File Result ({count} files)',
        'batchtext': 'Text Result ({count} items)',
        'text': 'Text Result ({count} item{plural})',
        'markdown': 'Markdown Result ({count} item{plural})',
    }

    # Analysis options
    ANALYSIS_OPTIONS = {
        1: {'name': 'transcribe Audio Files', 'desc': 'Convert audio files to text'},
        2: {'name': 'summarize photos in /tmp', 'desc': 'describe images'},
        3: {'name': 'detect faces', 'desc': 'detect faces in photos'},
        4: {'name': 'summarize text documents', 'desc': 'Generate summaries of text content'},
        5: {'name': 'predict age or gender', 'desc': 'Predict age or gender from images'},
    }
