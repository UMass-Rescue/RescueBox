# Image Similarity Search (CLIP)

This plugin finds **visually similar images** given a query image. It uses CLIP to embed all images in a folder and then ranks them by cosine similarity to the query image's embedding.

Embeddings are stored in the same PostgreSQL (pgvector) `image_embeddings` table used by the text-to-image **Search Images** plugin. If images have already been embedded by that plugin (or by a prior run of this one), their vectors are **reused** — no double computation.

**Route:** `/search_similar_images`

## Inputs

- **Input directory:** Folder containing image files to search within.

- **Query image:** A reference image file. The plugin returns the most visually similar images from the directory, excluding the query image itself from results.

## Parameters

- **CLIP model:** `apple/DFN5B-CLIP-ViT-H-14-378` current favorite.

- **Top K:** How many highest-similarity images to return (1–20, default 5).

- **Match threshold:** Similarity in 0–1; results at or above this count as a match in metadata. Image-to-image similarity scores are typically higher than text-to-image (~0.5–0.9 for related content).

## Supported Image Types

- `.jpg`, `.jpeg`, `.png`, `.bmp`, `.gif`, `.tiff`, `.webp`

## Outputs

- **Batch file response:** One row per ranked hit (`output_type`: `batchfile`). Each row includes the image **path**, rank/similarity in the title, and metadata (query label, similarity, match yes/no, model, id).

- In the RescueBox UI this appears as a **sortable table**; **click a row** to open or preview the image.

- If nothing scores in the top-k list, `files` may be empty.

## How It Works (brief)

1. Scan the input directory; for each image, check if its embedding already exists in `image_embeddings` (by path or content SHA-256). Only compute and store new CLIP image vectors for files not already in the database.
2. Look up or compute the **query image's** CLIP embedding. If it already exists in the DB (e.g. it is inside the directory, or was embedded in a prior run), that stored vector is reused.
3. Rank **only** the directory images using pgvector cosine similarity against the query embedding, return **top-k** results.

## Notes

- Search is **within the given folder's embedded set** for that job, not a global search across unrelated past embeddings.

- Both this plugin and the **Search Images** (text-to-image) plugin share the same `image_embeddings` table. Running one seeds the table for the other — embeddings are computed once and reused across both search modes.

- **GPU** speeds up CLIP; CPU works but is slower on large folders.

- **Pipeline:** Compatible with other plugins that consume or produce `BatchFileResponse` / file lists.

## Dependencies

- `transformers`, `torch`, `pillow`, `numpy`, PostgreSQL with **pgvector**, `sqlmodel` / `sqlalchemy`.
