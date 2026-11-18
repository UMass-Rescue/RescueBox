# Image Matching

Finds matches for images across investigations. It has two tasks:

| Task | Tool | Status |
|---|---|---|
| **Ingestion** | Image Ingestion | Implemented |
| **Query** | Image Match | Not yet implemented |

## Ingestion

Hashes a folder of images and stores the results in the shared archive database. Each distinct file is stored once in the `files` table; every ingestion is an **archive** that lists its files.

| Subtask | Use |
|---|---|
| **Ingest Images** | Hash a folder into a new archive |
| **Delete Archive** | Remove an archive by investigation label |
| **Rename Archive** | Change an archive's investigation label |

### Ingest Images

- **Folder of images:** the images to ingest, in common formats (JPEG, PNG, BMP, WebP).
- **Investigation label:** names the archive. Defaults to the folder name. Must be unique.
- **Description:** case details, survivor information.
- **SHA256** is always computed and identifies each file.
- **MD5** (default on): fast exact matching.
- **PDQ** (default on): perceptual hash that enables deduplication.
- **Semantic hash** (default on): moderately fast to slow; fuzzy matching. Private hashes (faces, tattoos and text blacked out) are created at the same time.
- **Essay hash** (default on): slow; a short paragraph (at most **Max essay words**, default 60, and 350 characters) describing the people, objects and scene, with personal information removed, for fuzzy matching. Essay hashes will be sent to the UMass Safe Matching service; this is not yet being done, and essays are currently stored locally only.

- **Max essay words** (default 60): word limit for new essays. Suggested max 60; more words make essays slower.

Work already done for a file in an earlier archive is reused, so only missing hashes are computed. A stored essay is kept even if Max essay words changes; to regenerate it, delete the archive with **Retain hashes** No and ingest again.

MD5 and PDQ run on any computer. The essay hash downloads the `qwen3-vl:4b-instruct` model (about 3 GB) the first time it is used and needs several GB of memory; a GPU makes semantic and essay hashes much faster.

### Delete Archive

An archive's contents cannot be changed after ingestion, but it can be deleted by investigation label. **Retain hashes** keeps the stored hashes in the database, which makes loading faster if the original data is loaded again. Choosing **No** also removes hashes no other archive uses.

### Rename Archive

Changes the investigation label of an existing archive. The label must stay unique.

## Query

Not yet implemented. Will search your archives for an image by SHA256, MD5, PDQ and semantic hashes, and compare its essay with other agencies' essays through the UMass Safe Matching service.
