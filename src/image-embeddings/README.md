# Image Embeddings Plugin

This plugin generates image embeddings using OpenAI's CLIP (Contrastive Language-Image Pre-Training) models and provides cross-modal text-to-image search capabilities.

## Features

### 1. Image Embedding Generation (`/embed_images`)
- Process all images in a directory
- Support for multiple image formats (JPG, PNG, BMP, GIF, TIFF, WebP)
- Two CLIP model options:
  - `openai/clip-vit-base-patch32` (Base model, 512-dim, faster)
  - `openai/clip-vit-large-patch14` (Large model, 768-dim, more accurate)
- Returns normalized embeddings for each image as JSON
- Automatic storage in PostgreSQL with pgvector

### 2. Text-to-Image Search (`/search_images`)
- **Cross-modal search**: Use text queries to find similar images
- Fast similarity search using pgvector's optimized cosine distance
- Returns top-k most similar images
- Configurable result count (1-20)
- Uses CLIP's text encoder to bridge text and image modalities

## Usage

### Embedding Images

**CLI:**
```bash
rescuebox image_embeddings /embed_images /path/to/images "openai/clip-vit-base-patch32"
```

**Parameters:**
- Directory path with image files
- Model name (default: openai/clip-vit-base-patch32)

**Output:**
```json
{
  "/path/to/image1.jpg": [0.123, 0.456, ...],
  "/path/to/image2.png": [0.789, 0.012, ...]
}
```

### Searching Images with Text

**CLI:**
```bash
rescuebox image_embeddings /search_images "a cat sitting on a couch" "openai/clip-vit-base-patch32,5"
```

**Parameters:**
- Query text (natural language description)
- Model name (must match embedding model, default: openai/clip-vit-base-patch32)
- Top K results (default: 5)

**Output:**
```json
{
  "query": "a cat sitting on a couch",
  "model": "openai/clip-vit-base-patch32",
  "top_k": 5,
  "results": [
    {
      "id": 42,
      "path": "/images/cat_couch_1.jpg",
      "similarity": 0.8932
    },
    {
      "id": 89,
      "path": "/images/cat_furniture.png",
      "similarity": 0.8654
    },
    {
      "id": 156,
      "path": "/images/pet_sofa.jpg",
      "similarity": 0.8421
    }
  ]
}
```

## How It Works

### Image Embedding Generation
1. Scans directory for image files
2. Loads and converts each image to RGB
3. Processes through CLIP's image encoder
4. Normalizes the embedding vector
5. Stores in PostgreSQL with pgvector for efficient similarity search

### Cross-Modal Text-to-Image Search
1. **Text Encoding**: Encodes query text using CLIP's text encoder
2. **Normalization**: Normalizes text embedding (same as image embeddings)
3. **Vector Search**: Uses pgvector's `<=>` operator for cosine distance
4. **Cross-Modal Matching**: Finds images whose embeddings are closest to the text embedding
5. **Returns Results**: Top-k most similar images with similarity scores

### Why CLIP Enables Text-to-Image Search

CLIP is uniquely designed for cross-modal search:
- **Shared Embedding Space**: Text and image embeddings live in the same vector space
- **Contrastive Training**: Trained to align matching text-image pairs
- **Zero-Shot**: Works on arbitrary text queries without fine-tuning
- **Semantic Understanding**: Captures high-level semantic meaning, not just keywords

## Performance Optimization

### pgvector Integration
```sql
SELECT path, 1 - (embedding <=> text_query_embedding) as similarity
FROM image_embeddings
ORDER BY embedding <=> text_query_embedding
LIMIT k
```

**Benefits:**
- ✅ **Fast**: Index-accelerated vector search
- ✅ **Scalable**: Handles millions of images efficiently
- ✅ **Cross-modal**: Same infrastructure for text and image queries
- ✅ **Memory efficient**: Optimized C implementation

