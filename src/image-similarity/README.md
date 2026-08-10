# Image Similarity Plugin

Finds images from the **same series** as a query image.

**Series:** A collection of images related **temporally** and by **subject matter**. Photos from a birthday party are a series. Photos of the same person at different times and places are **not**. See [UMass-Rescue/image-series-dataset](https://github.com/UMass-Rescue/image-series-dataset).

## When It Works

1. **Same series** — query with a full photo, get back other photos from the same event/scene.
2. **Specific subject** — crop the query image to one subject (a person, an object), get back images of that subject.

## Better with a Text Query?

If you're looking for a concept like "people eating" rather than a specific scene, use the **Image Search** plugin with a text description instead. This plugin works best when the query image clearly represents what you're looking for — a single event, a single subject, or a cropped subject of interest.

## Installation

```bash
poetry install
```

Download the ONNX models into `onnx_models/`:

**SigLIP2** (~1.7 GB) — vision encoder for embeddings:

```bash
mkdir -p src/image-similarity/image_similarity/onnx_models
curl -L -o src/image-similarity/image_similarity/onnx_models/siglip2-so400m-patch14-384.onnx \
  https://huggingface.co/onnx-community/siglip2-so400m-patch14-384-ONNX/resolve/main/onnx/vision_model.onnx
```

**CLIPSeg** (~545 MB) — detects and blacks out faces, people, text, signs, and logos for privacy. Download `onnx/model.onnx` from [Xenova/clipseg-rd64-refined](https://huggingface.co/Xenova/clipseg-rd64-refined) and save as `clipseg-rd64-refined.onnx`.

## Usage

```bash
rescuebox image_series_similarity /search_series "/path/to/photos|||/path/to/query.jpg" ",5,0.5,combined"
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `user_email` | *(empty)* | Contact email — identifies who ingested the embeddings for cross-agency sharing |
| `model_name` | `google/siglip2-so400m-patch14-384` | Vision encoder |
| `top_k` | 5 | Results to return (1–20) |
| `min_similarity` | 0.5 | Match threshold (0–1) |
| `scoring_mode` | `combined` | `combined`, `semantic`, or `pdq` |

**Scoring modes:** `combined` = 60% CLIP + 40% PDQ (default). `semantic` = CLIP cosine similarity only. `pdq` = PDQ perceptual hash only (near-duplicate detection).

### About PDQ (Perceptual Hashing)

Perceptual hashing identifies images that look the same or similar despite minor changes such as resizing, compression, cropping, or slight color and brightness adjustments. It compares how an image looks, including the arrangement of visual patterns, rather than what the image contains. As a result, images that look similar may match even if they contain different subjects, while images of the same subject may not match if they have different viewpoints, scales, or layouts.

**Examples:**

- **Potential match:** A photo of a red apple and a photo of a red tomato placed in the same position on the same white table and taken from the same angle may produce similar hashes because the overall appearance and arrangement of visual patterns are similar.
- **Potential non-match:** Two photos of the same car, where one is a close-up of the headlight and the other shows the entire vehicle, may produce different hashes because the images have different framing and visual layouts.

**Note:** When using `pdq` scoring mode, the input folder should contain images from only one series (e.g., only Bernie Sanders rally photos or only Kamala Harris event photos). Mixing multiple series will produce confusing results since PDQ matches visual structure, not semantic content.

## Privacy-Preserving Dual Ingestion

Every image gets **two** sets of data stored during ingestion — one **plain** and one **private** (anonymized).

### Step-by-Step Breakdown

**Ingestion (runs once per image):**

1. **Load image** — read `photo.jpg` from disk
2. **Plain path** — embed raw pixels → store embedding + PDQ hash
3. **Anonymize** — use CLIPSeg to black out faces, people, text, signs, and logos
   - Labels are fixed — all five are always applied, users cannot select individual labels
   - CLIPSeg finds where each label appears and blacks out those regions; layout and background remain
4. **Private path** — embed the anonymized image → store embedding + PDQ hash

Result: one image → two database rows (plain + private).

**Query (runs each search):**

1. **Load query image**
2. **Check anonymization toggle:**
   - OFF → use plain embedding/PDQ for query image, compare against plain directory embeddings
   - ON → anonymize query image, use private embedding/PDQ, compare against private directory embeddings
3. **Score matches** using selected mode (`combined`, `semantic`, or `pdq`)
4. **Return top-k** results above threshold

### Example: Rally Photo

Imagine ingesting `Bernie_Sanders_2016_063.jpg` showing Bernie at a podium with crowd and campaign signs.

| Step | Plain | Private |
|------|-------|---------|
| Input | Raw photo | Same photo with faces, "Bernie 2016" signs blacked out |
| Embedding | Encodes: Bernie's face, crowd, signs, colors | Encodes: podium shape, stage layout, blacked regions |
| PDQ Hash | Hash of raw visual patterns | Hash of anonymized visual patterns |
| Stored as | `privacy_protocol = ""` | `privacy_protocol = "clipseg-blackout-v1"` |

**Querying with `Bernie_Sanders_2016_001.jpg`:**

- **Anonymization OFF:** Query image's raw embedding compared against plain embeddings → finds Bernie rally photos by matching his face, crowd, signs
- **Anonymization ON:** Query image is anonymized first, then compared against private embeddings → finds rally photos by matching stage layout, podium shape, crowd density (no faces encoded)

### Simple Example: Anonymization ON

Query image has a **person** and a **logo**.

1. CLIPSeg detects person and logo in query image → blacks them out
2. Blacked-out query image is embedded
3. Compare against directory's private embeddings (already blacked out during ingestion)
4. Return top-k matches based on remaining visual content (background, objects, layout)

Both query image and directory images are processed the same way — private embeddings always compare blacked-out to blacked-out.

### Why Two Embeddings?

- **Plain** — maximum accuracy for local use where privacy isn't a concern
- **Private** — safe for cross-agency sharing; never encodes raw faces, text, or identifying content

Cross-agency comparison only works between embeddings of the same type (both plain or both private).

## Benchmarks

503 images, [image-series-dataset](https://github.com/UMass-Rescue/image-series-dataset), NVIDIA RTX 5090.

| Metric | Value |
|--------|-------|
| top-1 accuracy | 93% |
| top-5 accuracy | 98% |
| top-10 accuracy | 99% |
| Throughput | 14.1 img/s |
| Peak VRAM | 11.78 GB |

## Demo & Testing

`src-tauri/demo/image-similarity/inputs/` — 85 images, 5 series:

| Series | Event | Count |
|--------|-------|-------|
| `Bernie_Sanders_2016_*` | 2016 campaign rally | 26 |
| `Fumio_Kishida_2024_*` | 2024 Noto earthquake visit | 15 |
| `Kamala_Harris_2024_*` | 2024 campaign event | 10 |
| `Marine_Le_Pen_2017_*` | 2017 Lille rally | 5 |
| `Naftali_Bennett_2021_*` | 2021 U.S. Embassy Jerusalem | 29 |

**Correct:** Query image `Bernie_Sanders_2016_063_*` → results are other `Bernie_Sanders_2016_*` images.
**Incorrect:** Results are `Kamala_Harris_2024_*` — different person, different event.

### How to Test

```bash
# 1. Setup
cd src/image-similarity && poetry install
# Download ONNX models (see Installation section)

# 2. Run similarity search (plain embeddings)
rescuebox image_series_similarity /search_series \
  "src-tauri/demo/image-similarity/inputs/|||src-tauri/demo/image-similarity/inputs/Bernie_Sanders_2016_063.jpg" \
  ",5,0.5,combined"

# 3. Run with anonymization ON
# Blacks out faces, people, text, signs, and logos before comparing
```

## Unit Tests

```bash
poetry run pytest src/image-similarity/tests
```

No ONNX file needed for unit tests. End-to-end requires the model.

## Dependencies

`transformers`, `onnxruntime`, `pdqhash`, `pillow`, `numpy`, `sqlmodel`, `sqlalchemy`, `pgvector`