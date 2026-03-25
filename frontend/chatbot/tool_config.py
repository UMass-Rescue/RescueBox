# frontend/chatbot/tool_config.py
"""
Advanced Tool Configuration and Schema Management for RescueBox

This module provides comprehensive tool configuration for the Granite model,
including strict Pydantic schemas, dynamic tool definition generation,
and advanced prompting techniques for multi-tool chaining.

Key Features:
- Strict tool schemas with validation
- Editable tool configuration at runtime
- Advanced few-shot prompting for tool chaining
- Dynamic schema generation from tool mappings
"""

import json
import logging
from typing import List, Any, Optional, Literal
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ==========================================
# Tool Schemas (Strict)
# ==========================================
class TextSummarize(BaseModel):
    input_dir: str = Field(..., description="Path to input text")
    output_dir: str = Field(..., description="Path to save summary")
    model: Literal["gemma3:1b", "gemma3:4b"] = Field(..., description="The text summarize model version")

class ImageSummarize(BaseModel):
    input_dir: str = Field(..., description="Path to input images")
    output_dir: str = Field(..., description="Path to save summaries")
    model: Literal["gemma3:4b", "gemma3:27b"] = Field(..., description="The vision model version")

class AudioTranscribe(BaseModel):
    input_dir: str = Field(..., description="Path to input audio")

class AgeGenderPredict(BaseModel):
    image_directory: str = Field(..., description="Path to image directory")

class FaceFindBulk(BaseModel):
    query_directory: str = Field(..., description="Path to query images")
    collection_name: str = Field("default", description="Database collection")
    similarity_threshold: float = Field(0.75, description="Confidence threshold")

class FaceBulkUpload(BaseModel):
    directory_path: str = Field(..., description="Path to upload")
    collection_name: str = Field(..., description="Target collection")
    dropdown_collection_name: str = Field(..., description="UI selection")

class DeepfakeDetection(BaseModel):
    input_dataset: str = Field(..., description="Input path")
    output_file: str = Field(..., description="Output report path")
    facecrop: str = Field("true", description="Face crop settings")

class FileSystemScan(BaseModel):
    """
    List files in a directory to check content types.
    Use this when the user asks 'Is there a file?', 'Check folder content', or before running heavy tools.
    """
    directory_path: str = Field(..., description="The path to scan")


class TextSearch(BaseModel):
    """
    Semantic search over text files. Use after image_summary to search image descriptions.
    Chains from image_summary output_dir when user says 'summarize and search for X'.
    """
    input_dir: str = Field(..., description="Directory of text files (or image summary output)")
    query: str = Field(..., description="Search query (e.g. 'kid with brown clothes')")


# Legacy support for backward compatibility
class RescueBoxToolCall(BaseModel):
    name: Literal[
        "audio/transcribe",
        "age-gender/predict",
        "text_summarization/summarize",
        "image_summary/summarize-images",
        "text_embeddings/search",
        "face-match/findfacebulk",
        "face-match/bulkupload",
        "deepfake_detection/predict",
        "rescuebox/unknown",
    ]
    arguments: dict

class ToolCallList(BaseModel):
    calls: List[RescueBoxToolCall] = Field(..., description="List of tool calls (legacy format)")


# ==========================================
# Tool Configuration (Editable)
# ==========================================
SCHEMA_MAP = {
    "audio/transcribe": AudioTranscribe,
    "age-gender/predict": AgeGenderPredict,
    "text_summarization/summarize": TextSummarize,
    "image_summary/summarize-images": ImageSummarize,
    "text_embeddings/search": TextSearch,
    "face-match/findfacebulk": FaceFindBulk,
    "face-match/bulkupload": FaceBulkUpload,
    "deepfake_detection/predict": DeepfakeDetection,
    "rescuebox/unknown": FileSystemScan,
}


def get_available_tools() -> dict[str, type[BaseModel]]:
    """
    Get the current schema map of available tools.

    Returns:
        dict[str, type[BaseModel]]: Mapping of tool names to their schema classes.
    """
    return SCHEMA_MAP.copy()


