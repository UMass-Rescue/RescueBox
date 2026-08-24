# Image Similarity Search

This plugin has **three tasks:**

| Task | What it does |
|------|--------------|
| **Find series matches** | Search for similar images in a folder |
| **Export private embeddings** | Save anonymized data to share with other agencies |
| **Import private embeddings** | Load data received from another agency |

**Series:** A series is a collection of images that are related **temporally** and in terms of **subject or subject matter**. For example, photos taken at a birthday party would all be part of the same series. Photos of the same person taken at different times and places would **not** be part of the same series.

Embeddings are stored in the database. If images have already been processed by a prior run, they are **reused** — no double computation.

## When to Use This Plugin

| I have... | I want... | Use |
|---|---|---|
| A **birthday party image** | Other images from the **same birthday party** | **Image Similarity** (this plugin) |
| A **text description** | Photos that **match the description** | Image Search |
| A **photo** | A **text description** of what's in it | Image Summary |
| A **photo** with people | **Age and gender** of each person | Age-Gender Classifier |

### Use case 1: Find other images from the same series

The model embeds the **entire image** holistically — people, objects, background, lighting all contribute. Images from the same event naturally match well because they share many visual elements (same venue, same people, same lighting). Use a full uncropped photo as the query.

### Use case 2: Find images of a specific subject

To find images containing a specific object or person, **crop the query image** so that subject fills most of the frame. The model will then match based on that subject's visual features.

### Better with a text query?

If you're looking for a concept like "people eating" rather than a specific scene, use the **Image Search** plugin with a text description instead. This plugin works best when the query image clearly represents what you're looking for — a single event, a single subject, or a cropped subject of interest.

## Inputs

- **Input directory:** Folder containing image files to search within.

- **Query image:** A reference image file. The plugin returns images from the same series in the directory, excluding the query image itself from results.

## Parameters

- **Your email:** Contact email that identifies who ingested the embeddings. Required for cross-agency sharing — when embeddings are exported and matched on another machine, this lets the receiving agency know who to contact about a match.

- **CLIP model:** `google/siglip2-so400m-patch14-384` (SigLIP2-SO400M, 1152-dim, Apache 2.0).

- **Top K:** How many highest-similarity images to return (1–20, default 5).

- **Match threshold:** Similarity in 0–1; results at or above this count as a match in metadata. Image-to-image similarity scores are typically higher than text-to-image (~0.5–0.9 for related content).

- **Scoring mode:** Combined (60% CLIP + 40% PDQ, default), Semantic only (CLIP), or Perceptual only (PDQ). CLIP compares **scene content** (what's in the image); PDQ compares **pixel structure** (exact or near-duplicate detection). Combined uses both.

### About PDQ (Perceptual Hashing)

Perceptual hashing identifies images that look the same or similar despite minor changes such as resizing, compression, cropping, or slight color and brightness adjustments. It compares how an image looks, including the arrangement of visual patterns, rather than what the image contains. As a result, images that look similar may match even if they contain different subjects, while images of the same subject may not match if they have different viewpoints, scales, or layouts.

**Examples:**

- **Potential match:** A photo of a red apple and a photo of a red tomato placed in the same position on the same white table and taken from the same angle may produce similar hashes because the overall appearance and arrangement of visual patterns are similar.
- **Potential non-match:** Two photos of the same car, where one is a close-up of the headlight and the other shows the entire vehicle, may produce different hashes because the images have different framing and visual layouts.

**Note:** When using PDQ-only scoring mode, the input folder should contain images from only one series (e.g., only Bernie Sanders rally photos or only Kamala Harris event photos). Mixing multiple series will produce confusing results since PDQ matches visual structure, not semantic content.

## Supported Image Types

- `.jpg`, `.jpeg`, `.png`, `.bmp`, `.gif`, `.tiff`, `.webp`

## Outputs

- **Batch file response:** One row per ranked hit (`output_type`: `batchfile`). Each row includes the image **path**, rank/similarity in the title, and metadata (query label, similarity, match yes/no, model, id).

- In the RescueBox UI this appears as a **sortable table**; **click a row** to open or preview the image.

- If nothing scores in the top-k list, `files` may be empty.

## How It Works (brief)

1. Scan the input directory; for each image, check if its embedding already exists (by path or content SHA-256). Only compute and store new vectors for files not already in the database.
2. **Plain embeddings** are always created and stored in the plain table.
3. **When anonymization is ON:** CLIPSeg blacks out faces, people, text, signs, and logos, then the anonymized image is embedded and stored in a separate private table.
4. Look up or compute the **query image's** embedding and PDQ hash.
5. Compare query image against directory images and return **top-k** results. With anonymization ON, both query image and directory use their private embeddings.

## Sharing With Other Agencies (Export/Import)

Share image data with other agencies **without sharing the actual images**. Only the anonymized embeddings are shared.

| Shared | NOT Shared |
|--------|------------|
| Anonymized embedding (for matching) | Original images |
| Owner's email (for follow-up) | File paths |

### Export

Select **"Export private embeddings"** from the task menu.

- **Filter by email:** Leave empty to export all, or enter an email to export only that user's data

Creates a `.json` file you can download and send to another agency.

### Import

Select **"Import private embeddings"** from the task menu.

- **Embeddings file:** The `.json` file you received

Duplicates are automatically skipped. Owner contact info comes from each record in the file.

### Workflow

1. Run searches with "Create anonymized embeddings" ON
2. Export to a `.json` file
3. Send the file to partner agency
4. Partner imports and searches — matches show your email for follow-up

## Notes

- Search is **within the given folder's embedded set** for that job, not a global search across unrelated past embeddings.

- **GPU** speeds up inference; CPU works but is slower on large folders.

- **Pipeline:** Compatible with other plugins that consume or produce `BatchFileResponse` / file lists.

## Dependencies

- `transformers`, `onnxruntime`, `pdqhash`, `pillow`, `numpy`, PostgreSQL with **pgvector**, `sqlmodel` / `sqlalchemy`.
