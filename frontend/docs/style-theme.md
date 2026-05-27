# Style and theme (RescueBox frontend)

This document describes how **color, typography, and surfaces** are applied across NiceGUI screens **as implemented today**. The machine-readable contract is **`frontend/design.json`** (currently **v3.0**); the Python source of truth for shared class strings is **`frontend/design_tokens.py`** (`Design`).

The UI uses a **UMass brand-aligned** theme: it combines **UMass Maroon (#881c1c)** for primary actions and links, **UMass Medium Gray (#505759)** for key chrome (navbar, borders, and plugin rows), and **zinc** for neutral surfaces. This consistency matches `design.json` and `design_tokens.py`.

---

## Approach

- **Tailwind** utility classes on NiceGUI elements (`.classes('...')`) — layout, spacing, color, typography.
- **Prefer** importing **`Design`** from `frontend.design_tokens` for nav, primary buttons, chat bubbles, inputs, tool cards, and dialogs where tokens already exist.
- **Neutrals:** use the **zinc** scale for text, borders, and surfaces in Python UI (`text-zinc-*`, `bg-zinc-*`, `border-zinc-*`, `ring-zinc-*`). Do **not** introduce new **`gray-*`** utilities in frontend Python — use zinc for a single neutral family (`design.json` → `brand.neutrals`).
- **Brand / primary actions (buttons & links):** **UMass Maroon** `#881c1c` with darker hover `#6a1616` via **`Design.BTN_PRIMARY`**, **`BTN_PRIMARY_COMPACT`**, **`BTN_PRIMARY_TIGHT`**, and **`Design.LINK`**. (Quasar `--q-primary` at `:root` is aligned in **`frontend/utils/ui_readability_css.py`**). **Indigo is officially deprecated** for primary actions.
- **Navigation bar:** **Medium Gray #505759** background on **`.q-header.rb-brand-nav`** (`Design.NAV_HEADER`); white nav links (`Design.NAV_LINK`). Header scope sets **`--q-primary`** to `#505759` so Quasar controls in the bar match the bar (see `ui_readability_css.py`).
- **Secondary solid actions (Browse, Cancel, etc.):** **`Design.BTN_MEDIUM_GRAY`** → **`.rb-btn-medium-gray`** (`#505759` fill, documented in `ui_readability_css.py`).
- **Status & Processing:** Maroon is used for status text and spinners via **`Design.STATUS_PROCESSING`** and **`SPINNER_PROCESSING`**. **`Design.CHAT_SYSTEM_TOOL`** uses a **left border Medium Gray (#505759)** strip.
- **Brand-aligned borders without indigo:** many surfaces use **`border-[#505759]`** (e.g. plugin menu rows `CHATBOT_PLUGIN_MENU_ROW`, image-summary style shells). That is intentional **Medium Gray** chrome, not a mistake vs zinc borders elsewhere.
- **Elevated surfaces:** Surfaces like job table headers and tool-call cards use **zinc-50** and **zinc-200** borders via **`Design.CARD_TOOL_CALL`** / **`CARD_TOOL_RESULT`**.
- **Panel headers (gradients):** **`design.json` → `gradients.panel_headers`** — **zinc-50 → zinc-100** (subtle contrast) for file browser / text search style headers; Help-style flows use **zinc** panel shell + **`prose-zinc`**.
- **Markdown in-app:** Tailwind **`prose-zinc`** for guides and chat-adjacent markdown where applied.

### Semantic colors (keep)

These carry meaning and are **not** replaced by brand maroon or #505759:

| Role | Typical classes | Where |
|------|-----------------|--------|
| Success / completed | `green-*` | `Design.CARD_TOOL_RESULT`, stepper completed steps, positive notifications, optional success cards |
| Error | `red-*` | Errors, destructive emphasis |
| Warning | `yellow-*` / Quasar | Warnings |
| Info | Quasar `type='info'` | Toasts |

### Quasar + global CSS (must read with tokens)

**`frontend/utils/ui_readability_css.py`** injects global rules: e.g. **`:root`** `--q-primary` for **maroon**, **`.q-header.rb-brand-nav`** for navbar **#505759**, **`.rb-brand-primary`** and **`.rb-btn-medium-gray`** for button chrome, notification overrides, and other app-wide fixes. **Default `ui.button` / Quasar `color='primary'`** are affected by these layers — when debugging colors, inspect **CSS + Tailwind + `Design`**, not Tailwind alone.

---

---

## Where to change look

- **Tokens & contract:** `frontend/design.json`, `frontend/design_tokens.py`.
- **Global readability / Quasar overrides / notification sizing:** `frontend/utils/ui_readability_css.py`.
- **App bootstrap / root styling hooks:** `frontend/main.py`.
- **Shared chrome:** `frontend/components/shared/navbar.py`, chat under `frontend/components/chat/`.
- **Forms:** `frontend/components/forms/form_generator.py` and builders under `forms/builders/`, `forms/fields/`.

---

## `Design` class (canonical imports)

Files that **import `Design` from `frontend.design_tokens`** (use as examples; list may grow — verify with repo search):

| File | Typical use |
|------|-------------|
| `frontend/main.py` | Root / global layout / `Design` usage |
| `frontend/components/shared/navbar.py` | `NAV_HEADER`, `NAV_LINK`, `NAV_VERSION_MUTED` |
| `frontend/components/chat/chat_header.py` | Chat header (may use local classes; check file) |
| `frontend/components/chat/input_area.py` | `INPUT_MODERN` |
| `frontend/components/chat/message_card.py` | `CHAT_*_BUBBLE`, tool styling |
| `frontend/components/chat/help_dialog.py`, `history_dialog.py`, `conversation_view_dialog.py` | Dialog chrome |
| `frontend/pages/chatbot/utils/ui_styling.py` | Tool call/result cards, form field classes |
| `frontend/pages/chatbot/utils/chat_ui_builder.py` | Chat layout / `Design` |
| `frontend/pages/chatbot/chatbot_message.py` | Message-level `Design` (import on code path) |
| `frontend/components/jobs/job_row.py` | `BTN_PRIMARY_TIGHT` for row actions |
| `frontend/components/forms/*`, `frontend/components/errors/validation_dialog.py` | Forms, validation UI |
| `frontend/components/logs/log_viewer.py`, `frontend/pages/logs/logs.py` | Logs UI |
| `frontend/utils/file_browser.py`, `frontend/utils/error_handling.py` | File browser, errors |
| `frontend/components/results/results_utils.py`, `image_bbox_preview.py`, `image_summary_results_view.py`, `text_search_results_view.py` | Results / previews |
| `frontend/components/pickers/*`, `frontend/pages/chatbot/pickers.py` | Pickers |
| `frontend/components/jobs/case_export_button.py` | Case export |

Elsewhere, many components use **inline Tailwind** strings that **mirror** parts of `Design` or add **indigo / #505759 / zinc** combinations. When touching a file, consider switching repeated patterns to **`Design.*`** for easier refactors.

---

## Do / don’t

| Do | Don’t |
|----|--------|
| Use **zinc** for neutrals | Introduce **`gray-*`** in new Python UI code |
| Use **`Design.BTN_PRIMARY`** (maroon / `rb-brand-primary`) for **primary** actions | Use **indigo** for primary CTA buttons (outdated; maroon is the brand primary) |
| Use **`Design.BTN_MEDIUM_GRAY`** for Browse / Cancel-style **secondary solid** actions | Confuse **#505759** chrome with maroon primary — different roles |
| Use **`Design.NAV_*`** for navbar | Assume **`color=None`** on `ui.button` inherits nav colors without checking Quasar + `ui_readability_css.py` |
| Keep **indigo** where tokens/docs still specify it (links, some focus rings, some panels) **or** migrate deliberately | Introduce **violet / purple / slate** for new app chrome |
| Keep **green** for tool **result** semantics and completed steps | Use **green** as a generic substitute for **maroon** primary buttons |
| Read **`design.json` + `ui_readability_css.py`** when changing “brand” colors | Update only `design_tokens.py` and assume Quasar picks it up everywhere |

---

## TODO: migrate inline Tailwind to `Design` (and optional accent unification)

Most UI still passes **long Tailwind strings** to `.classes('...')` instead of **`Design`**. The gap is **duplication** and **harder refactors**. A systematic migration has eliminated hardcoded **indigo** in favor of brand-aligned maroon, #505759, and zinc variants across the entire frontend.

**TODO (incremental):**

- [ ] When editing a module, replace repeated primary buttons / inputs / cards with `Design.BTN_*`, `Design.INPUT_*`, `Design.CARD_*`, etc.
- [ ] **High-churn / large files** (good candidates): `frontend/utils/file_browser.py`, jobs under `frontend/pages/jobs/`, results under `frontend/components/results/`, `frontend/components/forms/form_generator.py`, demo pages under `frontend/pages/demo*.py`.
- [ ] After meaningful migration, re-run the **`zinc-`** inventory script below and refresh the appendix counts and list.

---

## Files inventory (styling adoption)

**`zinc-` in Python:** Regenerate the list and count with:

```bash
python3 -c "
import os
root='frontend'
paths=[]
for dirpath,_,files in os.walk(root):
    for f in files:
        if f.endswith('.py'):
            p=os.path.join(dirpath,f)
            try:
                with open(p,'rb') as fh:
                    if b'zinc-' in fh.read():
                        paths.append(p.replace(os.sep,'/'))
            except OSError:
                pass
print(len(paths))
for p in sorted(paths):
    print(p)
"
```

### Appendix: `frontend/**/*.py` containing `zinc-` (**78** files, last regenerated with the script above)

- `frontend/chatbot/forms.py`
- `frontend/components/base_component.py`
- `frontend/components/chat/rendering.py`
- `frontend/components/chat/dialogs.py`
- `frontend/components/component_utils.py`
- `frontend/components/errors/error_boundary.py`
- `frontend/components/errors/error_display.py`
- `frontend/components/file_browser/header.py`
- `frontend/components/forms/builders/input_field_builder.py`
- `frontend/components/forms/builders/parameter_field_builder.py`
- `frontend/components/forms/case_notes_dialog.py`
- `frontend/components/forms/fields/input_widgets.py`
- `frontend/components/forms/form_generator.py`
- `frontend/components/jobs/compact_inputs_summary.py`
- `frontend/components/jobs/job_details_panel.py`
- `frontend/components/jobs/job_outputs_card.py`
- `frontend/components/jobs/job_row.py`
- `frontend/components/jobs/readonly_form.py`
- `frontend/components/logs/log_viewer.py`
- `frontend/components/models/model_card.py`
- `frontend/components/models/model_info_card.py`
- `frontend/components/pickers/analysis_picker_dialog.py`
- `frontend/components/pickers/tool_picker_dialog.py`
- `frontend/components/results/batch_text_item.py`
- `frontend/components/results/directory_card.py`
- `frontend/components/results/directory_renderers.py`
- `frontend/components/results/file_card.py`
- `frontend/components/results/file_renderers.py`
- `frontend/components/results/image_bbox_preview.py`
- `frontend/components/results/image_summary_results_view.py`
- `frontend/components/results/markdown_card.py`
- `frontend/components/results/renderers/batch_text_renderer - Copy.py`
- `frontend/components/results/renderers/batch_text_renderer.py`
- `frontend/components/results/renderers/text_renderer.py`
- `frontend/components/results/result_card.py`
- `frontend/components/results/results_utils.py`
- `frontend/components/results/searchable_file_list.py`
- `frontend/components/results/table_helpers.py`
- `frontend/components/results/text_card.py`
- `frontend/components/results/text_search_results_view.py`
- `frontend/components/results/tool_selection_card.py`
- `frontend/components/shared/breadcrumbs.py`
- `frontend/components/shared/notifications.py`
- `frontend/components/shared/stepper.py`
- `frontend/design_tokens.py`
- `frontend/main.py`
- `frontend/pages/about.py`
- `frontend/pages/chatbot/chatbot_forms.py`
- `frontend/pages/chatbot/chatbot_message.py`
- `frontend/pages/chatbot/constants.py`
- `frontend/pages/chatbot/pickers.py`
- `frontend/pages/chatbot/results.py`
- `frontend/pages/chatbot/utils/chat_ui_builder.py`
- `frontend/pages/chatbot/utils/conversation_loader.py`
- `frontend/pages/chatbot/utils/job_submission_orchestrator.py`
- `frontend/pages/chatbot/utils/ui_styling.py`
- `frontend/pages/demo.py`
- `frontend/pages/jobs/components/job_forms.py`
- `frontend/pages/jobs/components/job_metadata.py`
- `frontend/pages/jobs/job_details.py`
- `frontend/pages/logs/logs.py`
- `frontend/tests/unit/test_file_browser.py`
- `frontend/tests/unit/test_stepper.py`
- `frontend/utils/demo_user_gate.py`
- `frontend/utils/file_browser.py`
- `frontend/utils/nicegui_storage.py`
- `frontend/utils/ui_readability_css.py`

---

## Audit commands

From the repo root:

```bash
# Should be empty for Python UI (no gray utilities)
rg 'gray-[0-9]' frontend --glob '*.py'

# Find straggler slate/violet/purple chrome (should be none in normal paths)
rg 'slate-[0-9]|border-violet|from-violet|purple-[0-9]{3}' frontend --glob '*.py'

# Files that import Design (maintainers: refresh list periodically)
rg 'from frontend\.design_tokens import Design' frontend --glob '*.py'
```

*(If `rg` is not installed, use `grep -R` equivalents.)*

---

## Related docs

- `frontend/docs/README.md` — doc index
- `frontend/database/README.md` — data layer (not visual theme)
