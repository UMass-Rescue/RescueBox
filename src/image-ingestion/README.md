# Image Ingestion Plugin

Hashes a folder of images into the shared PostgreSQL database. Each ingestion creates an **archive** named by a unique investigation label. Each distinct image (by SHA-256) is stored once and reused by every archive that contains it, so re-ingesting known images only computes the hashes they are missing. The in-app description is in [`app-info.md`](image_ingestion/app-info.md).

## Tasks

| Task | Route | Purpose |
|---|---|---|
| Ingest Images | `/image_ingestion/ingest_images` | Hash a folder into a new archive |
| Delete Archive | `/image_ingestion/delete_archive` | Delete an archive; optionally keep its hashes for faster re-ingestion |
| Rename Archive | `/image_ingestion/rename_archive` | Change an archive's label |

Ingest Images takes a folder of images in common formats (JPEG, PNG, BMP, WebP), a label (defaults to the folder name), a description, and four hash options that default to Yes. SHA-256 is always computed.

| Hash | Computed by |
|---|---|
| SHA-256, MD5 | `hashers.py` |
| PDQ, semantic, private | `image-similarity` (SigLIP2 and CLIPSeg ONNX models); Semantic also creates the private hash |
| Essay | `qwen3-vl:4b-instruct` through Ollama, redacted with Presidio (`rb-safe-matching-common`) |

The **essay** is one plain paragraph describing people, then key objects, then the scene, kept to whole sentences within 60 words and 350 characters. Essays will be sent to the UMass Semantic Matching API through the Safe Match intermediary; this is not yet done, and essays stay in the local database. For now, each redacted essay is also written to the backend log for testing; this will be removed before upload is enabled.

## Requirements

- PostgreSQL with pgvector, started by `./run_backend_server`.
- MD5 and PDQ: nothing else; they run on CPU.
- Semantic: the `image-similarity` ONNX models.
- Essay: Ollama. `qwen3-vl:4b-instruct` (about 3 GB, several GB of RAM; a GPU helps) is pulled on first use, and Presidio's spaCy model `en_core_web_lg` (about 600 MB) is installed with `rb-safe-matching-common`.

## Demo images

`src-tauri/demo/image-ingestion/` holds three image series (3, 3 and 11 images) from the UMass Rescue [image-series-dataset](https://github.com/UMass-Rescue/image-series-dataset), which groups [Wikimedia Commons](https://commons.wikimedia.org) photographs of political figures into series by event. Each image remains under the license on its Commons file page.

## Try it

Start the backend from the repository root and leave it running:

```bash
./run_backend_server
```

### Smoke test

In a second terminal:

```bash
./src/image-ingestion/smoke_test.sh
```

It ingests `series_0013_Alexandria_Ocasio-Cortez_2019` with MD5 and PDQ only, then checks the duplicate-label error, rename, delete, and the not-found error. Each request is printed as a `curl` command. A passing run ends with `PASS: ingest, duplicate label, rename, delete` and exits 0; otherwise it prints `FAIL` and exits nonzero. It deletes its own archive. Set `RESCUEBOX_API` to use a backend other than `http://127.0.0.1:8000`.

### UI

In a second terminal run `./run_ui_server`, open http://localhost:8080/chatbot, click **Menu**, then **11. Image Ingestion -> Open**.

| Try | Expected result |
|---|---|
| Ingest `series_0013_Alexandria_Ocasio-Cortez_2019`, label blank, Semantic and Essay No | `Archive 'series_0013_Alexandria_Ocasio-Cortez_2019': 3 files.` |
| The same ingest again | "Label already in use" |
| Ingest `series_0014_Alexandria_Ocasio-Cortez_2019` with Essay Yes | `3 files.`; essays appear in the backend log |
| The same folder again with a new label | Finishes quickly; existing hashes are reused |
| Rename `series_0013_Alexandria_Ocasio-Cortez_2019` to `demo-case` | "Archive renamed" |
| Delete `demo-case` with Retain hashes No | "Archive deleted" (3 files) |

Delete any remaining demo archives when done.

## Unit tests

No Postgres, Ollama or ONNX models needed (archive tests use in-memory SQLite):

```bash
poetry run pytest src/image-ingestion/tests src/rb-safe-matching-common
```
