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
logger.setLevel(logging.INFO)
# ==========================================
# Tool Schemas (Strict)
# ==========================================
class TextSummarize(BaseModel):
    """
    Summarize text files in a directory. Input is a folder of text files. Output is a folder of summary text files.
    """
    input_dir: str = Field(..., description="Path to input text")
    output_dir: str = Field(..., description="Path to save summary")
    model: Literal["gemma3:1b", "gemma3:4b"] = Field(..., description="The text summarize model version")

class ImageSummarize(BaseModel):
    """
    Write text captions/descriptions for each image.
    This is NOT CLIP image search and NOT semantic search over text.
    """
    input_dir: str = Field(..., description="Folder of images to caption/summarize")
    output_dir: str = Field(..., description="Folder where per-image text summaries are written")
    model: Literal["moondream:latest", "gemma3:4b", "gemma3:27b"] = Field(..., description="The vision model version")

class AudioTranscribe(BaseModel):
    """
    Transcribe audio files to text. Input is a folder of audio files. Output is a string of the transcription per input file
    """
    input_dir: str = Field(..., description="Path to input audio")

class AgeGenderPredict(BaseModel):
    """
    Predict age and gender of faces in an image directory. Input is a folder of images. Output is a string of the age and gender per input file
    """
    image_directory: str = Field(..., description="Path to image directory")

class FaceFindBulk(BaseModel):
    """
    Find faces in the database that was uploaded earlier using FaceBulkUpload. Input is a folder of images. Upload the images to the database first.
    """
    query_directory: str = Field(..., description="Path to query images")
    collection_name: str = Field("default", description="Database collection")
    similarity_threshold: float = Field(0.75, description="Confidence threshold")

class FaceBulkUpload(BaseModel):
    """
    Input is a folder of images. Upload the images to the database first and then use the collection name to find faces in the database using FaceFindBulk.
    """
    directory_path: str = Field(..., description="Path to upload")
    collection_name: str = Field(..., description="Target collection")
    dropdown_collection_name: str = Field(..., description="UI selection")

class DeepfakeDetection(BaseModel):
    """
    Detect deepfakes in an image directory. Input is a folder of images. Output is a file path of the deepfakes found per input file
    """
    input_dir: str = Field(..., description="Input directory of images")
    output_dir: str = Field(..., description="Output directory for reports and crops")
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
        description="Mount directory: must be /tmp/<folder_name> only (e.g. /tmp/case123).",
    )


class TextSearch(BaseModel):
    """
    Semantic search over plain text files only (e.g. .txt summaries from image_summary/summarize-images).
    Use when the user explicitly searches text or written summaries, captions, or .txt description files.
    Do NOT use when the user says "search these images", "search images for …", "search photos for …",
    or "these pictures" as the set to search—those mean CLIP over pixels (image_embeddings/search_images), not text files.
    """
    input_dir: str = Field(..., description="Folder of .txt/text files to search (typically image_summary output_dir)")
    query: str = Field(..., description="Phrase to find in those text files")

class ImageSearch(BaseModel):
    """
    CLIP text-to-image search: ranks images by visual similarity to the query (reads image pixels).
    Use for 'search these images for …', 'search images for a young person', 'find … in photos',
    'image search', and any query where the corpus is a folder of images—not .txt files.
    """
    input_dir: str = Field(..., description="Directory of image files to embed and search within")
    query: str = Field(..., description="What to look for visually (e.g. 'young person', 'red jacket', 'sunset')")

class ImageSimilaritySearch(BaseModel):
    """
    CLIP image-to-image similarity search: finds images visually similar to a given query image.
    Use when the user provides a reference image and wants to find similar-looking images in a folder.
    e.g. 'find images similar to this photo', 'find images that look like this one'.
    """
    input_dir: str = Field(..., description="Directory of image files to search within")
    query_image: str = Field(..., description="Path to the query image to find similar images for")

