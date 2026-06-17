# Image Embeddings Plugin

This plugin generates image embeddings using OpenAI's CLIP (Contrastive Language-Image Pre-Training) models and provides cross-modal text-to-image search capabilities.

## Features

### Embed + search (`/search_images`)

Single endpoint that:

1. For each image file in the directory: if a row for that **path** already exists in `image_embeddings`, it **reuses** it (no re-encode). Otherwise it **embeds**, normalizes, and **stores** the vector (PostgreSQL / pgvector). This supports the same folder with **new text queries** on repeat jobs without redoing CLIP on every file.
2. **Encodes** your text query with CLIP’s text encoder.
3. **Ranks** those folder images (reused + newly embedded) with pgvector and returns the **top_k** paths.

The table does not store CLIP `model_name` per row; reuse is by **path string** only. If you change `model_name` for the same files, delete or re-embed as needed so vectors stay consistent.

CLIP model options:

- `openai/clip-vit-base-patch32` (Base, 512-dim, faster)
- `openai/clip-vit-large-patch14` (Large, 768-dim, more accurate)

## Usage

**CLI:** pass folder and query as `input_dir|||query`. Parameters: `model_name,top_k,min_similarity` (omit trailing values for defaults).

```bash
rescuebox image_embeddings /search_images "/path/to/images|||a cat sitting on a couch" "openai/clip-vit-base-patch32,5,0.21"
```

**Inputs (HTTP/UI):**

- `input_dir` — directory of images to embed and search within
- `query` — natural language description

**Parameters:**

- `model_name` (default: `openai/clip-vit-base-patch32`)
- `top_k` (1–20, default: 5) — number of highest-similarity images to return
- `min_similarity` (0–1, default ~0.21) — Match column uses this floor

**Output:** `BatchFileResponse` (`output_type`: `batchfile`) — one `FileResponse` per ranked hit (image path, title with rank/similarity, metadata: Query, Similarity, Match, Model, id). The RescueBox UI renders this like other batch image results: **sortable table, click a row to open/preview the image**. If there are no hits, `files` is an empty list.

## How It Works

1. **Embed**: Scan the input directory, encode each image with CLIP, normalize vectors, and **persist** rows in PostgreSQL.
2. **Query**: Encode the text with the **same** CLIP model and normalize.
3. **Rank**: Score **only the images embedded in this request** with dot product (cosine similarity on normalized vectors), sort descending, return **top_k**.

Global search across older rows in the table is not used for ranking; each run searches within the folder batch you just embedded.

### Why CLIP Enables Text-to-Image Search

CLIP is uniquely designed for cross-modal search:
- **Shared Embedding Space**: Text and image embeddings live in the same vector space
- **Contrastive Training**: Trained to align matching text-image pairs
- **Zero-Shot**: Works on arbitrary text queries without fine-tuning
- **Semantic Understanding**: Captures high-level semantic meaning, not just keywords

## Performance notes

- **Storage**: Embeddings are still stored in PostgreSQL for reuse and tooling.
- **Ranking**: After commit, top‑`k` matches are resolved with **pgvector** (`<=>`), restricted with `WHERE path IN (...)` to **only** the paths embedded in this request (so the index still helps on large batches).
- **pgvector**: Table and indexes remain useful if you add other SQL-driven search later.

## Model Information

### CLIP ViT-B/32
- **Embedding dimension**: 512
- **Image encoder**: Vision Transformer Base with 32×32 patches
- **Text encoder**: Transformer with 63M parameters
- **Speed**: Faster inference
- **Use case**: General purpose, production deployments

### CLIP ViT-L/14
- **Embedding dimension**: 768
- **Image encoder**: Vision Transformer Large with 14×14 patches
- **Text encoder**: Transformer with 123M parameters
- **Speed**: Slower inference
- **Use case**: Higher accuracy needed, research

## Dependencies

- `transformers`: Hugging Face Transformers for CLIP
- `torch`: PyTorch for model inference
- `pillow`: Image processing library
- `sqlmodel`: Database ORM
- `pgvector`: PostgreSQL vector extension
- `sqlalchemy`: Raw SQL queries for optimization

## Database Schema

```sql
CREATE TABLE image_embeddings (
    id SERIAL PRIMARY KEY,
    path VARCHAR NOT NULL,
    embedding VECTOR(512) NOT NULL  -- 512 for base, 768 for large
);

CREATE INDEX ON image_embeddings (path);
CREATE INDEX ON image_embeddings USING ivfflat (embedding vector_cosine_ops);
```

## Example Use Cases

### 1. Content-Based Image Search
```bash
rescuebox image_embeddings /search_images "./photos|||sunset over mountains" "openai/clip-vit-base-patch32,10"
```

### 2. Semantic Image Discovery
```bash
rescuebox image_embeddings /search_images "./photos|||happiness and joy" "openai/clip-vit-base-patch32,5"
```

### 3. Visual Forensics
```bash
rescuebox image_embeddings /search_images "./case_photos|||outdoor crime scene at night" "openai/clip-vit-base-patch32,20"
```

### 4. Dataset Exploration
```bash
rescuebox image_embeddings /search_images "./dataset|||person wearing blue jacket" "openai/clip-vit-base-patch32,15"
```

## Tips for Best Results

1. **Model Consistency**: Use one CLIP model per run (embedding and query share the same weights)
2. **Descriptive Queries**: Use natural language descriptions, not just keywords
   - ✅ Good: "a red car parked in front of a house"
   - ❌ Less effective: "car red house"
3. **Specificity**: More specific queries generally yield better results
4. **Context Matters**: Include relevant context in your query
5. **Top-K Selection**: Start with 10-20 results for exploration, narrow down as needed
6. **Normalization**: Both text and image embeddings are automatically normalized

## Comparison with Text Embeddings

| Feature | Text Embeddings | Image Embeddings |
|---------|----------------|------------------|
| Input | Text files | Image files |
| Query Type | Text → Text | **Text → Image** |
| Model | SentenceTransformer | CLIP |
| Embedding Dim | 384/768 | 512/768 |
| Search Type | Semantic text search | Cross-modal visual search |

## Example Workflow

```bash
# Embed images under ./crime_scene_photos and rank by text query (same call)
rescuebox image_embeddings /search_images "./crime_scene_photos|||damaged vehicle front view" "openai/clip-vit-base-patch32,10"

# Refine with another query on the same folder (re-embeds then searches)
rescuebox image_embeddings /search_images "./crime_scene_photos|||vehicle with broken windshield" "openai/clip-vit-base-patch32,5"
```

## Advanced: Multi-Modal Search Pipeline

Combine text and image workflows:

```bash
# Search documents
rescuebox text_embeddings /search_text "vehicle collision report" "all-MiniLM-L6-v2,5"

# Embed a folder of images and search by description
rescuebox image_embeddings /search_images "./evidence/photos|||car accident aftermath" "openai/clip-vit-base-patch32,5"
```
