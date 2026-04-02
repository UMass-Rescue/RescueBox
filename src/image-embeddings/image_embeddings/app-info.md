# Image Embeddings (CLIP Search)

This plugin embeds images in a folder with OpenAI CLIP and runs **text-to-image search** over those images. You provide a directory of images and a natural-language **query**; it returns the top matches ranked by similarity. 

Embeddings are stored in PostgreSQL (pgvector) so repeat searches on the same folder can **reuse** vectors without re-encoding every image.

**Route:** `/search_images` (embed + search in one job).

## Inputs

- **Input directory:** Folder containing image files to embed and search within.

- **Text query:** What to look for in natural language (e.g. *a person wearing a red jacket*, 
*outdoor scene with trees*). 

Short single-word queries are often fuzzy; richer phrases usually work better.

## Parameters

- **CLIP model:** `openai/clip-vit-base-patch32` (faster, 512-dim) or `openai/clip-vit-large-patch14` (slower, 768-dim, often stronger).

- **Top K:** How many highest-similarity images to return (1–20, default 5).

- **Match threshold:** Similarity in 0–1; results at or above this count as a match in metadata. CLIP text–image scores are often roughly in the ~0.2–0.35 range for many queries—tune expectations accordingly.

## Supported Image Types

- `.jpg`, `.jpeg`, `.png`, `.bmp`, `.gif`, `.tiff`, `.webp`

## Outputs

- **Batch file response:** One row per ranked hit (`output_type`: `batchfile`). Each row includes the image **path**, rank/similarity in the title, and metadata (query, similarity, match yes/no, model, id). 

-In the RescueBox UI this appears as a **sortable table**; **click a row** to open or preview the image (same pattern as other batch image plugins). 

-If nothing scores in the top‑k list, `files` may be empty.

## How It Works (brief)

1. Scan the input directory; for each image, load the CLIP image encoder if the path is not already in `image_embeddings`, then store a normalized vector.
2. Encode the text query with the **same** CLIP model and normalize.
3. Rank **only** the images from this run’s path set using pgvector similarity, return **top_k** results.

Reuse is by **file path string**; the table does not record `model_name` per row. If you switch CLIP variants for the same files, vectors may be inconsistent until you re-embed or clear old rows.

## Notes

- Search is **within the given folder’s embedded set** for that job, not a global search across unrelated past embeddings.

- **GPU** speeds up CLIP; CPU works but is slower on large folders.

- **Pipeline:** Compatible with other plugins that consume or produce `BatchFileResponse` / file lists (e.g. optional **file filter** from a prior step when configured in the UI).

## Dependencies

- `transformers`, `torch`, `pillow`, PostgreSQL with **pgvector**, `sqlmodel` / `sqlalchemy`.
