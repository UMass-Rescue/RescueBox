# Forms & Utilities Architecture (Modular Refactor 2026)

This document describes the modular architecture of the form components and utility package, which were decomposed from monolithic files to improve maintainability.

## Form Components (`frontend/components/forms/`)

The forms package orchestrates the dynamic generation of UI controls from `TaskSchema` definitions.

| Module | Description |
| :--- | :--- |
| `form_generator.py` | The main `FormGenerator` class. Handles form state, generation orchestration, and submission actions. |
| `field_builders.py` | Dedicated logic for building individual input fields (Directory, File, Text) and parameter widgets (Sliders, Selects, Numbers). |
| `dialogs.py` | Specialized UI modals related to forms, such as the Case Notes dialog. |

### Key Patterns
- **Dynamic Generation:** Forms are built on-the-fly based on plugin schemas.
- **Autofill Logic:** Intelligent path suggestions (e.g., pre-filling `output_dir` based on `input_dir`) are handled during field construction.

---

## Utility Package (`frontend/utils/`)

The `utils` package provides centralized cross-cutting concerns for the frontend.

| Module | Description |
| :--- | :--- |
| `logging.py` | Contextual logging (Session/Job/Model IDs) and audit trail generation for compliance and debugging. |
| `paths.py` | Cross-platform path resolution, Windows drive support, and backend `sys.path` integration. |
| `browser.py` | Interactive file and directory browsers using NiceGUI components. |
| `validators.py` | Pydantic-powered validation for form inputs and API response bodies. |
| `storage.py` | Wrappers for NiceGUI `app.storage` handling user preferences, session state, and conversation drafts. |
| `ui.py` | Standardized notification patterns and global CSS injection for readability. |

### Public API
The `frontend/utils/__init__.py` file re-exports all commonly used functions, maintaining a flat import structure for the rest of the application while keeping the implementation modular.
