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
    """
    Write text captions/descriptions for each image (vision-language summaries saved as files).
    This is NOT CLIP image search and NOT semantic search over text—use image_embeddings/search_images
    for visual search, and text_embeddings/search to search already-written summary text.
    """
    input_dir: str = Field(..., description="Folder of images to caption/summarize")
    output_dir: str = Field(..., description="Folder where per-image text summaries are written")
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


class UfdrMount(BaseModel):
    """
    Mount a UFDR (.ufdr) forensic archive read-only via FUSE. Use when the user asks to mount UFDR,
    open a .ufdr file, or Cellebrite/UFED export. Run this FIRST; later tools use mount_name as the image folder path.
    """
    ufdr_file: str = Field(..., description="Absolute path to the .ufdr file")
    mount_name: str = Field(
        ...,
        description="Empty mount directory path or name (e.g. /mnt/case1 or case1 — see server rules for mnt/)",
    )


class TextSearch(BaseModel):
    """
    Semantic search over plain text files (including caption .txt files produced by image_summary/summarize-images).
    Use for 'search the summaries', 'search text for', 'find in descriptions' AFTER summaries exist in input_dir.
    Do NOT use for searching raw pixels—use image_embeddings/search_images for visual/CLIP search.
    """
    input_dir: str = Field(..., description="Folder of .txt files to search (often the image summary output_dir)")
    query: str = Field(..., description="Text query over written content (e.g. 'kid with brown clothes')")

class ImageSearch(BaseModel):
    """
    CLIP text-to-image search: ranks images in a folder by visual similarity to the query.
    Use for 'image search', 'find images of', 'search photos for', visual match—reads pixels, not summary files.
    Does not require image_summary first; input_dir is the folder of images (e.g. a mounted UFDR path).
    """
    input_dir: str = Field(..., description="Directory of image files to embed and search within")
    query: str = Field(..., description="Visual/concept query for CLIP (e.g. 'young kid', 'red jacket')")

# Legacy support for backward compatibility
class RescueBoxToolCall(BaseModel):
    name: Literal[
        "audio/transcribe",
        "age-gender/predict",
        "text_summarization/summarize",
        "image_summary/summarize-images",
        "text_embeddings/search",
        "image_embeddings/search_images",
        "ufdr_mounter/mount",
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
    "image_embeddings/search_images": ImageSearch,
    "ufdr_mounter/mount": UfdrMount,
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
            "1. CHAINING: If the user requests multiple actions, generate a LIST of tools in execution order.\n"
            "2. EXHAUSTIVE: Emit one tool call per distinct action. Use \"rescuebox/unknown\" only when no tool fits.\n"
            "3. SHARED CONTEXT: Reuse paths across tools; after ufdr_mounter/mount, use mount_name as input_dir for image tools.\n"
            "4. DEFAULTING: Infer output_dir for summaries (e.g. <folder>/summary) when omitted.\n"
            "5. IMAGE SUMMARIZE (captions): image_summary/summarize-images writes text descriptions of images. "
            "Phrases: \"summarize images\", \"describe photos\", \"caption images\".\n"
            "6. TEXT SEARCH vs IMAGE SEARCH (do not confuse):\n"
            "   - text_embeddings/search = semantic search over TEXT FILES (e.g. outputs of image_summary). "
            "Use when the user wants to search written summaries/descriptions for a phrase.\n"
            "   - image_embeddings/search_images = CLIP search over IMAGE PIXELS in a folder. "
            "Use when the user says \"image search\", \"search images for\", \"find photos of\", visual similarity.\n"
            "7. BOTH summarize AND image-search on the same folder: emit image_summary/summarize-images AND "
            "image_embeddings/search_images with the SAME input_dir (same image folder); order mount first if UFDR applies.\n"
            "8. SUMMARIZE + TEXT SEARCH pipeline: If the user wants summaries AND to search those written descriptions, use "
            "image_summary/summarize-images then text_embeddings/search with input_dir = that output_dir.\n"
            "9. UFDR: If the user mentions mounting UFDR/.ufdr, emit ufdr_mounter/mount first; downstream input_dir is mount_name.\n\n"
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
    # Same triple chain, phrasing close to real user prompts ("search text for …")
    ex_e2_user = {
        "role": "user",
        "content": "detect age gender of faces and summarize and search text for boy in /evidence/batch2",
    }
    ex_e2_asst = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "function": {
                    "name": "age-gender/predict",
                    "arguments": {"image_directory": "/evidence/batch2"}
                }
            },
            {
                "function": {
                    "name": "image_summary/summarize-images",
                    "arguments": {
                        "input_dir": "/evidence/batch2",
                        "output_dir": "/evidence/batch2/summary",
                        "model": "gemma3:4b",
                    },
                }
            },
            {
                "function": {
                    "name": "text_embeddings/search",
                    "arguments": {"input_dir": "/evidence/batch2/summary", "query": "boy"},
                }
            },
        ],
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

    # Age-gender + CLIP image search (same folder; no summarize required)
    ex_f_user = {"role": "user", "content": "detect age gender in /tmp and image search for a kid"}
    ex_f_asst = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "function": {
                    "name": "age-gender/predict",
                    "arguments": {"image_directory": "/tmp"},
                }
            },
            {
                "function": {
                    "name": "image_embeddings/search_images",
                    "arguments": {"input_dir": "/tmp", "query": "kid"},
                }
            },
        ],
    }

    # UFDR mount + CLIP image search + image summarize (same mounted tree)
    ex_g_user = {
        "role": "user",
        "content": "mount /data/evidence/case.ufdr at /mnt/case1, image search for young kid and summarize the images there",
    }
    ex_g_asst = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "function": {
                    "name": "ufdr_mounter/mount",
                    "arguments": {"ufdr_file": "/data/evidence/case.ufdr", "mount_name": "/mnt/case1"},
                }
            },
            {
                "function": {
                    "name": "image_embeddings/search_images",
                    "arguments": {"input_dir": "/mnt/case1", "query": "young kid"},
                }
            },
            {
                "function": {
                    "name": "image_summary/summarize-images",
                    "arguments": {
                        "input_dir": "/mnt/case1",
                        "output_dir": "/mnt/case1/summary",
                        "model": "gemma3:4b",
                    },
                }
            },
        ],
    }

    # Summarize + TEXT search (not CLIP) — explicit wording
    ex_h_user = {
        "role": "user",
        "content": "summarize images in /evidence/pics and search the text summaries for backpack",
    }
    ex_h_asst = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "function": {
                    "name": "image_summary/summarize-images",
                    "arguments": {
                        "input_dir": "/evidence/pics",
                        "output_dir": "/evidence/pics/summary",
                        "model": "gemma3:4b",
                    },
                }
            },
            {
                "function": {
                    "name": "text_embeddings/search",
                    "arguments": {"input_dir": "/evidence/pics/summary", "query": "backpack"},
                }
            },
        ],
    }

    # Build complete message list
    messages = [
        system_msg,
        ex_a_user, ex_a_asst,  # Teach Pattern A
        ex_b_user, ex_b_asst,  # Teach Pattern B
        ex_c_user, ex_c_asst,  # Teach Pattern C
        ex_e_user, ex_e_asst,  # age-gender + summarize + TEXT search
        ex_e2_user, ex_e2_asst,
        ex_f_user, ex_f_asst,  # age-gender + image_embeddings (CLIP)
        ex_g_user, ex_g_asst,  # UFDR + CLIP + summarize
        ex_h_user, ex_h_asst,  # summarize + text search (disambiguation)
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
