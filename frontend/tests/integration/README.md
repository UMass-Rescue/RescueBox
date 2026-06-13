# Integration tests (`frontend/tests/integration`)

These tests call real services unless mocked. The package is **skipped by default**.

## Enable

Set **`RUN_INTEGRATION=1`** (see **`conftest.py`** in this directory).

```bash
cd /path/to/RescueBox
RUN_INTEGRATION=1 poetry run pytest frontend/tests/integration/ -c frontend/tests/pytest.ini
```

You may need a running RescueBox API, Ollama with **`GRANITE_MODEL`**, etc. Read each file’s docstring and markers (`api`, `ollama`, …).

## Full testing guide

See **`frontend/docs/README.md`** and **`frontend/docs/ui-flow.md`** for current frontend behavior/context.
