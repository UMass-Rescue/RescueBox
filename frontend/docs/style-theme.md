# Style and theme (frontend)

Current source of truth for reusable style tokens is `frontend/design_tokens.py` (`Design`).
Global CSS/Quasar overrides are in `frontend/utils/ui_readability_css.py`.

## Core theme rules

- Primary brand actions: UMass maroon `#881c1c` (`Design.BTN_PRIMARY*`, `Design.LINK`).
- Secondary solid buttons: medium gray `#505759` (`Design.BTN_MEDIUM_GRAY`).
- Neutral surfaces/text/borders: zinc/slate classes used consistently across pages.
- Semantic status colors remain semantic:
  - success (`green-*`)
  - warning (`yellow-*`)
  - error (`red-*`)

## Where to update styling

- Tokens: `frontend/design_tokens.py`
- Global CSS + Quasar vars: `frontend/utils/ui_readability_css.py`
- Shared navbar/shell: `frontend/components/shared/`
- Chat UI styling: `frontend/components/chat/` and `frontend/pages/chatbot/`
- Forms: `frontend/components/forms/`
- Jobs and results cards: `frontend/components/jobs/`, `frontend/components/results/`

## Practical guidance

- Prefer `Design.*` tokens over repeating long inline class strings.
- Keep new neutral styles on zinc/slate family.
- Avoid introducing legacy/deprecated indigo primary CTA patterns.

## Audit helpers

From repo root:

```bash
# New gray utility usage (should be reviewed)
rg 'gray-[0-9]' frontend --glob '*.py'

# Files importing Design
rg 'from frontend\.design_tokens import Design' frontend --glob '*.py'
```

## Historical note

The previous style doc included a large generated file inventory that drifted from current module paths. That inventory has been removed; regenerate via commands above when needed.

## Related

- `frontend/docs/ui-flow.md`
- `frontend/docs/README.md`