### Indexing
For better performance with large image collections:
```sql
CREATE INDEX ON image_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

## Model Information

### CLIP ViT-B/32
- **Embedding dimension**: 512
- **Image encoder**: Vision Transformer Base with 32×32 patches
- **Text encoder**: Transformer with 63M parameters
- **Speed**: Faster inference
- **Use case**: General purpose, production deployments

### CLIP ViT-L/14
- **Embedding dimension**: 768
- **Image encoder**: Vision Transformer Large with 14×14 patches
- **Text encoder**: Transformer with 123M parameters
- **Speed**: Slower inference
- **Use case**: Higher accuracy needed, research

## Dependencies

- `transformers`: Hugging Face Transformers for CLIP
- `torch`: PyTorch for model inference
- `pillow`: Image processing library
- `sqlmodel`: Database ORM
- `pgvector`: PostgreSQL vector extension
- `sqlalchemy`: Raw SQL queries for optimization

## Database Schema

```sql
CREATE TABLE image_embeddings (
    id SERIAL PRIMARY KEY,
    path VARCHAR NOT NULL,
    embedding VECTOR(512) NOT NULL  -- 512 for base, 768 for large
);

CREATE INDEX ON image_embeddings (path);
CREATE INDEX ON image_embeddings USING ivfflat (embedding vector_cosine_ops);
```

## Example Use Cases

### 1. Content-Based Image Search
```bash
# Find images of specific objects or scenes
rescuebox image_embeddings /search_images "sunset over mountains" "openai/clip-vit-base-patch32,10"
```

### 2. Semantic Image Discovery
```bash
# Find images matching abstract concepts
rescuebox image_embeddings /search_images "happiness and joy" "openai/clip-vit-base-patch32,5"
```

### 3. Visual Forensics
```bash
# Search for images with specific characteristics
rescuebox image_embeddings /search_images "outdoor crime scene at night" "openai/clip-vit-base-patch32,20"
```

### 4. Dataset Exploration
```bash
# Find similar images without manual tagging
rescuebox image_embeddings /search_images "person wearing blue jacket" "openai/clip-vit-base-patch32,15"
```

## Tips for Best Results

1. **Model Consistency**: Always use the same CLIP model for embedding and search
2. **Descriptive Queries**: Use natural language descriptions, not just keywords
   - ✅ Good: "a red car parked in front of a house"
   - ❌ Less effective: "car red house"
3. **Specificity**: More specific queries generally yield better results
4. **Context Matters**: Include relevant context in your query
5. **Top-K Selection**: Start with 10-20 results for exploration, narrow down as needed
6. **Normalization**: Both text and image embeddings are automatically normalized

## Comparison with Text Embeddings

| Feature | Text Embeddings | Image Embeddings |
|---------|----------------|------------------|
| Input | Text files | Image files |
| Query Type | Text → Text | **Text → Image** |
| Model | SentenceTransformer | CLIP |
| Embedding Dim | 384/768 | 512/768 |
| Search Type | Semantic text search | Cross-modal visual search |

## Example Workflow

```bash
# 1. Embed all images in a directory
rescuebox image_embeddings /embed_images ./crime_scene_photos "openai/clip-vit-base-patch32"

# 2. Search for relevant images using natural language
rescuebox image_embeddings /search_images "damaged vehicle front view" "openai/clip-vit-base-patch32,10"

# 3. Results show most similar images with similarity scores
# 4. Can refine query based on results
rescuebox image_embeddings /search_images "vehicle with broken windshield" "openai/clip-vit-base-patch32,5"
```

## Advanced: Multi-Modal Search Pipeline

Combine text and image embeddings for comprehensive forensic analysis:

```bash
# Search documents
rescuebox text_embeddings /search_text "vehicle collision report" "all-MiniLM-L6-v2,5"

# Search images
rescuebox image_embeddings /search_images "car accident aftermath" "openai/clip-vit-base-patch32,5"

# Results can be correlated for comprehensive case analysis
```
