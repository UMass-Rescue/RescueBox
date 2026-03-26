import os
import pytest

# Integration tests require external services (backend API, Ollama, models).
# By default these are skipped in CI/local runs where external services are not running.
# To enable real integration tests, set environment variable RUN_INTEGRATION=1.
if os.getenv("RUN_INTEGRATION", "0") != "1":
    pytest.skip("Skipping integration tests (set RUN_INTEGRATION=1 to enable)", allow_module_level=True)


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
