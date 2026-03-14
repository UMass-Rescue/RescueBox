import os
import pytest

# Integration tests require external services (backend API, Ollama, models).
# By default these are skipped in CI/local runs where external services are not running.
# To enable real integration tests, set environment variable RUN_INTEGRATION=1.
if os.getenv("RUN_INTEGRATION", "0") != "1":
    pytest.skip("Skipping integration tests (set RUN_INTEGRATION=1 to enable)", allow_module_level=True)

