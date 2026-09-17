# Image Similarity Search

Finds images from the **same series** as a query image.

**Series:** Images related **temporally** and by **subject matter** (e.g. one birthday party). Photos of the same person at different times and places are **not** one series.

Embeddings are stored in the database. Images processed in a prior run are **reused** — no double computation.

## Chatbot plugin menu

In the **Assistant**, the tool picker lists **three separate plugin options** grouped as **4.1–4.3** (not one plugin with sub-tasks). Pick the option you need:

| # | Chatbot menu option | Form / task | When to use |
|---|---------------------|-------------|-------------|
| **4.1** | **Image Series Similarity** | Find series matches | Search a local folder for images similar to a query photo |
| **4.2** | **Image Series Similarity - Export Embeddings** | Export embeddings | Download a `.json` to share with another organization or user |
| **4.3** | **Image Series Similarity - Import Embeddings** | Import embeddings | Load a `.json` from another organization or user |

Slash shortcuts: `/search-series`, `/export-private-embeddings`, `/import-private-embeddings`.

## Workflows

### Local search only (4.1)

1. **Assistant** → plugin menu → **Image Series Similarity**
2. **Input directory** — folder of images to search
3. **Query image** — select an image to find similar images against the input folder
4. **Submit** → local matches in the results table (Path shows filename; click to preview)

### Share embeddings (4.1, then 4.2)

1. **Image Series Similarity** on your case folder (indexes plain and private embeddings)
2. **Assistant** → plugin menu → **Image Series Similarity - Export Embeddings** → **Organization** and **Contact email** → **Submit** → download `.json`
3. Send the `.json` to another organization or user

### Import and search (4.3, then 4.1)

Another organization can share anonymized embeddings from their case without sending image files. You import their `.json` and search your own case folder against their embeddings plus your local files.

1. **Assistant** → plugin menu → **Image Series Similarity - Import Embeddings** → select `.json` from another organization or user → **Submit**
2. **Image Series Similarity** on your own case folder:
   - **Input directory** — your local images (required)
   - **Query image** — local reference photo
3. **Submit** → **Local** rows (filename, optional preview) and **Imported** rows (Source shows clickable **Imported** JSON with contact email, organization, and full content hash)

**Imported** rows are matches from the other organization's case data. You do not have their files — if a hit is relevant, click **Imported** in the Source column for contact info, then send the **Content ID** (first 12 characters of `content_sha256`) to request more information. Exporters may or may not include a filename — when absent, the Filename column shows *Not available*.


### Resolve Content ID (after follow-up from another user)

The importing user cannot resolve a Content ID to a filepath. When they email you the Content ID from an imported match, look up the local path in the RescueBox database (see README for the `docker exec … psql` command). Default credentials: username `rbuser`, password `rescue`, database `rescuebox`.

## When to use this plugin

| I have... | I want... | Use |
|---|---|---|
| A **birthday party image** | Other images from the **same birthday party** | **Image Similarity** (this plugin) |
| A **text description** | Photos that **match the description** | Image Search |
| A **photo** | A **text description** of what's in it | Image Summary |
| A **photo** with people | **Age and gender** of each person | Age-Gender Classifier |

**Use case — same series:** Use a full uncropped query photo. The model embeds the whole scene (people, background, lighting).

**Use case — specific subject:** Crop the query so one subject fills the frame.

**Use case — shared embeddings:** Import from another organization or user (4.3), then search your folder (4.1).

If you want a concept like "people eating" rather than a specific scene, use **Image Search** with a text query instead.

## 4.1 Image Series Similarity

Chatbot menu: **Image Series Similarity**. Form title: **Find series matches**.

### Inputs

- **Input directory** — folder containing image files to search
- **Query image** — select an image to find similar images against the input folder

### Parameters

- **CLIP model:** `google/siglip2-so400m-patch14-384` (SigLIP2-SO400M, 1152-dim)
- **Top K:** 1–20 results (default 5)
- **Match threshold:** 0–1; only results with similarity ≥ this value are returned
- **Scoring mode:** Combined (60% CLIP + 40% PDQ, default), Semantic only (CLIP), or Perceptual only (PDQ)

Search does **not** require an email. Owner contact info is collected only on **4.2 — Image Series Similarity - Export Embeddings**.

### Results

Search compares both **plain vs plain** (original images) and **private vs private** (anonymized images) and merges results into one ranked table. This privacy-enhanced search ensures that imported embeddings — which are always anonymized — are compared only against other anonymized embeddings.

| Column | Local rows | Imported rows |
|--------|-----------|---------------|
| **Preview** | Thumbnail when previews are enabled (file on disk) | *Not available* |
| **Filename** | Local basename | Basename if exporter included it, otherwise *Not available* |
| **Title** | Rank + similarity score | Rank + similarity score |
| **Source** | `Local` | Clickable **Imported** — JSON with contact email, organization, full `content_sha256`, optional filename and export file |

Both local and imported hits are ranked together by score. If an imported hit is relevant, click **Imported** in Source for contact info, then send the **Content ID** (first 12 characters of `content_sha256`) to request more information.

### About PDQ

Perceptual hashing matches images that look similar despite resize, compression, or minor edits. PDQ-only mode works best when the folder contains **one series** only.

### Anonymization

Every search automatically creates **both** plain and private (anonymized) embeddings — there is no toggle. Private embeddings black out **face**, **tattoo**, and **text** regions (CLIPSeg) before embedding.

## 4.2 Image Series Similarity - Export Embeddings

Chatbot menu: **Image Series Similarity - Export Embeddings** — separate plugin option.

Exports all your **private (anonymized) embeddings** to a `.json` file. The file does not contain original images or full file paths. Each search creates private embeddings automatically — run a search first so there are records to export.

- **Organization** (required) — so importers know who to contact
- **Contact email** (required) — stored on every exported record
- **Share filename** (default Yes) — include the original filename (basename only) in each record; set to No to omit it

The export file is a JSON object with `format_version`, `export_date`, `export_filename`, `count`, and a `records` array. Each record contains: embedding, content hash, perceptual hash, contact info, model, anonymization protocol, and **filename** (only when Share filename is Yes). In search results, imported rows without a filename show *Not available* in the Filename column — the full content hash is in the Source JSON.

## 4.3 Image Series Similarity - Import Embeddings

Chatbot menu: **Image Series Similarity - Import Embeddings** — separate plugin option.

Loads an exported `.json` into your database.

- **Embeddings file (.json)** — select the file received from another organization

Each imported record stores the same fields described in the export section above, plus `path = [imported]` (no local file).

After import, every search ranks your local images **and** the imported embeddings together. Imported records that score high enough appear as **Imported** rows in results.

Within a single import file, duplicate records (same `content_sha256` + `model_name`) are skipped. Records already indexed locally (same content hash) are skipped. Re-importing the same hash and model updates the existing imported row with all metadata.

## How it works (brief)

1. Scan the input directory; reuse existing embeddings when the file is already indexed (by path or content SHA-256).
2. **Plain** and **private** embeddings are stored for every local file (private: face, tattoo, and text blacked out).
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
