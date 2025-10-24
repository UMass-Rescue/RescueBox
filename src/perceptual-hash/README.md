# Perceptual Hash Plugin

A forensic investigation plugin for detecting duplicate and near-duplicate images using perceptual hashing algorithms. This plugin enables large-scale image similarity detection using PostgreSQL with the pgvector extension for efficient vector-based similarity search.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [How It Works](#how-it-works)
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
  - [1. PostgreSQL Installation](#1-postgresql-installation)
  - [2. pgvector Extension](#2-pgvector-extension)
  - [3. Database Setup](#3-database-setup)
  - [4. Environment Variables](#4-environment-variables)
- [Usage](#usage)
  - [CLI Usage](#cli-usage)
  - [Web UI Usage](#web-ui-usage)
- [Supported Hash Algorithms](#supported-hash-algorithms)
- [Understanding Results](#understanding-results)
- [Demo and Testing](#demo-and-testing)
- [Architecture](#architecture)
- [Troubleshooting](#troubleshooting)
- [Performance Considerations](#performance-considerations)

---

## Overview

The Perceptual Hash plugin is designed for forensic investigators who need to:
- Detect duplicate and near-duplicate images in large datasets
- Find modified versions of images (cropped, resized, filtered, etc.)
- Build searchable databases of known image content
- Perform similarity searches across image collections

Unlike cryptographic hashes (MD5, SHA), perceptual hashes are robust to image transformations, making them ideal for forensic scenarios where images may be modified to evade detection.

## Features

- **6 Endpoint Operations**:
  1. Create Hash Database - Index a directory of images
  2. Find Matches - Search for similar images
  3. Export Database - Export hashes to JSON
  4. Import Database - Import hashes from JSON
  5. List Collections - View all collections
  6. Delete Collection - Remove a collection

- **5 Hash Algorithms**:
  - pHash (Perceptual Hash) - Recommended for general use
  - Average Hash - Fast, good for exact matches
  - dHash (Difference Hash) - Robust to brightness changes
  - Wavelet Hash - Good for complex transformations
  - PDQ Hash - Facebook's production-grade algorithm

- **PostgreSQL + pgvector Backend**:
  - Scalable vector similarity search
  - Hamming distance-based matching
  - Efficient indexing for large datasets
  - Support for multiple collections

## How It Works

### 1. Hash Generation

The plugin uses the [perception](https://github.com/thorn-oss/perception) library to compute perceptual hashes:

```
Image → Perceptual Hash Algorithm → Binary Vector (64-256 dimensions)
```

Each algorithm converts an image into a fixed-length binary vector that captures visual features:
- **pHash**: Uses Discrete Cosine Transform (DCT) to capture frequency patterns
- **Average Hash**: Compares pixels to average brightness
- **dHash**: Captures gradients between adjacent pixels
- **Wavelet Hash**: Uses Haar wavelet decomposition
- **PDQ**: Facebook's robust hash optimized for scale

### 2. Storage in PostgreSQL

Hashes are stored as vectors in PostgreSQL using the pgvector extension:

```sql
CREATE TABLE collection_algorithm (
    id SERIAL PRIMARY KEY,
    file_path TEXT NOT NULL,
    hash_string TEXT NOT NULL,
    hash_vector vector(64) NOT NULL,  -- Binary vector representation
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(file_path)
);
```

### 3. Similarity Search

When searching for matches, the plugin uses **Hamming distance** (L1 distance for binary vectors):

```sql
SELECT file_path, hash_string,
       hash_vector <+> query_vector AS hamming_distance
FROM collection_algorithm
WHERE hash_vector <+> query_vector <= threshold
ORDER BY hamming_distance
LIMIT n_results;
```

**Hamming distance** counts the number of differing bits:
- Distance 0 = Identical images
- Distance 1-5 = Near-identical (extremely similar)
- Distance 6-15 = Very similar (likely same content)
- Distance 16-30 = Similar (related content)
- Distance > 30 = Potentially different images

### 4. Match Quality Scoring

Results include:
- **hamming_distance**: Number of differing bits (lower = more similar)
- **similarity**: Normalized score from 0.0 (different) to 1.0 (identical)
- **quality**: Human-readable label (exact, very_similar, similar, somewhat_similar)

---

## Prerequisites

Before using the Perceptual Hash plugin, you need:

1. **PostgreSQL** (version 12 or higher)
2. **pgvector extension** for PostgreSQL
3. **Python 3.11+** with Poetry
4. **RescueBox** development environment

---

## Setup Instructions

### 1. PostgreSQL Installation

#### macOS (using Homebrew)

```bash
# Install PostgreSQL
brew install postgresql@15

# Start PostgreSQL service
brew services start postgresql@15

# Verify installation
psql --version
```

#### Linux (Ubuntu/Debian)

```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Verify installation
psql --version
```

#### Docker (Alternative)

```bash
# Run PostgreSQL in Docker
docker run -d \
  --name rescuebox-postgres \
  -e POSTGRES_PASSWORD=test \
  -e POSTGRES_USER=test \
  -e POSTGRES_DB=rescuebox \
  -p 5432:5432 \
  postgres:15
```

### 2. pgvector Extension

pgvector must be compiled and installed from source:

```bash
# Clone pgvector repository
cd /tmp
git clone https://github.com/pgvector/pgvector.git
cd pgvector

# Compile and install (requires PostgreSQL development headers)
# macOS:
brew install postgresql@15  # Includes dev headers

# Linux:
sudo apt install postgresql-server-dev-15

# Compile
make
sudo make install

# Verify installation
cd /Users/aravadikesh/Documents/GitHub/RescueBox
ls -la pgvector/  # Should see vector.so and other files
```

The RescueBox repository includes a pre-built `vector.so` in the `pgvector/` directory for convenience.

### 3. Database Setup

#### Create Database and User

```bash
# Connect to PostgreSQL as superuser
psql postgres

# Create user and database
CREATE USER test WITH PASSWORD 'test';
CREATE DATABASE rescuebox OWNER test;

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE rescuebox TO test;

# Exit psql
\q
```

#### Enable pgvector Extension

```bash
# Connect to the rescuebox database
psql -U test -d rescuebox

# Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

# Verify installation
SELECT extversion FROM pg_extension WHERE extname = 'vector';

# You should see output like:
#  extversion
# ------------
#  0.7.4
# (1 row)

# Exit psql
\q
```

#### Test Connection

```bash
# Test connection with environment variables
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=test
export POSTGRES_PASSWORD=test
export POSTGRES_DB=rescuebox

# Test query
psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
  -c "SELECT extversion FROM pg_extension WHERE extname = 'vector';"
```

If successful, you should see the pgvector version number.

### 4. Environment Variables

The plugin uses environment variables for database configuration. Add these to your shell configuration file (`~/.bashrc`, `~/.zshrc`, or `.env`):

```bash
# PostgreSQL Configuration
export POSTGRES_HOST=localhost          # Database host
export POSTGRES_PORT=5432               # Database port
export POSTGRES_USER=test               # Database user
export POSTGRES_PASSWORD=test           # Database password
export POSTGRES_DB=rescuebox            # Database name

# Optional: Enable testing mode (uses separate rescuebox_test database)
# export IS_TESTING=true
```

**For persistent configuration**, add to your shell profile:

```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'export POSTGRES_HOST=localhost' >> ~/.bashrc
echo 'export POSTGRES_PORT=5432' >> ~/.bashrc
echo 'export POSTGRES_USER=test' >> ~/.bashrc
echo 'export POSTGRES_PASSWORD=test' >> ~/.bashrc
echo 'export POSTGRES_DB=rescuebox' >> ~/.bashrc

# Reload shell configuration
source ~/.bashrc
```

**For VS Code Dev Container**, add to [.devcontainer/devcontainer.json](../../.devcontainer/devcontainer.json):

```json
{
  "containerEnv": {
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "POSTGRES_USER": "test",
    "POSTGRES_PASSWORD": "test",
    "POSTGRES_DB": "rescuebox"
  }
}
```

---

## Usage

### CLI Usage

The plugin provides 6 endpoints accessible via CLI:

#### 1. Create Hash Database

Index a directory of images to create a searchable collection:

```bash
poetry run rescuebox perceptual-hash/create_database \
  /path/to/images \
  --params "my_collection,phash,true"

# Parameters format: collection_name,hash_algorithm,recursive
# - collection_name: Name for this collection (e.g., "evidence_photos")
# - hash_algorithm: phash|average|dhash|wavelet|pdq
# - recursive: true|false (search subdirectories)
```

**Example:**

```bash
# Index all images in a directory recursively
poetry run rescuebox perceptual-hash/create_database \
  src/perceptual-hash/demo/original_images \
  --params "evidence_set1,phash,true"

# Output:
# Successfully created collection 'evidence_set1' with 150 hashes using phash algorithm.
# Total hashes in collection: 150
```

#### 2. Find Matches

Search for similar images in a collection:

```bash
poetry run rescuebox perceptual-hash/find_matches \
  /path/to/query_images,output.json \
  --params "my_collection,phash,10.0,10"

# Parameters format: collection_name,hash_algorithm,max_distance,max_results
# - collection_name: Collection to search in
# - hash_algorithm: Must match the collection's algorithm
# - max_distance: Maximum Hamming distance threshold (0-100)
# - max_results: Max results per query (1-100)
```

**Example:**

```bash
# Find similar images with Hamming distance <= 10
poetry run rescuebox perceptual-hash/find_matches \
  src/perceptual-hash/demo/query_images,matches.json \
  --params "evidence_set1,phash,10.0,10"

# Output:
# Successfully found 8 matches for 3 query files. Results saved to matches.json
```

**Output JSON format:**

```json
{
  "metadata": {
    "collection_name": "evidence_set1",
    "hash_algorithm": "phash",
    "max_distance": 10.0,
    "max_results_per_query": 10,
    "total_query_files": 3,
    "total_matches_found": 8
  },
  "results": {
    "/path/to/query1.jpg": {
      "matches": [
        {
          "file_path": "/path/to/original1.jpg",
          "hamming_distance": 0,
          "similarity": 1.0,
          "quality": "exact"
        },
        {
          "file_path": "/path/to/original2.jpg",
          "hamming_distance": 5,
          "similarity": 0.921875,
          "quality": "very_similar"
        }
      ],
      "total_matches": 2
    }
  }
}
```

#### 3. Export Database

Export a collection to a portable JSON file:

```bash
poetry run rescuebox perceptual-hash/export_database \
  export.json \
  --params "my_collection,phash"

# Parameters format: collection_name,hash_algorithm
```

**Example:**

```bash
poetry run rescuebox perceptual-hash/export_database \
  evidence_set1_backup.json \
  --params "evidence_set1,phash"

# Output:
# Successfully exported collection 'evidence_set1' (phash) with 150 hashes to evidence_set1_backup.json
```

#### 4. Import Database

Import a collection from JSON:

```bash
poetry run rescuebox perceptual-hash/import_database \
  export.json \
  --params "new_collection_name"

# Parameters: new_collection_name (optional - uses original name if empty)
```

**Example:**

```bash
# Import with new name
poetry run rescuebox perceptual-hash/import_database \
  evidence_set1_backup.json \
  --params "evidence_set1_restored"

# Import with original name
poetry run rescuebox perceptual-hash/import_database \
  evidence_set1_backup.json \
  --params ""
```

#### 5. List Collections

View all available collections:

```bash
poetry run rescuebox perceptual-hash/list_collections ""

# Output:
# Available Collections:
#
# evidence_set1:
#   - phash: 150 hashes (dimension: 64)
#   - pdq: 150 hashes (dimension: 256)
#
# evidence_set2:
#   - average: 85 hashes (dimension: 64)
```

#### 6. Delete Collection

Remove a collection:

```bash
poetry run rescuebox perceptual-hash/delete_collection \
  "" \
  --params "my_collection,phash"

# Parameters format: collection_name,hash_algorithm
```

**Example:**

```bash
poetry run rescuebox perceptual-hash/delete_collection \
  "" \
  --params "evidence_set1,phash"

# Output:
# Successfully deleted collection 'evidence_set1' (phash)
```

### Web UI Usage

The plugin is also accessible via the RescueBox AutoUI:

1. **Start the backend server:**

```bash
cd /Users/aravadikesh/Documents/GitHub/RescueBox
./run_server

# Or manually:
poetry run python -m src.rb-api.rb.api.main
```

2. **Access the web interface:**

Open your browser to [http://localhost:8000](http://localhost:8000)

3. **Select "Perceptual Hash" from the plugin list**

4. **Use the dynamically generated UI:**
   - **Create Database**: Upload or select a directory, choose algorithm and collection name
   - **Find Matches**: Select query directory, choose collection and search parameters
   - **Export/Import**: Manage collection backups
   - **List/Delete**: View and manage collections

The UI automatically validates inputs and provides real-time feedback.

---

## Supported Hash Algorithms

### 1. pHash (Perceptual Hash) - **Recommended**

```bash
--params "collection,phash,true"
```

- **Method**: Discrete Cosine Transform (DCT)
- **Dimensions**: 64 bits
- **Best for**: General-purpose similarity detection
- **Robust to**: Scaling, aspect ratio changes, minor compression, brightness/contrast adjustments
- **Use cases**: Finding modified images, duplicate detection, general forensic work

### 2. Average Hash

```bash
--params "collection,average,true"
```

- **Method**: Compare pixels to average brightness
- **Dimensions**: 64 bits
- **Best for**: Fast exact duplicate detection
- **Robust to**: Minor compression, small color changes
- **Use cases**: Quick deduplication, nearly-identical image detection

### 3. dHash (Difference Hash)

```bash
--params "collection,dhash,true"
```

- **Method**: Gradient-based (differences between adjacent pixels)
- **Dimensions**: 64 bits
- **Best for**: Images with different brightness/contrast
- **Robust to**: Brightness changes, contrast adjustments, gamma correction
- **Use cases**: Finding images with exposure/lighting differences

### 4. Wavelet Hash

```bash
--params "collection,wavelet,true"
```

- **Method**: Haar wavelet decomposition
- **Dimensions**: 64 bits
- **Best for**: Complex image transformations
- **Robust to**: Rotation, complex filtering, artistic modifications
- **Use cases**: Finding heavily modified images

### 5. PDQ Hash

```bash
--params "collection,pdq,true"
```

- **Method**: Facebook's production-grade hash (DCT-based with quality improvements)
- **Dimensions**: 256 bits
- **Best for**: Large-scale production deployments
- **Robust to**: All common transformations, optimized for CSAM detection
- **Use cases**: Large datasets, law enforcement applications, high-accuracy requirements

---

## Understanding Results

### Hamming Distance Interpretation

The Hamming distance indicates how many bits differ between two hashes:

| Distance | Quality | Interpretation | Example Scenarios |
|----------|---------|----------------|-------------------|
| 0 | Exact | Identical images | Exact duplicate, same file |
| 1-5 | Very Similar | Near-identical | Resized, re-compressed, watermarked |
| 6-15 | Similar | Likely same content | Cropped, filtered, color-adjusted |
| 16-30 | Somewhat Similar | Related content | Different angles, partial matches |
| 31+ | Different | Likely unrelated | Different images |

### Similarity Score

The similarity score is normalized: `similarity = 1.0 - (hamming_distance / vector_dimension)`

- **1.0** = Perfect match (0 bits different)
- **0.9-0.99** = Near-identical (1-6 bits different for 64-bit hash)
- **0.75-0.89** = Very similar (7-16 bits different)
- **0.5-0.74** = Somewhat similar (17-32 bits different)
- **< 0.5** = Likely different images

### Setting Thresholds

**For high precision (fewer false positives):**
```bash
--params "collection,phash,5.0,10"  # Very strict
```

**For high recall (catch more matches):**
```bash
--params "collection,phash,20.0,50"  # More permissive
```

**Recommended thresholds by use case:**

- **Exact duplicates**: max_distance = 5
- **Near-duplicates** (resized, compressed): max_distance = 10
- **Modified images** (cropped, filtered): max_distance = 15-20
- **Related content** (same scene, different angle): max_distance = 25-30
