# Image Similarity Search

This plugin finds **visually similar images** given a query image. It semantically hashes every image in a folder using a CLIP model and ranks them by cosine similarity to the query image's embedding.

Embeddings are stored in the plugin's own PostgreSQL (pgvector) `image_similarity_embeddings` table. Vectors from prior runs of this plugin are **reused** — no double computation. Rows are keyed by `(path, model_name)` so future model swaps can coexist with old data.

**Route:** `/search_similar_images`

## Inputs

- **Input directory:** Folder containing image files to search within.

- **Query image:** A reference image file. The plugin returns the most visually similar images from the directory, excluding the query image itself from results.

## Parameters

- **Vision model:** `google/siglip2-so400m-patch14-384` (Apache 2.0 license; 1152-dim embeddings).

- **Top K:** How many highest-similarity images to return (1–20, default 5).

- **Match threshold:** Similarity in 0–1; results at or above this count as a match in metadata. Image-to-image similarity scores are typically higher than text-to-image (~0.5–0.9 for related content).

## Supported Image Types

- `.jpg`, `.jpeg`, `.png`, `.bmp`, `.gif`, `.tiff`, `.webp`

## Outputs

- **Batch file response:** One row per ranked hit (`output_type`: `batchfile`). Each row includes the image **path**, rank/similarity in the title, and metadata (query label, similarity, match yes/no, model, id).

- In the RescueBox UI this appears as a **sortable table**; **click a row** to open or preview the image.

- If nothing scores in the top-k list, `files` may be empty.

## How It Works (brief)

1. Scan the input directory; for each image, check if its embedding already exists in `image_similarity_embeddings` (by path or content SHA-256, for the current `model_name`). Only compute and store new image vectors for files not already in the database.
2. Look up or compute the **query image's** embedding. If it already exists in the DB, that stored vector is reused.
3. Rank **only** the directory images using pgvector cosine similarity against the query embedding, return **top-k** results.

## Notes

- Search is **within the given folder's embedded set** for that job, not a global search across unrelated past embeddings.

- This plugin keeps its own `image_similarity_embeddings` table, separate from the text-to-image **Search Images** plugin's `image_embeddings` table. Different vision encoders produce embeddings in different vector spaces, so cross-plugin reuse would be incorrect.

- **GPU** speeds up inference; CPU works but is slower on large folders.

- **Pipeline:** Compatible with other plugins that consume or produce `BatchFileResponse` / file lists.

## Dependencies

- `transformers`, `onnxruntime`, `pillow`, `numpy`, PostgreSQL with **pgvector**, `sqlmodel` / `sqlalchemy`.
