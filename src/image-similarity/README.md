# Image Similarity Plugin

**Three tasks:**

| Task | What it does |
|------|--------------|
| **Find series matches** | Search for similar images in a folder |
| **Export private embeddings** | Save anonymized data to share with other agencies |
| **Import private embeddings** | Load data received from another agency |

Finds images from the **same series** as a query image.

**Series:** A collection of images related **temporally** and by **subject matter**. Photos from a birthday party are a series. Photos of the same person at different times and places are **not**.

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
| `top_k` | 5 | How many results to show (1–20). Default is 5. |
| `min_similarity` | 0.5 | Minimum score (0–1) for a result to count as a "match" in metadata. Lower = more results, higher = stricter. |
| `scoring_mode` | `combined` | How to compare images — see Scoring Modes below |

## Scoring Modes

| Mode | What it compares | When to use |
|------|------------------|-------------|
| `combined` | Weighted score: 60% CLIP + 40% PDQ | **Default — use for most searches** |
| `semantic` | Scene content only (CLIP) | When images look different but show the same subject (e.g., different angles) |
| `pdq` | Visual structure only (perceptual hash) | Only for near-duplicates — resized, compressed, or lightly edited copies |

### About PDQ (Perceptual Hashing)

Perceptual hashing identifies images that look the same or similar despite minor changes such as resizing, compression, cropping, or slight color and brightness adjustments. It compares how an image looks, including the arrangement of visual patterns, rather than what the image contains. As a result, images that look similar may match even if they contain different subjects, while images of the same subject may not match if they have different viewpoints, scales, or layouts.

**Examples:**

- **Potential match:** A photo of a red apple and a photo of a red tomato placed in the same position on the same white table and taken from the same angle may produce similar hashes because the overall appearance and arrangement of visual patterns are similar.
- **Potential non-match:** Two photos of the same car, where one is a close-up of the headlight and the other shows the entire vehicle, may produce different hashes because the images have different framing and visual layouts.

**Note:** When using `pdq` scoring mode, the input folder should contain images from only one series (e.g., only Bernie Sanders rally photos or only Kamala Harris event photos). Mixing multiple series will produce confusing results since PDQ matches visual structure, not semantic content.

## Privacy-Preserving Mode

### Anonymization OFF (default)

1. Select a folder of images and a query image
2. Run the search
3. Get similar images based on everything visible in the photos

### Anonymization ON

1. Select a folder of images and a query image
2. Toggle **Anonymization ON**
3. Run the search
4. Faces, people, text, signs, and logos are blacked out in all images before comparing (these labels are fixed and cannot be changed)
5. Get similar images based on background, layout, and remaining objects — without matching on faces or identifying content

Use this mode when you want to find similar scenes without relying on who is in the photo or what text/logos appear.

### Test Anonymization

- Folder: `src-tauri/demo/image-similarity/inputs/`
- Query image: `Bernie_Sanders_2016_068_Bernie Sanders by DW Nance 14.jpg`
- Create anonymized embeddings: **Yes**
- Scoring mode: **combined** or **semantic** (anonymization works best with these modes, not PDQ-only)
- Expected: Other `Bernie_Sanders_2016_*` images returned as matches

### Example

**Query image:** A photo with a person wearing a company logo shirt, standing in front of a building.

**Anonymization ON:** The person and the logo are blacked out in the query image. The same blackout is also applied to all images in the folder being searched. The search then finds similar images based on the building, background, and layout — not based on who the person is or what logo appears.

**Result:** Other photos of the same building or similar scenes are returned, regardless of who is in them.

## Sharing With Other Agencies

Share anonymized embeddings with other agencies **without sharing the actual images**.

| Shared | NOT Shared |
|--------|------------|
| Anonymized embedding | Original images |
| Owner email | File paths |

### Export

```bash
rescuebox image_series_similarity /export_embeddings "/path/to/output/" ""
```

### Import

```bash
rescuebox image_series_similarity /import_embeddings "/path/to/file.json" "your@email.com"
```

### Workflow

1. Run search with anonymization ON
2. Export to `.json` file
3. Send to partner agency
4. Partner imports and searches — matches show your email

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