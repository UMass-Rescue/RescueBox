import logging
import os

import httpx
import pytest
import pytest_asyncio

from frontend.chatbot.config import (
    ChatbotConfig,
    collect_ollama_model_names,
    resolve_ollama_model_tag,
)

logger = logging.getLogger(__name__)

# Integration tests require external services (backend API, Ollama, models).
# By default these are skipped in CI/local runs where external services are not running.
# To enable real integration tests, set environment variable RUN_INTEGRATION=1.
if os.getenv("RUN_INTEGRATION", "0") != "1":
    pytest.skip(
        "Skipping integration tests (set RUN_INTEGRATION=1 to enable)",
        allow_module_level=True,
    )


def pytest_collection_modifyitems(config, items):
    """Run NiceGUI User page tests before heavy API/Ollama modules.

    Long-running integration tests can leave the ASGI test client in a state where
    /chatbot renders an empty shell; mock page tests are ordered first.
    """

    def priority(item):
        path = str(item.fspath)
        if path.endswith("test_pages.py"):
            return (0, item.nodeid)
        if path.endswith("test_pages_integration.py"):
            return (1, item.nodeid)
        return (2, item.nodeid)

    items[:] = sorted(items, key=priority)


@pytest.fixture(scope="session")
def integration_chatbot_config() -> ChatbotConfig:
    return ChatbotConfig()


@pytest_asyncio.fixture
async def ollama_client(integration_chatbot_config: ChatbotConfig):
    async with httpx.AsyncClient(
        base_url=integration_chatbot_config.OLLAMA_HOST, timeout=60.0
    ) as client:
        yield client


@pytest_asyncio.fixture
async def ollama_available(ollama_client: httpx.AsyncClient) -> bool:
    try:
        response = await ollama_client.get("/api/tags", timeout=10.0)
        return response.status_code == 200
    except Exception:
        return False


@pytest_asyncio.fixture
async def granite_model_tag(
    ollama_client: httpx.AsyncClient,
    ollama_available: bool,
    integration_chatbot_config: ChatbotConfig,
) -> str:
    """Resolved Ollama model tag for ``GRANITE_MODEL``; skips if missing."""
    if not ollama_available:
        pytest.skip("Ollama server not running")
    response = await ollama_client.get("/api/tags", timeout=10.0)
    if response.status_code != 200:
        pytest.skip(f"Ollama /api/tags failed: HTTP {response.status_code}")
    names = collect_ollama_model_names(response.json())
    requested = integration_chatbot_config.GRANITE_MODEL
    resolved = resolve_ollama_model_tag(requested, names)
    if not resolved:
        logger.warning(
            "Granite model %r not matched in Ollama tags: %s", requested, names
        )
        pytest.skip(
            f"Granite model {requested!r} not found in Ollama. " f"Available: {names!r}"
        )
    logger.info("Using Ollama Granite tag %r (requested %r)", resolved, requested)
    return resolved
