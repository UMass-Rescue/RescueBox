# frontend/chatbot/multi_tool_handler.py
"""
Compatibility facade for Granite multi-tool and pipeline utilities.

The implementation is split into focused modules under ``frontend.chatbot.multi_tool``
to keep this import path stable for existing callers and tests.
"""

from frontend.chatbot.multi_tool import (
    MultiToolCallResult,
    apply_metadata_filter,
    batch_items_have_age_gender_metadata,
    chain_output_to_input,
    coerce_pipeline_response,
    extract_batch_file_items,
    extract_output_path,
)

__all__ = [
    "MultiToolCallResult",
    "apply_metadata_filter",
    "batch_items_have_age_gender_metadata",
    "chain_output_to_input",
    "coerce_pipeline_response",
    "extract_batch_file_items",
    "extract_output_path",
]
