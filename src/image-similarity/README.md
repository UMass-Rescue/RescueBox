# Image Similarity Plugin

Finds images from the **same series** as a query image.

**Series:** Images related **temporally** and by **subject matter** (e.g. one birthday party). Photos of the same person at different times and places are **not** one series.

## Chatbot plugin menu

In the **Assistant** tool picker, these are **three separate plugin options** (same backend service, different menu entries):

| # | Chatbot menu option | CLI route | What it does |
|---|---------------------|-----------|--------------|
| **1** | **Image Series Similarity** | `/search_series` | Search for similar images in a folder |
| **2** | **Export Private Embeddings** | `/export_embeddings` | Save anonymized embeddings to a `.json` for another agency |
| **3** | **Import Private Embeddings** | `/import_embeddings` | Load a `.json` received from another agency |

Slash shortcuts: `/search-series`, `/export-private-embeddings`, `/import-private-embeddings`.

## Workflows

### Local search (option 1)

Pick **Image Series Similarity** in the chatbot plugin menu (or use CLI below).

```bash
rescuebox image_series_similarity /search_series \
  "/path/to/photos|||/path/to/query.jpg" ",5,0.5,combined"
```

### Agency A — share embeddings (option 1 → option 2)

1. **Image Series Similarity** with **Create anonymized embeddings: Yes** on your case folder
2. **Export Private Embeddings** in the chatbot plugin menu — **Organization** + **Contact email**

```bash
rescuebox image_series_similarity /export_embeddings _ "My Agency,owner@example.com"
```

3. Send the `.json` to the partner agency

### Agency B — import and search (option 3 → option 1)

1. **Import Private Embeddings** in the chatbot plugin menu

```bash
rescuebox image_series_similarity /import_embeddings "/path/to/file.json"
```

2. **Image Series Similarity** on your case folder with **Create anonymized embeddings: Yes**
3. Review results:
   - **Local** rows — Path shows filename; click to preview
   - **Imported** rows — Path blank; use **Owner**, **Organization**, and **Content ID** to follow up with the exporting agency

### Agency A — resolve Content ID

**Content ID** is the first 12 characters of the SHA-256 hash of the original file bytes (`content_sha256` in export JSON). Agency B emails this to Agency A — Agency B cannot resolve it to a filepath.

Agency A looks up the path in the embedding database. Plain embeddings are always indexed locally; anonymized search also writes the private table. Search both. Replace `a1b2c3d4e5f6` with the prefix Agency B sent (omit `…`):

```bash
docker exec -i rb-postgres psql -U rbuser -d rescuebox -c "
SELECT path, content_sha256
FROM image_similarity_private_embeddings
WHERE content_sha256 LIKE 'a1b2c3d4e5f6%'
UNION ALL
SELECT path, content_sha256
FROM image_similarity_embeddings
WHERE content_sha256 LIKE 'a1b2c3d4e5f6%';
"
```

Database runs in Docker (`rb-postgres`). Start with `startup/pgvector_start.sh` if needed.

Host `psql` (port 5433):

```bash
psql postgresql://rbuser:rescue@127.0.0.1:5433/rescuebox -c "
SELECT path, content_sha256
FROM image_similarity_private_embeddings
WHERE content_sha256 LIKE 'a1b2c3d4e5f6%'
UNION ALL
SELECT path, content_sha256
FROM image_similarity_embeddings
WHERE content_sha256 LIKE 'a1b2c3d4e5f6%';
"
```

## When it works

1. **Same series** — full query photo → other photos from the same event/scene
2. **Specific subject** — crop the query to one subject → images containing that subject

For concept search ("people eating"), use the **Image Search** plugin with text instead.

## Option 1: Image Series Similarity (`/search_series`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `enable_anonymized` | `no` | `yes` — blackout + search imported partner embeddings |
| `model_name` | `google/siglip2-so400m-patch14-384` | Vision encoder |
| `top_k` | 5 | Results to return (1–20) |
| `min_similarity` | 0.5 | Minimum score for "match" in metadata |
| `scoring_mode` | `combined` | `combined`, `semantic`, or `pdq` |

Search does **not** require an email. Owner contact info is collected only on **option 2 — Export Private Embeddings**.

### Scoring modes

| Mode | Compares | When to use |
|------|----------|-------------|
| `combined` | 60% CLIP + 40% PDQ | Default |
| `semantic` | Scene content (CLIP) | Different angles, same subject |
| `pdq` | Pixel structure | Near-duplicates only; one series per folder |

### Anonymization

**OFF:** match on everything visible in the photos.

**ON:** faces, people, text, signs, and logos are blacked out before embedding. Match on background, layout, and remaining objects. Required before option 2 export and to search imported embeddings after option 3.

**Test:** `src-tauri/demo/image-similarity/inputs/`, query `Bernie_Sanders_2016_068_*`, anonymization **Yes**, scoring **combined** or **semantic**.

## Option 2: Export Private Embeddings (`/export_embeddings`)

Separate chatbot plugin option — organization and contact email required (stored as owner contact info on exported records).

| Shared | NOT shared |
|--------|------------|
| Anonymized embedding | Original images |
| Organization and contact email | File paths |

Requires option 1 with **Create anonymized embeddings: Yes** first.

## Option 3: Import Private Embeddings (`/import_embeddings`)

Separate chatbot plugin option — select the partner `.json`. Duplicates skipped; owner info comes from the file.

## Installation

```bash
poetry install
```

Download ONNX models into `onnx_models/`:

**SigLIP2** (~1.7 GB):

```bash
mkdir -p src/image-similarity/image_similarity/onnx_models
curl -L -o src/image-similarity/image_similarity/onnx_models/siglip2-so400m-patch14-384.onnx \
  https://huggingface.co/onnx-community/siglip2-so400m-patch14-384-ONNX/resolve/main/onnx/vision_model.onnx
```

**CLIPSeg** (~545 MB) — save as `clipseg-rd64-refined.onnx` from [Xenova/clipseg-rd64-refined](https://huggingface.co/Xenova/clipseg-rd64-refined).

## Benchmarks

503 images, [image-series-dataset](https://github.com/UMass-Rescue/image-series-dataset), NVIDIA RTX 5090.

| Metric | Value |
|--------|-------|
| top-1 accuracy | 93% |
| top-5 accuracy | 98% |
| top-10 accuracy | 99% |
| Throughput | 14.1 img/s |
| Peak VRAM | 11.78 GB |

## Demo & testing

`src-tauri/demo/image-similarity/inputs/` — 85 images, 5 series (Bernie Sanders, Kishida, Harris, Le Pen, Bennett).

```bash
cd src/image-similarity && poetry install
rescuebox image_series_similarity /search_series \
  "src-tauri/demo/image-similarity/inputs/|||src-tauri/demo/image-similarity/inputs/Bernie_Sanders_2016_063.jpg" \
  ",5,0.5,combined"
```

## Unit tests

```bash
poetry run pytest src/image-similarity/tests
```

No ONNX file needed for unit tests.

## Dependencies

`transformers`, `onnxruntime`, `pdqhash`, `pillow`, `numpy`, `sqlmodel`, `sqlalchemy`, `pgvector`
