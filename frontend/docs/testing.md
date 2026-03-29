# Frontend tests

## Run (Poetry)

From **repository root**:

```bash
poetry run pytest frontend/tests/ -c frontend/tests/pytest.ini
```

Or from **`frontend/`** (uses `frontend/tests/pytest.ini` via `-c` or run with `testpaths = tests`):

```bash
cd frontend && poetry run pytest tests/ -c tests/pytest.ini
```

Config: **`frontend/tests/pytest.ini`** — markers: `unit`, `integration`, `api`, `ollama`, `slow`, `asyncio`.

## Integration gate

**`frontend/tests/integration/conftest.py`** skips the whole integration package unless **`RUN_INTEGRATION=1`**.

```bash
RUN_INTEGRATION=1 poetry run pytest frontend/tests/integration/ -c frontend/tests/pytest.ini
```

Some tests need Ollama, Granite model, or a live API — see per-file docstrings and **`@pytest.mark`**.

## Layout

| Path | Role |
|------|------|
| `frontend/tests/conftest.py` | Shared fixtures |
| `frontend/tests/unit/` | Unit tests |
| `frontend/tests/integration/` | Integration (gated) |

## Backend / plugin tests

Not under `frontend/tests/` — see `src/**/tests/` and root **`pytest.ini`**.
