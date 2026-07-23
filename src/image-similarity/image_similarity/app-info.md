# Image Similarity Search

**Series:** A series is a collection of images that are related **temporally** and in terms of **subject or subject matter**. For example, photos taken at a birthday party would all be part of the same series. Photos of the same person taken at different times and places would **not** be part of the same series. See the [UMass-Rescue/image-series-dataset](https://github.com/UMass-Rescue/image-series-dataset) for examples.

This plugin finds images from the **same series** as a query image. It embeds all images in a folder using a SigLIP2 vision encoder (ONNX Runtime) and ranks them using a configurable scoring mode combining semantic similarity and perceptual hashing.

Embeddings are stored in a dedicated PostgreSQL (pgvector) `image_similarity_embeddings` table. If images have already been embedded by a prior run, their vectors are **reused** — no double computation.

**Route:** `/search_series`

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

- **Scoring mode:** Combined (CLIP + PDQ, default), Semantic only (CLIP), or Perceptual only (PDQ). CLIP compares **scene content** (what's in the image); PDQ compares **pixel structure** (exact or near-duplicate detection). Combined uses both.

## Supported Image Types

- `.jpg`, `.jpeg`, `.png`, `.bmp`, `.gif`, `.tiff`, `.webp`

## Outputs

- **Batch file response:** One row per ranked hit (`output_type`: `batchfile`). Each row includes the image **path**, rank/similarity in the title, and metadata (query label, similarity, match yes/no, model, id).

- In the RescueBox UI this appears as a **sortable table**; **click a row** to open or preview the image.

- If nothing scores in the top-k list, `files` may be empty.

## How It Works (brief)

1. Scan the input directory; for each image, check if its embedding already exists in `image_similarity_embeddings` (by path or content SHA-256). Only compute and store new vectors for files not already in the database.
2. **Dual ingestion:** For each image, create both a **plain** embedding (raw pixels) and a **private** embedding (SAM3-anonymized — faces, text, logos blacked out before encoding). Private embeddings are stored with a `+anonymized` model name suffix.
3. Compute PDQ perceptual hashes for all images (backfilling any that are missing).
4. Look up or compute the **query image's** embedding and PDQ hash.
5. Rank **only** the directory images using the selected scoring mode against **plain** embeddings, return **top-k** results. (Future PRs will add cross-machine query merging plain + private results.)

## Notes

- Search is **within the given folder's embedded set** for that job, not a global search across unrelated past embeddings.

- **GPU** speeds up inference; CPU works but is slower on large folders.

- **Pipeline:** Compatible with other plugins that consume or produce `BatchFileResponse` / file lists.

## Dependencies

- `transformers`, `onnxruntime`, `pdqhash`, `pillow`, `numpy`, `samexporter`, `huggingface-hub`, PostgreSQL with **pgvector**, `sqlmodel` / `sqlalchemy`.
