# Image Similarity Plugin

This plugin finds visually similar images given a query image. It embeds every image in a directory using a CLIP model and ranks them by cosine similarity using pgvector.

Default model: [`google/siglip2-so400m-patch14-384`](https://huggingface.co/google/siglip2-so400m-patch14-384) (Apache 2.0, 1152-dim).

## Features

### Embed + search (`/search_similar_images`)

Single endpoint that:

1. For each image in the directory: if a row for that `(path, model_name)` (or `(content_sha256, model_name)`) already exists in `image_similarity_embeddings`, it **reuses** it. Otherwise it embeds, normalizes, and **stores** the vector.
2. Embeds the **query image** the same way (also reusing if already in the DB).
3. **Ranks** the directory images with pgvector cosine distance and returns the **top_k** paths.

Embeddings are stored in a dedicated `image_similarity_embeddings` table, separate from the text-to-image `image_embeddings` table, because different vision encoders produce embeddings in different vector spaces.

## Installation

### Install dependencies

From the project root:

```bash
poetry install
```

### Download the ONNX model

Create the model directory and pull the canonical ONNX export from [`onnx-community/siglip2-so400m-patch14-384-ONNX`](https://huggingface.co/onnx-community/siglip2-so400m-patch14-384-ONNX) (~1.7 GB, not committed to git):

```bash
mkdir -p src/image-similarity/image_similarity/onnx_models
curl -L -o src/image-similarity/image_similarity/onnx_models/siglip2-so400m-patch14-384.onnx \
  https://huggingface.co/onnx-community/siglip2-so400m-patch14-384-ONNX/resolve/main/onnx/vision_model.onnx
```

## Usage

**CLI:** pass folder and query image as `input_dir|||query_image_path`. Parameters: `top_k,min_similarity` (omit trailing values for defaults).

```bash
rescuebox image_similarity /search_similar_images "/path/to/photos|||/path/to/query.jpg" "5,0.5"
```

**Inputs (HTTP/UI):**

- `input_dir` — directory of images to search within
- `query_image` — reference image file

**Parameters:**

- `top_k` (1–20, default: 5) — number of highest-similarity images to return
- `min_similarity` (0–1, default: 0.5) — Match column uses this floor

The encoder is fixed to `google/siglip2-so400m-patch14-384` (the bundled ONNX model), so it is not a user-facing parameter.

**Output:** `BatchFileResponse` (`output_type`: `batchfile`) — one `FileResponse` per ranked hit (image path, title with rank/similarity, metadata: Query, Similarity, Match, Model, id). The RescueBox UI renders this as a **sortable table, click a row to open/preview the image**. If there are no hits, `files` is an empty list.

## How It Works

1. **Embed**: Scan the input directory, encode each image with the CLIP vision tower (ONNX Runtime), normalize vectors, and **persist** rows in PostgreSQL.
2. **Query**: Encode the query image with the **same** model and normalize.
3. **Rank**: Score **only the images in this request** with pgvector cosine distance (`<=>`), sort descending, return **top_k**.

## Model Information

### SigLIP 2 SO400M (patch14, 384²)
- **Embedding dimension**: 1152
- **Image encoder**: Shape-Optimized 400M-parameter Vision Transformer, 14×14 patches, 384×384 input
- **License**: Apache 2.0
- **Use case**: High-accuracy image-to-image similarity

## Benchmarks

Embedding-only numbers (not the full plugin pipeline) for SO400M SigLIP-2, measured on the OpenCLIP/timm port `ViT-SO400M-14-SigLIP2-378`. This is the same model family as what the plugin ships (`google/siglip2-so400m-patch14-384` is the HF Transformers port at 384², near-equivalent quality).

- **Hardware**: NVIDIA RTX 5090 (32 GB VRAM), PyTorch 2.11.0, CUDA 13.0
- **Dataset**: 503 images grouped into **series** of semantically-related images (e.g. photos from the same event, location, or theme — not necessarily the same subject or pixel-level duplicates). A retrieval counts as correct if **any other image from the query's series** appears in the top-`k` results — we're measuring how well the model clusters semantically related content in vector space. Batch size 200.
- **Throughput**: 14.1 images/second
- **Peak GPU memory**: 11.78 GB — the maximum VRAM used during inference, so any GPU with at least ~12 GB can run this batch size
- **Retrieval accuracy**: top-1 = 93%, top-5 = 98%, top-10 = 99%

Selected over three alternatives (LAION CLIP-H, DFN5B, SigLIP-2-gopt) as the best trade-off between accuracy, GPU memory, throughput, and Apache-2.0 licensing.

## Dependencies

- `transformers`: image preprocessor (`AutoProcessor`)
- `onnxruntime`: vision-tower inference
- `pillow`: image loading
- `sqlmodel`, `sqlalchemy`, `pgvector`: storage and similarity search

## Database Schema

```sql
CREATE TABLE image_similarity_embeddings (
    id SERIAL PRIMARY KEY,
    path VARCHAR NOT NULL,
    content_sha256 VARCHAR NOT NULL,
    model_name VARCHAR NOT NULL,
    embedding VECTOR(1152) NOT NULL
);

CREATE INDEX ON image_similarity_embeddings (path);
CREATE INDEX ON image_similarity_embeddings (content_sha256);
CREATE INDEX ON image_similarity_embeddings USING hnsw (embedding vector_l2_ops);
```

## Tips for Best Results

1. **Model Consistency**: Use one model per dataset — embeddings from different CLIP models are not comparable.
2. **GPU**: On CUDA hosts (`onnxruntime-gpu` installed), inference runs at GPU speed (tens of ms/image). On macOS, ORT falls back to CPU because it has no MPS provider and CoreML doesn't accelerate SigLIP-2's ops well.
3. **Threshold**: Image-to-image similarity scores are typically higher than text-to-image (~0.5–0.9 for related content).

## Tests

```bash
poetry run pytest src/image-similarity/tests
```

The unit tests cover task schema, types, and CLI parsers — none of these require the ONNX file. End-to-end runs require the model downloaded as above.
