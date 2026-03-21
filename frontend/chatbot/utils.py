# frontend/chatbot/utils.py
"""
Utility Functions for Chatbot Operations

This module provides utility functions for argument normalization and input filtering.
These functions help ensure consistent data formats and filter out invalid requests.

Key Functions:
- normalize_arguments: Maps argument key variations to standardized names
- is_rescuebox_request: Validates if input is a valid forensic request
- get_rejection_message: Generates user-friendly rejection messages
"""

import logging
import re
from typing import Dict, Any, Tuple
from frontend.chatbot.config import ToolRegistry

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def normalize_arguments(user_args: Dict[str, Any], endpoint: str = "") -> Dict[str, Any]:
    """
    Normalize user argument keys to match API expectations.
    
    This function maps common key variations to standardized API parameter names.
    For example, it converts "input_directory", "input_path", "input", "path",
    "directory", or "folder" all to the standard "input_dir" key.
    
    The function also handles endpoint-specific overrides where certain endpoints
    expect different parameter names even after general normalization.
    
    Args:
        user_args (Dict[str, Any]): Dictionary of arguments from tool call or user input.
            Keys may use various formats (e.g., "input_directory", "input_dir")
        endpoint (str): Endpoint name for endpoint-specific normalization overrides.
            Used to apply special cases (e.g., age_gender expects "image_directory")
        
    Returns:
        Dict[str, Any]: Dictionary with normalized argument keys matching API expectations.
            Original values are preserved, only keys are normalized.
    
    Examples:
        >>> normalize_arguments({"input_directory": "/tmp", "output_path": "/out"})
        {'input_dir': '/tmp', 'output_dir': '/out'}
        
    >>> normalize_arguments({"input_dir": "/tmp"}, endpoint="age-gender/predict")
    {'image_directory': '/tmp'}  # Special override for age-gender endpoint
    
    Tips:
    - Always pass the endpoint name when available for accurate normalization
    - Unknown keys are preserved as-is (no mapping found)
    - Normalization is case-insensitive (INPUT_DIRECTORY -> input_dir)
    - Endpoint-specific overrides take precedence over general mappings
    """
    logger.info("Normalizing arguments for endpoint: %s", endpoint or 'generic')
    logger.debug("Input arguments: %s", list(user_args.keys()))
    
    key_mappings = {
        "input_directory": "input_dir",
        "input_path": "input_dir",
        "input": "input_dir",
        "path": "input_dir",
        "directory": "input_dir",
        "folder": "input_dir",
        "output_directory": "output_dir",
        "output_path": "output_dir",
        "output": "output_dir",
        "faces_directory": "directory_path",
        "face_directory": "directory_path",
        "query_path": "query_directory",
        "query": "query_directory",
        "collection": "collection_name",
        "threshold": "similarity_threshold",
        "media_directory": "input_dataset",
        "videos": "input_dataset",
        "report": "output_file",
        "crop": "facecrop",
    }
    
    normalized = {}
    for key, value in user_args.items():
        key_lower = key.lower()
        new_key = key_mappings.get(key_lower, key)
        
        # Endpoint-specific overrides (from rescuebox_tool.py)
        if ("age_gender" in endpoint or "age-gender" in endpoint) and new_key == "input_dir":
            new_key = "image_directory"
            logger.debug("Applied age-gender override: %s -> %s", key, new_key)
        elif "deepfake" in endpoint and new_key == "input_dir":
            new_key = "input_dataset"
            logger.debug("Applied deepfake override: %s -> %s", key, new_key)
        elif "bulk_upload" in endpoint and new_key == "input_dir":
            new_key = "directory_path"
            logger.debug("Applied bulk_upload override: %s -> %s", key, new_key)
        elif "find_face" in endpoint and new_key == "input_dir":
            new_key = "query_directory"
            logger.debug("Applied find_face override: %s -> %s", key, new_key)
        elif key != new_key:
            logger.debug("Mapped key: %s -> %s", key, new_key)
        
        normalized[new_key] = value
    
    logger.info("Normalization complete. Output keys: %s", list(normalized.keys()))
    return normalized