def update_tool_schema(tool_name: str, schema_class: type[BaseModel]) -> None:
    """
    Update or add a tool schema to the SCHEMA_MAP.

    Args:
        tool_name: The tool endpoint name (e.g., "audio/transcribe")
        schema_class: The Pydantic model class for the tool's parameters
    """
    SCHEMA_MAP[tool_name] = schema_class


def remove_tool_schema(tool_name: str) -> None:
    """
    Remove a tool schema from the SCHEMA_MAP.

    Args:
        tool_name: The tool endpoint name to remove
    """
    if tool_name in SCHEMA_MAP:
        del SCHEMA_MAP[tool_name]

def generate_tool_definitions() -> list[dict]:
    """
    Generate tool definitions for the Granite model prompt.

    This function dynamically creates the tool definitions from the current schema map,
    which can be modified at runtime using the configuration functions.

    Returns:
        list[dict]: List of tool definition dictionaries for the model prompt.
    """
    tools_definitions = []

    for name, model in get_available_tools().items():
        json_schema = model.model_json_schema()
        if "title" in json_schema:
            del json_schema["title"]
        tools_definitions.append({
            "type": "function",
            "function": {
                "name": name,
                "description": json_schema.get("description", ""),
                "parameters": json_schema
            }
        })

    return tools_definitions


def create_advanced_granite_prompt(user_query: str) -> list[dict[str, str]]:
    """
    Creates an advanced structured prompt for the Granite model with comprehensive tool chaining.

    Uses dynamic schema generation and few-shot prompting for intelligent multi-tool orchestration.

    Args:
        user_query (str): The user's natural language request.

    Returns:
        list[dict[str, str]]: A list of message dictionaries for chat completion.
    """
    # Generate Dynamic Schema for the prompt
    tools_definitions = generate_tool_definitions()

    # ==========================================
    # FEW-SHOT PROMPTING (The Secret Sauce)
    # ==========================================

    # 1. System Rule
    system_msg = {
        "role": "system",
        "content": (
            "You are a forensic analysis assistant for RescueBox.\n"
            "RULES:\n"
            "1. CHAINING: If the user requests multiple actions, generate a LIST of tools.\n"
            "2. EXHAUSTIVE: You must generate a tool call for EVERY verb in the request. Do not stop until all actions are covered. Pick fuction name \"rescuebox/unknown\" when there is no clear match \n"
            "3. SHARED CONTEXT: If a path appears once, apply it to ALL relevant tools (Backward or Forward).\n"
            "4. DEFAULTING: Infer required arguments (like output paths) from the input path.\n\n"
            f"<tools>{json.dumps(tools_definitions)}</tools>"
        )
    }

    ex_a_user = {"role": "user", "content": "In /cases/c10, summarize the photos and check for deepfakes"}
    ex_a_asst = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "function": {
                    "name": "image_summary/summarize-images",
                    "arguments": {"input_dir": "/cases/c10", "output_dir": "/cases/c10/summary", "model": "gemma3:4b"}
                }
            },
            {
                "function": {
                    "name": "deepfake_detection/predict",
                    "arguments": {"input_dataset": "/cases/c10", "output_file": "/cases/c10/report.json", "facecrop": "true"}
                }
            }
        ]
    }

    # 3. Example B: Path at END (Distribute Backward)
    # "Summarize and Check /cases/c10"
    ex_b_user = {"role": "user", "content": "Summarize images and detect fakes in /evidence/batch2"}
    ex_b_asst = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "function": {
                    "name": "image_summary/summarize-images",
                    "arguments": {"input_dir": "/evidence/batch2", "output_dir": "/evidence/batch2/summary", "model": "gemma3:4b"}
                }
            },
            {
                "function": {
                    "name": "deepfake_detection/predict",
                    "arguments": {"input_dataset": "/evidence/batch2", "output_file": "/evidence/batch2/report.json", "facecrop": "true"}
                }
            }
        ]
    }

    # 4. Example C: The "Chain of 3" (Crucial Fix)
    ex_c_user = {"role": "user", "content": "detect age/gender in /data/evidence/batch5, then detect fakes, describe the images"}
    ex_c_asst = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "function": {
                    "name": "age-gender/predict",
                    "arguments": {"image_directory": "/data/evidence/batch5"}
                }
            },
            {
                "function": {
                    "name": "deepfake_detection/predict",
                    "arguments": {"input_dataset": "/data/evidence/batch5", "output_file": "/data/evidence/batch5/report.json", "facecrop": "true"}
                }
            },
            {
                "function": {
                    "name": "image_summary/summarize-images",
                    "arguments": {"input_dir": "/data/evidence/batch5", "output_dir": "/data/evidence/batch5/summary", "model": "gemma3:4b"}
                }
            }
        ]
    }

    # 5. Example E: Age-gender + Summarize + Search (image_summary -> text_embeddings pipeline)
    ex_e_user = {"role": "user", "content": "detect age and gender of faces in /tmp, summarize, and search for a kid with brown clothes"}
    ex_e_asst = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "function": {
                    "name": "age-gender/predict",
                    "arguments": {"image_directory": "/tmp"}
                }
            },
            {
                "function": {
                    "name": "image_summary/summarize-images",
                    "arguments": {"input_dir": "/tmp", "output_dir": "/tmp/summaries", "model": "gemma3:4b"}
                }
            },
            {
                "function": {
                    "name": "text_embeddings/search",
                    "arguments": {"input_dir": "/tmp/summaries", "query": "kid with brown clothes"}
                }
            }
        ]
    }
    ex_d_user = {"role": "user", "content": "Summarize images in /evidence/batch2"}
    ex_d_asst = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "function": {
                    "name": "image_summary/summarize-images",
                    "arguments": {"input_dir": "/evidence/batch2", "output_dir": "/evidence/batch2/summary", "model": "gemma3:4b"}
                }
            },
        ]
    }

    # Build complete message list
    messages = [
        system_msg,
        ex_a_user, ex_a_asst,  # Teach Pattern A
        ex_b_user, ex_b_asst,  # Teach Pattern B
        ex_c_user, ex_c_asst,  # Teach Pattern C
        ex_e_user, ex_e_asst,  # Teach Pattern E: age-gender + summarize + search
        ex_d_user, ex_d_asst,
        {"role": "user", "content": user_query}  # Real Query
    ]

    return messages


