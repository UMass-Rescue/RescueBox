# Style and theme

## Approach

- **Tailwind** utility classes on NiceGUI elements (`.classes('...')`) — layout, spacing, color, typography.
- **Shared chrome:** `frontend/components/shared/navbar.py`, chat under `frontend/components/chat/`.

## Dark mode

- **`RESCUEBOX_DARK_MODE`** → **`APP_DARK_MODE`** in `frontend/config.py`, passed to **`ui.run(dark=...)`** in `frontend/main.py`.
- **Runtime theme helpers:** `frontend/utils/theme.py` (e.g. **`apply_saved_theme`** used on job details page).

## Where to change look

- App bootstrap: `frontend/main.py`.
- Forms: `frontend/components/forms/form_generator.py` and builders under `forms/builders/`, `forms/fields/`.
