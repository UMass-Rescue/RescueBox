# Style and theme (RescueBox frontend)

This document describes the **strict indigo + zinc** look used across NiceGUI screens. The machine-readable contract is **`frontend/design.json`** (currently **v2.2.0**); the Python source of truth for shared class strings is **`frontend/design_tokens.py`** (`Design`).

---

## Approach

- **Tailwind** utility classes on NiceGUI elements (`.classes('...')`) — layout, spacing, color, typography.
- **Prefer** importing **`Design`** from `frontend.design_tokens` for nav, primary buttons, chat bubbles, inputs, and tool cards so chrome stays consistent.
- **Neutrals:** use the **zinc** scale for text, borders, and surfaces in Python UI (`text-zinc-*`, `bg-zinc-*`, `border-zinc-*`, `ring-zinc-*`). Do **not** introduce new **`gray-*`** utilities in frontend Python — they were migrated to zinc for a single neutral family.
- **Brand / primary actions:** **indigo-600** with **indigo-700** on hover (`Design.BTN_PRIMARY`, `BTN_PRIMARY_TIGHT`, etc.).
- **Elevated surfaces:** **indigo-50** with **indigo-100** / **indigo-200** borders where appropriate (navbar-adjacent panels, tool-call cards, jobs table header, plugin/analysis pickers, “job running” chips).
- **Panel headers (gradients):** **indigo-500 → indigo-700** (or **600 → 800**) for file browser, text search, help, markdown cards — see `design.json` → `gradients.panel_headers`.
- **Markdown in-app:** Tailwind **`prose-zinc`** for guides and chat-adjacent markdown.

### Semantic colors (keep)

These are **not** replaced by indigo; they carry meaning:

| Role | Typical classes | Where |
|------|-----------------|--------|
| Success / completed | `green-*` | `Design.CARD_TOOL_RESULT`, stepper completed steps, positive notifications, optional success cards |
| Error | `red-*` | Errors, destructive emphasis |
| Warning | `yellow-*` / Quasar | Warnings |
| Info | Quasar `type='info'` | Toasts |

---

## Dark mode

- **`RESCUEBOX_DARK_MODE`** → **`APP_DARK_MODE`** in `frontend/config.py`, passed to **`ui.run(dark=...)`** in `frontend/main.py`.
- **Runtime theme helpers:** `frontend/utils/theme.py` (e.g. **`apply_saved_theme`** on some pages).

---

## Where to change look

- **Tokens & contract:** `frontend/design.json`, `frontend/design_tokens.py`.
- **Global readability / notification sizing:** `frontend/utils/ui_readability_css.py`.
- **App bootstrap / root styling hooks:** `frontend/main.py`.
- **Shared chrome:** `frontend/components/shared/navbar.py`, chat under `frontend/components/chat/`.
- **Forms:** `frontend/components/forms/form_generator.py` and builders under `forms/builders/`, `forms/fields/`.

---

## `Design` class (canonical imports)

Files that **import `Design` from `frontend.design_tokens`** (use these as examples when adding new UI):

| File | Typical use |
|------|-------------|
| `frontend/main.py` | Root / global button or layout classes |
| `frontend/components/shared/navbar.py` | `NAV_HEADER`, `NAV_LINK`, `NAV_VERSION_MUTED` |
| `frontend/components/chat/chat_header.py` | Chat header styling |
| `frontend/components/chat/input_area.py` | `INPUT_MODERN` |
| `frontend/components/chat/message_card.py` | `CHAT_*_BUBBLE`, tool styling |
| `frontend/pages/chatbot/utils/ui_styling.py` | Tool call/result cards, form field classes |
| `frontend/pages/chatbot/chatbot_message.py` | Message-level `Design` usage |
| `frontend/components/jobs/job_row.py` | `BTN_PRIMARY_TIGHT` for row actions |

Elsewhere, many components use **inline Tailwind** strings that **mirror** `Design` (indigo + zinc). When touching a file, consider switching repeated patterns to `Design.*`.

---

## Do / don’t

| Do | Don’t |
|----|--------|
| Use **zinc** for neutrals | Introduce **`gray-*`** in new Python UI code |
| Use **indigo** for primary buttons, links, picker chrome, result **summary** cards | Use **violet / purple / slate** for app chrome (legacy passes removed these) |
| Use **`Design`** for nav, chat, and repeated buttons | Duplicate long indigo button strings in many files without consolidating |
| Keep **green** for tool **result** panels and true success semantics | Use **green-600** as a generic “primary” button (use indigo) |

