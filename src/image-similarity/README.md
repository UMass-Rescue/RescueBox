# Image Similarity Plugin

Finds images from the **same series** as a query image.

**Series:** A collection of images related **temporally** and by **subject matter**. Photos from a birthday party are a series. Photos of the same person at different times and places are **not**. See [UMass-Rescue/image-series-dataset](https://github.com/UMass-Rescue/image-series-dataset).

## When It Works

1. **Same series** — query with a full photo, get back other photos from the same event/scene.
2. **Specific subject** — crop the query to one subject (a person, an object), get back images of that subject.

## Better with a Text Query?

If you're looking for a concept like "people eating" rather than a specific scene, use the **Image Search** plugin with a text description instead. This plugin works best when the query image clearly represents what you're looking for — a single event, a single subject, or a cropped subject of interest.

## Installation

```bash
poetry install
```

Download the ONNX model (~1.7 GB):

```bash
mkdir -p src/image-similarity/image_similarity/onnx_models
curl -L -o src/image-similarity/image_similarity/onnx_models/siglip2-so400m-patch14-384.onnx \
  https://huggingface.co/onnx-community/siglip2-so400m-patch14-384-ONNX/resolve/main/onnx/vision_model.onnx
```

## Usage

```bash
rescuebox image_series_similarity /search_series "/path/to/photos|||/path/to/query.jpg" ",5,0.5,combined"
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `model_name` | `google/siglip2-so400m-patch14-384` | Vision encoder |
| `top_k` | 5 | Results to return (1–20) |
| `min_similarity` | 0.5 | Match threshold (0–1) |
| `scoring_mode` | `combined` | `combined`, `semantic`, or `pdq` |

**Scoring modes:** `combined` = CLIP + PDQ (default). `semantic` = CLIP cosine similarity only. `pdq` = PDQ perceptual hash only (near-duplicate detection).

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

**Correct:** Query `Bernie_Sanders_2016_063_*` → results are other `Bernie_Sanders_2016_*` images.
**Incorrect:** Results are `Kamala_Harris_2024_*` — different person, different event.

## Unit Tests

```bash
poetry run pytest src/image-similarity/tests
```

No ONNX file needed for unit tests. End-to-end requires the model.

## Dependencies

`transformers`, `onnxruntime`, `pdqhash`, `pillow`, `numpy`, `sqlmodel`, `sqlalchemy`, `pgvector`