def parse_tool_calls_response(response_text: str) -> Optional[list[dict[str, Any]]]:
    """
    Parse the Granite model's tool calls response into a list of tool call dictionaries.

    Handles the standard Granite tool calling format with tool_calls array.

    Args:
        response_text (str): Raw response text from the model (JSON string)

    Returns:
        Optional[list[dict[str, Any]]]: List of tool call dictionaries, or None if parsing fails
    """
    try:
        tool_calls = []
        # response_text is already the content string from the model response
        data = json.loads(response_text)
        tool_list = ToolCallList(**data)

        for i, tool_call in enumerate(tool_list.calls, 1):
            logger.info("--- [Task %d] ---", i)
            logger.info("Function: %s", tool_call.name)
            logger.info("Arguments: %s", tool_call.arguments)

            tool_calls.append({
                'name': tool_call.name,
                'arguments': tool_call.arguments
            })

        if tool_calls:
            for call in tool_calls:
                if call.get('name') == 'unknown':
                    logger.info("⚠️  No valid tool calls found")
                    return None
            xml_output = f"<tool_code>{json.dumps(data['calls'])}</tool_code>"
            logger.debug("formatted_output: %s", xml_output)
            return tool_calls
        else:
            logger.warning("⚠️  No valid tool calls found")
            return None

    except Exception as e:
        logger.error("❌ Error parsing model output: %s", str(e))
        logger.error("Raw Output: %s", response_text)
        return None
