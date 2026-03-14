"""
Models Utilities

This module provides shared utilities and common setup for the models package.
"""

import logging
from pathlib import Path
import sys
from typing import Dict, Any, Optional

# Setup backend path for imports
def setup_models_path():
    """Setup backend path for models module imports."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'src'))

# Configure logging for models package
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def extract_model_info(model_info, model_info_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract model information from various sources.

    Provides a standardized way to extract model metadata from AppMetadata objects
    and fallback dictionaries.

    Args:
        model_info: AppMetadata object or None
        model_info_dict: Dictionary fallback for model information

    Returns:
        Dict[str, Any]: Dictionary containing extracted model information
    """
    if model_info:
        return {
            'info': model_info.info,
            'version': model_info.version,
            'author': model_info.author,
            'name': getattr(model_info, 'name', 'Unknown'),
            'description': getattr(model_info, 'description', ''),
        }
    else:
        return {
            'info': model_info_dict.get('info', 'No documentation available.'),
            'version': model_info_dict.get('version', 'N/A'),
            'author': model_info_dict.get('author', 'N/A'),
            'name': model_info_dict.get('name', 'Unknown'),
            'description': model_info_dict.get('description', ''),
        }
