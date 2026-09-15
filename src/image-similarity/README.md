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

## Which plugin to use

| Goal | Plugin | Notes |
|------|--------|-------|
| Find similar photos in **your** folder | **Image Series Similarity** | Pick input directory + query image |
| Share your indexed photos with another team **without sending files** | **Export Private Embeddings** | Run search first so private embeddings exist |
| Search your case against another organization’s shared case data | **Import Private Embeddings**, then **Image Series Similarity** | Import their `.json`; search ranks your folder and their indexed embeddings |

All three are separate entries in the Assistant plugin menu (not sub-steps on one form).

## Workflows

### Local search only

**Image Series Similarity** → input directory + query image → Submit.

- Search always creates both plain and private (anonymized) embeddings automatically
- Results: **Local** rows with filename and preview

```bash
rescuebox image_series_similarity /search_series \
  "/path/to/photos|||/path/to/query.jpg" ",5,0.5,combined"
```

### Export / import — case data from another organization

Another team can share anonymized embeddings from their case without sending image files. You import their `.json` and search your own case folder against those embeddings plus your local files.

**Exporter**

1. **Image Series Similarity** on their case folder
2. **Export Private Embeddings** — Organization + Contact email → download `.json`

**Importer**

1. **Import Private Embeddings** → select the `.json`
2. **Image Series Similarity** on your case folder — local query image
3. **Local** rows — matches in your folder (preview available)
4. **Imported** rows — matches to their case data (no preview; you do not have their files). If a hit matters, contact **Owner** / **Organization** from the row and send the **Content ID** (content hash prefix) to request more information. They may or may not have included a **filename** in the export — when missing, use Content ID only.


```bash
rescuebox image_series_similarity /export_embeddings _ "My Agency,owner@example.com"
rescuebox image_series_similarity /import_embeddings "/path/to/file.json"
```

### Resolve Content ID (exporter side)

**Content ID** is the first 12 characters of the SHA-256 hash of the original file bytes (`content_sha256` in export JSON). The importer cannot resolve it to a filepath — they email it to you. Look up the path in the embedding database. Replace `a1b2c3d4e5f6` with the prefix they sent (omit `…`):

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

Database runs in Docker (`rb-postgres`). Start with `startup/pgvector_start.sh` if needed. Default credentials: username `rbuser`, password `rescue`, database `rescuebox`.

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
| `model_name` | `google/siglip2-so400m-patch14-384` | Vision encoder |
| `top_k` | 5 | Results to return (1–20) |
| `min_similarity` | 0.5 | Minimum score for "match" in metadata |
| `scoring_mode` | `combined` | `combined`, `semantic`, or `pdq` |

Search does **not** require an email. Owner contact info is collected only on **option 2 — Export Private Embeddings**.

### Results

Search compares both **plain vs plain** (original images) and **private vs private** (anonymized images) and merges results into one ranked table. This privacy-enhanced search ensures that imported embeddings — which are always anonymized — are compared only against other anonymized embeddings. Example top-5 after importing another organization's embeddings:

| Preview | Filename | Title | Source |
|---------|----------|-------|--------|
| thumbnail | `Bernie_Sanders_2016_070…16.jpg` | #1 · similarity 0.97 | **Imported** |
| thumbnail | `Bernie_Sanders_2016_067…13.jpg` | #2 · similarity 0.93 | **Imported** |
| thumbnail | `Bernie_Sanders_2016_065…11.jpg` | #3 · similarity 0.91 | Local |
| thumbnail | `Bernie_Sanders_2016_063…1.jpg` | #4 · similarity 0.89 | Local |
| thumbnail | `Bernie_Sanders_2016_074…2.jpg` | #5 · similarity 0.86 | Local |

- **Local** rows have a preview thumbnail (file is on disk) and show the local filename
- **Imported** rows show *Not available* for preview (you do not have the file); filename shown if the exporter included it, otherwise Content ID only
- Both local and imported hits are ranked together by score

### Scoring modes

| Mode | Compares | When to use |
|------|----------|-------------|
| `combined` | 60% CLIP + 40% PDQ | Default |
| `semantic` | Scene content (CLIP) | Different angles, same subject |
| `pdq` | Pixel structure | Near-duplicates only; one series per folder |

### Anonymization

Every search automatically creates **both** plain and private (anonymized) embeddings — there is no toggle.

- **Plain embeddings** — computed from the original image; used for local matching
- **Private embeddings** — faces, people, text, signs, and logos are blacked out before embedding; used for export and for matching against imported data

**Test:** `src-tauri/demo/image-similarity/inputs/`, query `Bernie_Sanders_2016_068_*`, scoring **combined** or **semantic**.

## Option 2: Export Private Embeddings (`/export_embeddings`)

Exports all your **private (anonymized) embeddings** to a `.json` file you can share with another organization. The exported file does not contain original images or full file paths.

- **Organization** (required) — your organization, so importers know who to contact
- **Contact email** (required) — stored on every exported record
- **Share filename** (default Yes) — include the original filename (basename only) in each record; set to No to omit it

Each search creates private embeddings automatically. Export writes one record per indexed image:

```json
{
  "content_sha256": "abc123…",
  "embedding": [0.1, 0.2, …],
  "pdq_hash": "def456…",
  "user_email": "agent@agency.gov",
  "organization": "Agency A",
  "privacy_protocol": "clipseg-blackout-v1:face,logo,person,sign,text",
  "model_name": "google/siglip2-so400m-patch14-384",
  "filename": "photo.jpg"
}
```

| Field | Always present | Description |
|-------|---------------|-------------|
| `content_sha256` | Yes | SHA-256 hash of file bytes — used as Content ID |
| `embedding` | Yes | Anonymized embedding vector |
| `pdq_hash` | Yes | Perceptual hash |
| `user_email` | Yes | Contact email from export form |
| `organization` | Yes | Organization name from export form |
| `privacy_protocol` | Yes | Anonymization method used |
| `model_name` | Yes | Vision encoder |
| `filename` | Only if **Share filename = Yes** | Basename of the original file; omitted when the toggle is off or the row is a re-exported import |

## Option 3: Import Private Embeddings (`/import_embeddings`)

Loads an exported `.json` into your database. Each record stores the same fields described in the export table above, plus `path = "[imported]"` (no local file).

- **Embeddings file (.json)** — select the file received from another organization

After import, every search ranks your local images **and** the imported embeddings together. Imported records that score high enough appear as **Imported** rows in results.

Duplicates are skipped automatically (matched by content hash + protocol + model + owner email).

Import result:

```
Imported 7 embeddings (0 skipped)
```

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
