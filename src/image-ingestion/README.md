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
| Essay | `gemma3:4b` through Ollama, redacted with Presidio (`rb-safe-matching-common`) |

## Dependencies

PostgreSQL with pgvector, the `image-similarity` ONNX models, and Ollama for the essay hash. Sending essays to UMass requires the Safe Match intermediary service.