# Legacy support for backward compatibility
class RescueBoxToolCall(BaseModel):
    name: Literal[
        "audio/transcribe",
        "age-gender/predict",
        "text_summarization/summarize",
        "image_summary/summarize-images",
        "text_embeddings/search",
        "image_embeddings/search_images",
        "image_similarity/search_similar_images",
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
    # List image (CLIP) search before text search so tool JSON order matches typical "search images" intent.
    "image_embeddings/search_images": ImageSearch,
    "image_similarity/search_similar_images": ImageSimilaritySearch,
    "text_embeddings/search": TextSearch,
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
            "   - If the user asks for transcribe AND/OR summarize in the SAME request as \"search text\" or "
            "\"search\", that is a multi-step pipeline—emit ALL steps (see rules 11–12).\n"
            "   - text_embeddings/search = search inside TEXT FILES (.txt), usually caption/summary outputs. "
            "Use only when the user asks to search summaries/captions/written text, or the chain first ran image_summary "
            "and then searches that output folder\n"
            "   - image_embeddings/search_images = CLIP search over IMAGE PIXELS. "
            "Use when the user mentions photos, images, pictures, \"in these photos\", \"find … in images\", or any "
            "visual \"find X\" query over a folder of images—even if they say \"find\" without saying \"CLIP\".\n"
            "   - If the user says \"find … in these photos\" or similar, choose image_embeddings/search_images, "
            "NOT text_embeddings/search, unless they explicitly mean searching text or .txt summary files.\n"
            "   - If the user wants ONLY image/photo search, emit image_embeddings/search_images only.\n"
            "   - If the user wants ONLY text/.txt search, emit text_embeddings/search only.\n"
            "   - If ONE prompt asks for BOTH \"image search\" (or photos/CLIP/visual) AND \"text search\" (or summaries/.txt), "
            "emit TWO tools: image_embeddings/search_images AND text_embeddings/search.\n"
            "7. BOTH summarize AND image-search on the same folder: emit image_summary/summarize-images AND "
            "image_embeddings/search_images with the SAME input_dir (same image folder); order mount first if UFDR applies.\n"
            "8. SUMMARIZE + TEXT SEARCH pipeline: If the user wants summaries AND to search those written descriptions, use "
            "image_summary/summarize-images then text_embeddings/search with input_dir = that output_dir.\n"
            "9. UFDR: If the user mentions mounting UFDR/.ufdr, emit ufdr_mounter/mount first; downstream input_dir is mount_name.\n"
            "10. AUDIO vs TEXT SUMMARIZE: audio/transcribe converts speech in audio files to text. "
            "text_summarization/summarize condenses text/PDF files already on disk. These are different tools.\n"
            "11. TRANSCRIBE + SUMMARIZE: If the user asks to transcribe audio/files and summarize "
            "the text only, emit TWO tools in order: audio/transcribe first, then text_summarization/summarize.\n"
            "12. TRANSCRIBE + SUMMARIZE + SEARCH TEXT (three steps): Phrases like \"transcribe summarize and search text\" "
            "mean THREE tools in order—never answer with only text_embeddings/search. "
            "Emit: audio/transcribe, then text_summarization/summarize, then text_embeddings/search. "
            "Summarize output_dir feeds text_embeddings/search input_dir.\n"
            "13. IMAGE SEARCH + TEXT SEARCH (two search tools): Phrases like \"image search text search\" require BOTH "
            "image_embeddings/search_images and text_embeddings/search.\n\n"
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
                    "arguments": {"input_dir": "/cases/c10", "output_dir": "/cases/c10/summary", "model": "moondream:latest"}
                }
            },
            {
                "function": {
                    "name": "deepfake_detection/predict",
                    "arguments": {"input_dir": "/cases/c10", "output_dir": "/cases/c10", "facecrop": "true"}
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
                    "arguments": {"input_dir": "/evidence/case1", "output_dir": "/evidence/case1/summaries", "model": "moondream:latest"}
                }
            },
            {
                "function": {
                    "name": "deepfake_detection/predict",
                    "arguments": {"input_dir": "/evidence/batch2", "output_dir": "/evidence/batch2", "facecrop": "true"}
                }
            }
        ]
    }

    # 4. Example C: The "Chain of 3" (Crucial Fix)
    ex_c_user = {"role": "user", "content": "detect age/gender in /data/evidence/batch5, then detect fakes, and describe the images"}
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
                    "arguments": {"input_dir": "/data/evidence/batch5", "output_dir": "/data/evidence/batch5", "facecrop": "true"}
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
    ex_e_user = {"role": "user", "content": "detect age and gender of faces in /evidence/case1, summarize, and search for a kid with brown clothes"}
    ex_e_asst = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "function": {
                    "name": "age-gender/predict",
                    "arguments": {"image_directory": "/evidence/case1"}
                }
            },
            {
                "function": {
                    "name": "image_summary/summarize-images",
                    "arguments": {"input_dir": "/evidence/case1", "output_dir": "/evidence/case1/summaries", "model": "gemma3:4b"}
                }
            },
            {
                "function": {
                    "name": "image_embeddings/search_images",
                    "arguments": {"input_dir": "/evidence/case1", "query": "kid with brown clothes"}
                }
            }
        ]
    }
    # Same triple chain, phrasing close to real user prompts ("search text for …")
    ex_e2_user = {
        "role": "user",
        "content": "detect age gender of faces and summarize and search text for a young boy",
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
    ex_d_user = {"role": "user", "content": "Summarize these images"}
    ex_d_asst = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "function": {
                    "name": "image_summary/summarize-images",
                    "arguments": {"input_dir": "/evidence/batch2", "output_dir": "/evidence/batch2/summary", "model": "moondream:latest"}
                }
            },
        ]
    }

    # Age-gender + CLIP image search (same folder; no summarize required)
    ex_f_user = {"role": "user", "content": "detect age gender in these images and search for a kid"}
    ex_f_asst = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "function": {
                    "name": "age-gender/predict",
                    "arguments": {"image_directory": "/evidence/case1"},
                }
            },
            {
                "function": {
                    "name": "image_embeddings/search_images",
                    "arguments": {"input_dir": "/evidence/case1", "query": "kid"},
                }
            },
        ],
    }

    # UFDR mount + CLIP image search + image summarize (same mounted tree)
    ex_g_user = {
        "role": "user",
        "content": "mount /data/evidence/case.ufdr at /tmp/case1, search images for young kid and summarize",
    }
    ex_g_asst = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "function": {
                    "name": "ufdr_mounter/mount",
                    "arguments": {"ufdr_file": "/data/evidence/case.ufdr", "mount_name": "/tmp/case1"},
                }
            },
            {
                "function": {
                    "name": "image_embeddings/search_images",
                    "arguments": {"input_dir": "/evidence/case1", "query": "young kid"},
                }
            },
            {
                "function": {
                    "name": "image_summary/summarize-images",
                    "arguments": {
                        "input_dir": "/evidence/case1",
                        "output_dir": "/evidence/case1/summary",
                        "model": "gemma3:4b",
                    },
                }
            },
        ],
    }

    # Summarize + TEXT search (not CLIP) — explicit wording
    ex_h_user = {
        "role": "user",
        "content": "summarize these images and search the text summaries for backpack",
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

    # Audio transcription + text summarization (distinct from image_summary/summarize-images)
    ex_ts_user = {
        "role": "user",
        "content": "transcribe the audio files and summarize",
    }
    ex_ts_asst = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "function": {
                    "name": "audio/transcribe",
                    "arguments": {"input_dir": "/evidence/case1/audio_in"},
                }
            },
            {
                "function": {
                    "name": "text_summarization/summarize",
                    "arguments": {
                        "input_dir": "/evidence/case1/transcripts",
                        "output_dir": "/evidence/case1/summary",
                        "model": "gemma3:1b",
                    },
                }
            },
        ],
    }

    # Transcribe + summarize + semantic text search (matches "transcribe summarize and search text")
    ex_ts3_user = {
        "role": "user",
        "content": "transcribe summarize and search text",
    }
    ex_ts3_asst = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "function": {
                    "name": "audio/transcribe",
                    "arguments": {"input_dir": "/evidence/meeting/audio_in"},
                }
            },
            {
                "function": {
                    "name": "text_summarization/summarize",
                    "arguments": {
                        "input_dir": "/evidence/meeting/transcripts",
                        "output_dir": "/evidence/meeting/summary_text",
                        "model": "gemma3:1b",
                    },
                }
            },
            {
                "function": {
                    "name": "text_embeddings/search",
                    "arguments": {
                        "input_dir": "/evidence/meeting/summary_text",
                        "query": "main topics",
                    },
                }
            },
        ],
    }

    # Both CLIP image search and semantic text search in one prompt (do not return only text_embeddings/search)
    ex_imgtxt_user = {
        "role": "user",
        "content": "image search text search",
    }
    ex_imgtxt_asst = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "function": {
                    "name": "image_embeddings/search_images",
                    "arguments": {"input_dir": "/evidence/case/photos", "query": "visual match"},
                }
            },
            {
                "function": {
                    "name": "text_embeddings/search",
                    "arguments": {"input_dir": "/evidence/case/text_summaries", "query": "text match"},
                }
            },
        ],
    }

    # Visual "find in photos" — CLIP only (no summarize, no text_embeddings)
    ex_i_user = {
        "role": "user",
        "content": "find a young girl in these photos",
    }
    ex_i_asst = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "function": {
                    "name": "image_embeddings/search_images",
                    "arguments": {"input_dir": "/data/case/inputs", "query": "young girl"},
                }
            },
        ],
    }

    # "Search these images for …" — CLIP (phrase often misparsed as text search)
    ex_j_user = {
        "role": "user",
        "content": "search these images for a young person",
    }
    ex_j_asst = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "function": {
                    "name": "image_embeddings/search_images",
                    "arguments": {"input_dir": "/evidence/album1", "query": "young person"},
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
        ex_ts_user, ex_ts_asst,  # transcribe audio + text_summarization (two tools)
        ex_i_user, ex_i_asst,  # find in photos → image_embeddings only
        ex_j_user, ex_j_asst,  # search these images for → image_embeddings only
        ex_d_user, ex_d_asst,
        # Last: recency — multi-search prompts that models often collapse to one tool.
        ex_ts3_user, ex_ts3_asst,  # transcribe + summarize + text_embeddings/search (three tools)
        ex_imgtxt_user, ex_imgtxt_asst,  # image_embeddings + text_embeddings (two tools)
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
            logger.debug("--- [Task %d] ---", i)
            logger.debug("Function: %s", tool_call.name)
            logger.debug("Arguments: %s", tool_call.arguments)

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
