# Integration tests (`frontend/tests/integration`)

These tests call real services unless mocked. The package is **skipped by default**.

## Enable

Set **`RUN_INTEGRATION=1`** (see **`conftest.py`** in this directory).

```bash
cd /path/to/RescueBox
set RUN_INTEGRATION=1
poetry run pytest frontend/tests/integration/ -c frontend/tests/pytest.ini -m ""
```

`frontend/tests/pytest.ini` defaults to `-m "not integration"`. Use **`-m ""`** to run the whole integration folder, or **`-m integration`** for tests explicitly marked `@pytest.mark.integration` only.

You may need a running RescueBox API, Ollama with **`GRANITE_MODEL`**, etc. Read each file’s docstring and markers (`api`, `ollama`, …).

| File | Focus |
|------|--------|
| `test_pages.py` | NiceGUI pages with mocked HTTP (run first) |
| `test_pages_integration.py` | Same UI checks against live API when available |
| `test_chatbot_refactor_integration.py` | Pipeline planner/context + handler split (no API) |
| `test_rerun_and_pipeline_context_integration.py` | Re-run route + job DB pipeline paths |
| `test_chatbot_storage_integration.py` | Conversation id in NiceGUI storage |

## Full testing guide

See **`frontend/docs/README.md`** and **`frontend/docs/ui-flow.md`** for current frontend behavior/context.