---

## TODO: migrate inline Tailwind to `Design`

Most UI still passes **long Tailwind strings** to `.classes('...')` instead of **`Design`** from `frontend/design_tokens.py`. Visually the app follows indigo + zinc; the gap is **duplication** and **harder global refactors** until more code uses tokens.

**Current state:** only these files import `Design` (everything else with `.classes(` is inline unless it only consumes helpers from `ui_styling.py`):

- `frontend/main.py`
- `frontend/components/shared/navbar.py`
- `frontend/components/chat/chat_header.py`
- `frontend/components/chat/input_area.py`
- `frontend/components/chat/message_card.py`
- `frontend/components/jobs/job_row.py`
- `frontend/pages/chatbot/utils/ui_styling.py`
- `frontend/pages/chatbot/chatbot_message.py` (import inside a code path)

**TODO (incremental):**

- [ ] When editing a module, replace repeated primary buttons / inputs / cards with `Design.BTN_*`, `Design.INPUT_*`, `Design.CARD_*`, etc., instead of copying new indigo/zinc strings.
- [ ] **High-churn / large files** good candidates: `frontend/utils/file_browser.py`, jobs pages under `frontend/pages/jobs/`, results under `frontend/components/results/`, `frontend/components/forms/form_generator.py`, demo pages under `frontend/pages/demo*.py`.
- [ ] Add or extend thin wrappers in `ui_styling.py` (or small module-level constants next to `Design`) where chat-adjacent patterns repeat but should not live in `design_tokens.py` itself.
- [ ] After meaningful migration, re-run the **`zinc-`** file list in the appendix and update counts if needed.

---

## Files inventory (styling adoption)

The indigo/zinc alignment touched modules that set Tailwind classes (bulk **gray → zinc**, then **slate → zinc**, **violet/purple → indigo**, primary **greens → indigo** where the control was a brand action). **Every path** under `frontend/` that currently contains the substring **`zinc-`** is listed exhaustively below (**78** Python files as of the last doc update). Regenerate with:

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
                        paths.append(p)
            except OSError:
                pass
for p in sorted(paths):
    print(p.replace(os.sep,'/'))
"
```

### Appendix: exhaustive list — `frontend/**/*.py` containing `zinc-` (78 files)

- `frontend/components/about/license_documents.py`
- `frontend/components/base_component.py`
- `frontend/components/chat/chat_header.py`
- `frontend/components/chat/chat_window.py`
- `frontend/components/chat/conversation_card.py`
- `frontend/components/chat/conversation_view_dialog.py`
- `frontend/components/chat/help_dialog.py`
- `frontend/components/chat/input_area.py`
- `frontend/components/chat/message_card.py`
- `frontend/components/chat/panels/conversation_actions.py`
- `frontend/components/chat/panels/conversation_renderer.py`
- `frontend/components/chat/panels/history_panel.py`
- `frontend/components/chat/tool_call_card.py`
- `frontend/components/component_utils.py`
- `frontend/components/demo/demo_files_explorer.py`
- `frontend/components/demo/guided_markdown.py`
- `frontend/components/errors/error_boundary.py`
- `frontend/components/errors/error_display.py`
- `frontend/components/forms/builders/input_field_builder.py`
- `frontend/components/forms/builders/parameter_field_builder.py`
- `frontend/components/forms/case_notes_dialog.py`
- `frontend/components/forms/fields/input_widgets.py`
- `frontend/components/forms/form_actions.py`
- `frontend/components/forms/form_generator.py`
- `frontend/components/jobs/compact_inputs_summary.py`
- `frontend/components/jobs/job_details_panel.py`
- `frontend/components/jobs/job_outputs_card.py`
- `frontend/components/jobs/job_row.py`
- `frontend/components/jobs/readonly_form.py`
- `frontend/components/logs/log_viewer.py`
- `frontend/components/models/model_card.py`
- `frontend/components/pickers/analysis_picker_dialog.py`
- `frontend/components/pickers/tool_picker_dialog.py`
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
- `frontend/pages/base_page.py`
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
- `frontend/pages/jobs/jobs.py`
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
```

---

## Related docs

- `frontend/docs/README.md` — doc index
- `frontend/database/README.md` — data layer (not visual theme)