def is_rescuebox_request(user_input: str, filter_enabled: bool = True) -> Tuple[bool, str]:
    """
    Check if input is a valid RescueBox forensic request.
    
    This function validates user input to determine if it's a legitimate forensic
    analysis request. It uses keyword matching, pattern blocking, and path detection
    to filter out non-forensic requests like weather queries, jokes, recipes, etc.
    
    The validation process:
    1. If filtering is disabled, always returns True
    2. Allows internal commands (starting with /) from tool picker
    3. Checks against blocked patterns (non-forensic keywords)
    4. Checks for RescueBox keywords (forensic-related terms)
    5. Checks for file paths (indicators of file operations)
    6. Returns False if none of the above match
    
    Args:
        user_input (str): User input string to validate
        filter_enabled (bool): Whether input filtering is enabled. Defaults to True.
            Set to False to bypass all filtering (useful for testing)
        
    Returns:
        tuple[bool, str]: A tuple containing:
            - is_valid (bool): True if the input is a valid forensic request
            - reason (str): One of:
                - "filter_disabled": Filtering is disabled, request allowed
                - "internal_command": Internal command from tool picker (starts with /)
                - "keyword_match": Contains forensic keywords
                - "path_detected": Contains file path indicators
                - "non_forensic": Matches blocked patterns (weather, jokes, etc.)
                - "no_match": Doesn't match any forensic indicators
    
    Examples:
        >>> is_rescuebox_request("transcribe audio in /tmp/recordings")
        (True, 'keyword_match')
        
        >>> is_rescuebox_request("what's the weather today?")
        (False, 'non_forensic')
        
        >>> is_rescuebox_request("process files in /evidence")
        (True, 'path_detected')
    
    Tips:
    - Use filter_enabled=False during development for easier testing
    - Add new keywords to ToolRegistry.RESCUEBOX_KEYWORDS to expand matching
    - Blocked patterns use regex, so be careful with special characters
    - Path detection uses a simple regex pattern - may need adjustment for edge cases
    """
    logger.info("Checking if request is valid RescueBox request (filter_enabled=%s)", filter_enabled)
    
    if not filter_enabled:
        logger.debug("Filter disabled - allowing all requests")
        return True, "filter_disabled"
    
    input_lower = user_input.lower().strip()
    logger.debug("Checking input (length=%d): %s...", len(user_input), user_input[:50])

    # Allow internal commands (starting with /) - these come from tool picker
    if user_input.strip().startswith('/'):
        logger.info("Request validated as internal command: %s", user_input)
        return True, "internal_command"

    # Check blocked patterns first
    for pattern in ToolRegistry.BLOCKED_PATTERNS:
        if re.search(pattern, input_lower):
            logger.info("Request blocked by pattern: %s...", pattern[:30])
            return False, "non_forensic"

    # Check for RescueBox keywords
    for keyword in ToolRegistry.RESCUEBOX_KEYWORDS:
        if keyword in input_lower:
            logger.info("Request validated by keyword match: '%s'", keyword)
            return True, "keyword_match"

    # Check if a file path is mentioned
    if re.search(r'[/\\][\w\-\.]+[/\\]?', user_input):
        logger.info("Request validated by path detection")
        return True, "path_detected"

    logger.info("Request did not match any validation criteria")
    return False, "no_match"


def get_rejection_message(reason: str) -> str:
    """
    Get appropriate rejection message based on rejection reason.
    
    This function generates user-friendly markdown messages explaining why a
    request was rejected and providing guidance on how to make valid requests.
    
    The messages are designed to:
    - Clearly explain what RescueBox does (forensic analysis only)
    - Provide examples of valid requests
    - Guide users on proper usage
    
    Args:
        reason (str): The rejection reason from is_rescuebox_request().
            Expected values: "non_forensic" or "no_match"
        
    Returns:
        str: Formatted markdown message suitable for display in the UI.
            The message includes headers, tables, and example usage.
    
    Examples:
        >>> get_rejection_message("non_forensic")
        "## 🚫 Request Not Supported\n\nI am **RescueBox Forensic Assistant**..."
        
        >>> get_rejection_message("no_match")
        "## ❓ I Didn't Understand Your Request\n\nI am **RescueBox Forensic Assistant**..."
    
    Tips:
    - Messages are in markdown format for rich display in UI
    - Add more examples to help users understand valid request formats
    - Consider internationalization if supporting multiple languages
    - Messages should be concise but informative
    """
    logger.info("Generating rejection message for reason: %s", reason)
    
    if reason == "non_forensic":
        logger.debug("Using non_forensic rejection message")
        return """## 🚫 Request Not Supported

I am **RescueBox Forensic Assistant** - I only handle forensic analysis tasks.

### What I CAN Do:

| Task | Example |
|------|---------|
| 🎤 **Transcribe Audio** | "Transcribe recordings in /evidence/audio" |
| 🖼️ **Describe Images** | "Describe photos in /case/images" |
| 👤 **Age & Gender** | "Classify faces in /suspects" |
| 🔍 **Detect Deepfakes** | "Check /evidence/videos for deepfakes" |
| 📤 **Upload Faces** | "Upload faces from /known to suspects collection" |
| 🔎 **Find Faces** | "Find matching faces in /unknown" |
| 📝 **Summarize Text** | "Summarize documents in /case/reports" |

Please rephrase your request as a forensic analysis task."""
    else:  # no_match
        logger.debug("Using no_match rejection message")
        return """#### I am a **RescueBox Forensic Assistant**.


#### these are some prompt **Examples:**

* Transcribe audio in /evidence/recordings

* Detect deepfakes in /case/videos

* Detect age and gender of faces in /suspects/unknown

* Describe images in /evidence/photos

Type `/help` for detailed instructions."""


def calculate_text_area_height(text_length: int, min_height: int = 24, max_height: int = 96) -> str:
    """
    Calculate appropriate Tailwind height class for text content areas.

    This function determines the optimal height for scrollable text areas based on
    content length, ensuring readable layouts without excessive whitespace.

    Args:
        text_length (int): Number of characters in the text content
        min_height (int): Minimum Tailwind height class number (default: 8 = 32px)
        max_height (int): Maximum Tailwind height class number (default: 64 = 256px)

    Returns:
        str: Tailwind height class (e.g., 'h-32', 'h-48', 'h-64')

    Examples:
        >>> calculate_text_area_height(100)   # Short text
        'h-35'
        >>> calculate_text_area_height(683)   # Your Twinkle Twinkle lyrics
        'h-96'
        >>> calculate_text_area_height(2000)  # Very long text
        'h-96'

    Notes:
        - Assumes ~25 characters per line of readable text
        - Adds 40px padding for UI elements
        - Scales between min_height and max_height.
        - Returns Tailwind class numbers (where 1 unit = 0.25rem = 4px)
    """
    if text_length <= 0:
        return f'h-{min_height}'

    # Estimate lines: ~25 chars per line
    text_lines = text_length // 25 + 1

    # Calculate pixel height: 20px per line + 40px padding
    estimated_height_px = text_lines * 20 + 40

    # Convert to Tailwind class units (1 unit = 4px), with bounds
    height_class_num = min(max(estimated_height_px // 4, min_height), max_height)

    return f'h-{height_class_num}'