"""
Exhaustive Granite (Ollama) tool-selection tests.

Each case sends a **short, distinct user prompt** through the same path as production:
``ChatbotCore.call_granite_model_direct`` → advanced Granite prompt → ``/api/chat``.

**Requirements:** Ollama at ``OLLAMA_HOST`` (default http://localhost:11434) and
``GRANITE_MODEL`` (default ibm/granite4.1:3b) pulled locally.

**Run:**
  cd frontend && RUN_INTEGRATION=1 pytest tests/integration/test_granite_tool_prompts.py -v -m ollama

Logs: enable INFO on ``frontend.chatbot.core`` and ``frontend.chatbot.message_handler`` to see
prompt previews and selected tool names (also emitted during tests via caplog if needed).

**Note:** LLM routing can be nondeterministic. If a case fails intermittently, re-run or refine
the prompt; the first returned tool must match ``expected_endpoint``.
"""

from __future__ import annotations

import logging

import pytest

from frontend.chatbot.config import ChatbotConfig

logger = logging.getLogger(__name__)

_integration_cfg = ChatbotConfig()
OLLAMA_HOST = _integration_cfg.OLLAMA_HOST
GRANITE_MODEL = _integration_cfg.GRANITE_MODEL


# (expected_endpoint, short_user_prompt) — one clear forensic-style sentence per tool in SCHEMA_MAP
GRANITE_TOOL_PROMPTS = [
    (
        "audio/transcribe",
        "Transcribe the MP3 recordings in /evidence/wiretaps to text.",
    ),
    (
        "age-gender/predict",
        "Estimate age and gender for each face in /case/photos/batch1.",
    ),
    (
        "text_summarization/summarize",
        "Summarize long text documents under /reports/inbox into short briefs.",
    ),
    (
        "image_summary/summarize-images",
        "Describe every image in /photos/scene for a written overview.",
    ),
    (
        "text_embeddings/search",
        "Semantic search text files for mentions of red vehicle near /data/text_export.",
    ),
    (
        "image_embeddings/search_images",
        "Image search the folder /photos/proofs for a young kid in a red jacket.",
    ),
    (
        "ufdr_mounter/mount",
        "Mount the forensic archive /data/evidence/case.ufdr at /tmp/case1 for browsing.",
    ),
    (
        "face-match/findfacebulk",
        "Find matching identities in the face gallery using probe images from /query/probes.",
    ),
    (
        "face-match/bulkupload",
        "Upload and enroll face crops from /enroll/subjects into the collection.",
    ),
    (
        "deepfake_detection/predict",
        "Detect synthetic or manipulated media in /datasets/clips for authenticity.",
    ),
    (
        "rescuebox/unknown",
        "List file names in /tmp/evidence_folder without running heavy models.",
    ),
]


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.ollama
@pytest.mark.parametrize(
    "expected_endpoint,short_prompt",
    GRANITE_TOOL_PROMPTS,
    ids=[row[0] for row in GRANITE_TOOL_PROMPTS],
)
async def test_granite_selects_expected_tool_first(
    granite_model_tag: str,
    expected_endpoint: str,
    short_prompt: str,
    caplog,
):
    """First tool call from Granite must match ``expected_endpoint`` for the given prompt."""
    from frontend.chatbot.core import ChatbotCore
    from frontend.chatbot.config import ChatbotConfig

    config = ChatbotConfig(OLLAMA_HOST=OLLAMA_HOST, GRANITE_MODEL=granite_model_tag)
    core = ChatbotCore(config)
    try:
        caplog.set_level(logging.INFO, "frontend.chatbot.core")
        with caplog.at_level(logging.INFO):
            tool_calls = await core.call_granite_model_direct(
                short_prompt, use_advanced=True
            )

        assert (
            tool_calls is not None and len(tool_calls) > 0
        ), f"No tool calls for prompt={short_prompt!r} — check Ollama logs and Granite output."
        first = tool_calls[0]
        got = first.get("name", "")
        logger.info(
            "Granite tool selection test: expected=%s got=%s prompt=%r",
            expected_endpoint,
            got,
            short_prompt,
        )
        assert got == expected_endpoint, (
            f"Expected first tool {expected_endpoint!r}, got {got!r}. "
            f"Full tool_calls={tool_calls!r}. Prompt={short_prompt!r}"
        )
    finally:
        await core.close()
