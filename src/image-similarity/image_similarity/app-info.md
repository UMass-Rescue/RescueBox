# Image Similarity Search

Finds images from the **same series** as a query image.

**Series:** Images related **temporally** and by **subject matter** (e.g. one birthday party). Photos of the same person at different times and places are **not** one series.

Embeddings are stored in the database. Images processed in a prior run are **reused** — no double computation.

## Chatbot plugin menu

In the **Assistant**, the tool picker lists **three separate plugin options** (not one plugin with sub-tasks). Pick the option you need:

| # | Chatbot menu option | Form / task | When to use |
|---|---------------------|-------------|-------------|
| **1** | **Image Series Similarity** | Find series matches | Search a local folder for images similar to a query photo |
| **2** | **Image Series Similarity - Export Embeddings** | Export embeddings | Download a `.json` to share with another organization or user |
| **3** | **Image Series Similarity - Import Embeddings** | Import embeddings | Load a `.json` from another organization or user |

Slash shortcuts: `/search-series`, `/export-private-embeddings`, `/import-private-embeddings`.

## Workflows

### Local search only (option 1)

1. **Assistant** → plugin menu → **Image Series Similarity**
2. **Input directory** — folder of images to search
3. **Query image** — reference photo from that case
4. **Submit** → local matches in the results table (Path shows filename; click to preview)

### Share embeddings (option 1, then option 2)

1. **Image Series Similarity** on your case folder (indexes plain and private embeddings)
2. **Assistant** → plugin menu → **Image Series Similarity - Export Embeddings** → **Organization** and **Contact email** → **Submit** → download `.json`
3. Send the `.json` to another organization or user

### Import and search (option 3, then option 1)

1. **Assistant** → plugin menu → **Image Series Similarity - Import Embeddings** → select `.json` from another organization or user → **Submit**
2. **Image Series Similarity** on your own case folder:
   - **Input directory** — your local images (required)
   - **Query image** — local reference photo
3. **Submit** → **Local** rows (filename, preview) and **Imported** rows (Owner, Organization, Content ID)

Use **Owner** and **Organization** to contact whoever exported the embedding. **Content ID** is a truncated SHA-256 hash for referring to the same image in email — not a contact address.

### Resolve Content ID (after follow-up from another user)

The importing user cannot resolve a Content ID to a filepath. When they email you the Content ID from an imported match, look up the local path in the RescueBox database (see README for the `docker exec … psql` command).

## When to use this plugin

| I have... | I want... | Use |
|---|---|---|
| A **birthday party image** | Other images from the **same birthday party** | **Image Similarity** (this plugin) |
| A **text description** | Photos that **match the description** | Image Search |
| A **photo** | A **text description** of what's in it | Image Summary |
| A **photo** with people | **Age and gender** of each person | Age-Gender Classifier |

**Use case — same series:** Use a full uncropped query photo. The model embeds the whole scene (people, background, lighting).

**Use case — specific subject:** Crop the query so one subject fills the frame.

**Use case — shared embeddings:** Import from another organization or user (option 3), then search your folder (option 1).

If you want a concept like "people eating" rather than a specific scene, use **Image Search** with a text query instead.

## Option 1: Image Series Similarity

Chatbot menu: **Image Series Similarity**. Form title: **Find series matches**.

### Inputs

- **Input directory** — folder containing image files to search
- **Query image** — reference image; results exclude the query itself

### Parameters

- **CLIP model:** `google/siglip2-so400m-patch14-384` (SigLIP2-SO400M, 1152-dim)
- **Top K:** 1–20 results (default 5)
- **Match threshold:** 0–1; metadata marks results at or above this as a match
- **Scoring mode:** Combined (60% CLIP + 40% PDQ, default), Semantic only (CLIP), or Perceptual only (PDQ)

Search does **not** require an email. Owner contact info is collected only on **option 2 — Image Series Similarity - Export Embeddings**.

### Outputs

- Sortable results table — one row per hit
- **Local hits:** Path shows filename; click to preview
- **Imported hits:** Path shows content ID; metadata shows **Source: Imported**, **Owner**, **Organization**, **Content ID**, **Embedding type**

### About PDQ

Perceptual hashing matches images that look similar despite resize, compression, or minor edits. PDQ-only mode works best when the folder contains **one series** only.

## Option 2: Image Series Similarity - Export Embeddings

Chatbot menu: **Image Series Similarity - Export Embeddings** — separate plugin option, not part of the search form.

- **Organization** (required) — your organization, for follow-up by importers
- **Contact email** (required) — stored on every exported record

**Submit** downloads a `.json` file. Run **Image Series Similarity** on a folder first so private embeddings exist.

| Shared in export | NOT shared |
|------------------|------------|
| Anonymized embedding | Original images |
| Organization and contact email | File paths |

## Option 3: Image Series Similarity - Import Embeddings

Chatbot menu: **Image Series Similarity - Import Embeddings** — separate plugin option.

- **Embeddings file (.json)** — file from another organization or user

Duplicates are skipped automatically. Owner contact info comes from each record in the file.

## How it works (brief)

1. Scan the input directory; reuse existing embeddings when the file is already indexed (by path or content SHA-256).
2. **Plain** and **private** embeddings are stored for every local file.
3. Search runs both embedding types and merges the top results.
4. Imported embeddings from other organizations or users are included in the private search.

## Notes

- Search covers your input folder plus all imported private embeddings.
- **GPU** speeds up inference; CPU works but is slower on large folders.
- **Pipeline:** Compatible with plugins that consume or produce `BatchFileResponse` / file lists.

## Supported image types

`.jpg`, `.jpeg`, `.png`, `.bmp`, `.gif`, `.tiff`, `.webp`

## Dependencies

`transformers`, `onnxruntime`, `pdqhash`, `pillow`, `numpy`, PostgreSQL with **pgvector**, `sqlmodel` / `sqlalchemy`.
