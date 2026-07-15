# Image Similarity Search

This plugin finds **visually similar images** given a query image. It embeds all images in a folder using a SigLIP2 vision encoder (ONNX Runtime) and ranks them using a configurable scoring mode combining semantic similarity and perceptual hashing.

Embeddings are stored in a dedicated PostgreSQL (pgvector) `image_similarity_embeddings` table. If images have already been embedded by a prior run, their vectors are **reused** — no double computation.

**Route:** `/search_similar_images`

## Which Plugin Should I Use?

| I have... | I want... | Use |
|---|---|---|
| A **photo** | Other photos that **look like it** | **Image Similarity** (this plugin) |
| A **text description** | Photos that **match the description** | Image Search |
| A **photo** | A **text description** of what's in it | Image Summary |
| A **photo** with people | **Age and gender** of each person | Age-Gender Classifier |

This plugin takes an image as input and finds visually similar images from a folder — same event, same scene, same setting, or near-duplicates. The model considers the entire image (people, objects, background, lighting), so images from the same event naturally match well even with busy multi-person scenes. To isolate a specific object or person, crop the query image so that subject fills most of the frame.

## Inputs

- **Input directory:** Folder containing image files to search within.

- **Query image:** A reference image file. The plugin returns the most visually similar images from the directory, excluding the query image itself from results.

## Parameters

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
2. Compute PDQ perceptual hashes for all images (backfilling any that are missing).
3. Look up or compute the **query image's** embedding and PDQ hash.
4. Rank **only** the directory images using the selected scoring mode, return **top-k** results.

## Notes

- Search is **within the given folder's embedded set** for that job, not a global search across unrelated past embeddings.

- **GPU** speeds up inference; CPU works but is slower on large folders.

- **Pipeline:** Compatible with other plugins that consume or produce `BatchFileResponse` / file lists.

## Dependencies

- `transformers`, `onnxruntime`, `pdqhash`, `pillow`, `numpy`, PostgreSQL with **pgvector**, `sqlmodel` / `sqlalchemy`.
