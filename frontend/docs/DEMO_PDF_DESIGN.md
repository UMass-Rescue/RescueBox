# Demo PDF Design for RescueBox

## Overview

Add a **Demo** entry point so users can view step-by-step PDF guides in the browser and follow them to use RescueBox (Assistant, Models, Jobs, etc.).

---

## 1. Folder Structure

```
frontend/
├── demo/                          # Demo assets (PDFs)
│   ├── RescueBox_Quick_Start.pdf  # Main guide: getting started, first run
│   ├── Assistant_Guide.pdf        # Using the chat assistant (optional)
│   └── Models_and_Jobs.pdf        # Models + Jobs workflow (optional)
```

- **Option A (single PDF):** One `RescueBox_Quick_Start.pdf` covering all main flows.
- **Option B (multiple PDFs):** Several focused guides; user picks from a demo page.

---

## 2. Serving PDFs

NiceGUI can serve static files. Add in `frontend/main.py` (before `ui.run()`):

```python
# Serve demo PDFs at /demo/...
demo_dir = Path(__file__).parent / 'demo'
if demo_dir.exists():
    app.add_static_files(url_path='/demo', local_directory=str(demo_dir))
```

- PDFs become: `http://localhost:8080/demo/RescueBox_Quick_Start.pdf`
- Browser opens them directly (native PDF viewer or download).

---

## 3. Where to Add the Demo Entry Point

### Option 1: Navbar Link (recommended)

Add a **Demo** link next to Model Details, Assistant, Jobs, Logs:

**File:** `frontend/components/shared/navbar.py`

```python
ui.link('Demo', '/demo').classes('text-white hover:underline px-3 py-2 rounded hover:bg-blue-700')
```

- `NAV_LINKS['demo']` = `'/demo'` in `frontend/constants.py`.

### Option 2: Home Page Button

On the index page, add a Demo button:

**File:** `frontend/main.py` (in the `index()` function)

```python
ui.button('Demo', on_click=lambda: ui.navigate.to('/demo')).classes('bg-amber-500 text-white px-6 py-3')
```

### Option 3: Both

- Navbar: always visible, one click to demo.
- Home: extra visibility for first-time users.

---

## 4. Demo Page Design

### Option A: Single PDF (minimal)

- **Route:** `/demo`
- **Behavior:** Redirect or open the main PDF in a new tab.
- **Implementation:** A simple page that does `ui.run_javascript('window.open("/demo/RescueBox_Quick_Start.pdf", "_blank")')` or renders an embedded viewer.

### Option B: Demo Index Page (multiple PDFs)

- **Route:** `/demo`
- **Content:** List of demo guides with short descriptions.
- **Actions:** 
  - "Open in new tab" (or "View PDF") → `window.open(url, '_blank')`
  - Optional: embedded viewer with `<iframe>` or `<embed>`

**File:** `frontend/pages/demo.py` (new)

```python
@ui.page('/demo')
async def demo_page():
    apply_saved_theme()
    create_navbar()
    with ui.column().classes('container mx-auto p-8'):
        ui.label('RescueBox Demo Guides').classes('text-3xl font-bold mb-6')
        ui.label('Follow these step-by-step guides to learn RescueBox.').classes('text-gray-600 mb-6')
        with ui.row().classes('gap-4'):
            ui.button('Quick Start', on_click=lambda: ui.run_javascript(
                'window.open("/demo/RescueBox_Quick_Start.pdf", "_blank")'
            )).classes('bg-blue-600 text-white')
            # Add more buttons for other PDFs if using Option B
```

---

## 5. PDF Content Recommendations

### RescueBox_Quick_Start.pdf (example outline)

1. **Welcome** – What RescueBox does.
2. **Assistant Mode**
   - Type a prompt (e.g., "Transcribe audio in /path/to/folder").
   - Choose tool from the menu.
   - Fill the form and submit.
3. **Models Mode**
   - Click Models, pick a tool, fill form, submit.
4. **Jobs**
   - Open Jobs to see status, view results, re-run.
5. **Re-run**
   - Load a past conversation and use Re-run for a tool.
6. **Tips** – Shortcuts, folder paths, common errors.

---

## 6. Implementation Checklist

| Step | Action |
|------|--------|
| 1 | Create `frontend/demo/` and add placeholder or real PDF(s). |
| 2 | In `frontend/main.py`, call `app.add_static_files(...)` for `/demo`. |
| 3 | Add `NAV_LINKS['demo']` and `UI_TITLES['demo']` in `frontend/constants.py`. |
| 4 | Add Demo link in `frontend/components/shared/navbar.py`. |
| 5 | Create `frontend/pages/demo.py` with `/demo` route and "View PDF" buttons. |
| 6 | Register demo page in `frontend/main.py`: `import frontend.pages.demo`. |
| 7 | (Optional) Add Demo button on home page in `frontend/main.py`. |

---

## 7. Embedded PDF Viewer (optional)

To show the PDF inside the app instead of a new tab:

```python
# In demo_page:
pdf_url = '/demo/RescueBox_Quick_Start.pdf'
ui.html(f'''
    <iframe src="{pdf_url}" width="100%" height="800px" style="border: none;"></iframe>
''')
```

- Pros: User stays in the app, can read and use RescueBox in another tab.
- Cons: Less space, no browser-native PDF controls; depends on iframe support.

---

## 8. Summary

- **Entry:** Navbar "Demo" (and optionally a home-page button).
- **Storage:** `frontend/demo/*.pdf`.
- **Serving:** `app.add_static_files('/demo', demo_dir)`.
- **Page:** `/demo` with links that open PDFs in a new tab.
- **Content:** One or more PDFs (e.g. `RescueBox_Quick_Start.pdf`) with step-by-step instructions.
