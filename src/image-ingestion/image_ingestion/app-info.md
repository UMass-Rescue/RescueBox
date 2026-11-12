# Image Ingestion

Hashes a folder of images and stores the results in the shared archive database. Each distinct file is stored once in the `files` table; every ingestion is an **archive** that lists its files.

## Tasks

| Task | Use |
|---|---|
| **Ingest Images** | Hash a folder into a new archive |
| **Delete Archive** | Remove an archive by investigation label |
| **Rename Archive** | Change an archive's investigation label |

## Ingest Images

- **Folder of images:** the images to ingest (`.jpg`, `.jpeg`, `.png`, `.bmp`, `.gif`, `.tiff`, `.webp`).
- **Investigation label:** names the archive. Defaults to the folder name. Must be unique.
- **Description:** case details, survivor information.
- **SHA256** is always computed and identifies each file.
- **MD5** (default on): fast exact matching.
- **PDQ** (default on): perceptual hash that enables deduplication.
- **Semantic hash** (default on): moderately fast to slow; fuzzy matching. Private hashes (faces, tattoos and text blacked out) are created at the same time.
- **Essay hash** (default on): slow; a short text description with personal information removed, for fuzzy matching against the UMass Safe Semantic Matching Service. When selected, essay hashes are automatically sent to UMass. Your admin needs to configure access.

Work already done for a file in an earlier archive is reused, so only missing hashes are computed.

MD5 and PDQ run on any computer. The essay hash downloads the `qwen3-vl:4b-instruct` model (about 3 GB) the first time it is used and needs several GB of memory; a GPU makes semantic and essay hashes much faster.

## Delete Archive

An archive's contents cannot be changed after ingestion, but it can be deleted by investigation label. **Retain hashes** keeps the stored hashes in the database, which makes loading faster if the original data is loaded again. Choosing **No** also removes hashes no other archive uses.

## Rename Archive

Changes the investigation label of an existing archive. The label must stay unique.
