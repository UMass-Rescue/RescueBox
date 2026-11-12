# Image Ingestion Plugin

Hashes a folder of images into the shared archive database. Each ingestion creates an **archive** named by an investigation label; each distinct image is stored once and reused across archives. See [`app-info.md`](image_ingestion/app-info.md) for the user-facing description.

## Features

| Route | Purpose |
|---|---|
| `/ingest_images` | Hash a folder of images into a new archive |
| `/delete_archive` | Delete an archive by label; optionally keep its hashes |
| `/rename_archive` | Change an archive's label |

## Usage

`/ingest_images` parameters:

| Parameter | Description |
|---|---|
| Folder of images | `.jpg`, `.jpeg`, `.png`, `.bmp`, `.gif`, `.tiff`, `.webp` |
| Investigation label | Unique; defaults to the folder name |
| Description | Case details |
| MD5, PDQ, Semantic, Essay | Each default on. SHA-256 is always computed |

## How It Works

1. Each image is hashed with SHA-256 and looked up in the database.
2. Only the selected hashes that are missing for that image are computed.
3. Every path is linked to the archive.

| Hash | Source |
|---|---|
| SHA-256, MD5 | `hashers.py` |
| PDQ, semantic, private | `image-similarity` (SigLIP2 and CLIPSeg ONNX models) |
| Essay | `qwen3-vl:4b-instruct` through Ollama, redacted with Presidio (`rb-safe-matching-common`) |

## Dependencies

PostgreSQL with pgvector, the `image-similarity` ONNX models, and Ollama for the essay hash. Essays will be sent to the UMass Semantic Matching API through the Safe Match intermediary service; this is not yet being done.

MD5 and PDQ run on CPU with no extra downloads. The essay hash is the heavy option:

- `qwen3-vl:4b-instruct` is pulled through Ollama on first use (about 3 GB download, several GB of RAM while running; a GPU helps).
- Presidio uses the spaCy `en_core_web_lg` model (about 600 MB wheel, installed with `rb-safe-matching-common`).

## Testing

Unit tests need no database or models:

```bash
poetry run pytest src/image-ingestion/tests
```

The smoke test exercises the happy path against a running backend. Start the backend in one terminal, then run the script from the repository root in another:

```bash
./run_backend_server
./src/image-ingestion/smoke_test.sh
```

It ingests the 3-image demo folder `src-tauri/demo/image-ingestion/series_0013_Alexandria_Ocasio-Cortez_2019` with MD5 and PDQ only (no model downloads), checks that a duplicate label is rejected, renames the archive, deletes it, and checks that deleting it again reports "Archive not found". Each request is printed as a `curl` command so it can be rerun by hand. A passing run ends with `PASS: ingest, duplicate label, rename, delete` and exits 0; the first unexpected response prints `FAIL` and exits nonzero. Each run uses a timestamped label and deletes its own archive. Set `RESCUEBOX_API` to target a backend other than `http://127.0.0.1:8000`.
