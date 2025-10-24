# Text Embeddings Plugin

This plugin generates text embeddings using SentenceTransformer models and provides semantic search capabilities using pgvector.

## Features

### 1. Text Embedding Generation (`/embed_text`)
- Process all text files in a directory
- Support for multiple file formats (TXT, MD, LOG)
- Configurable chunking strategies:
  - **LangChain** RecursiveCharacterTextSplitter
  - **LlamaIndex** SentenceSplitter
- Multiple SentenceTransformer models:
  - `all-MiniLM-L6-v2` (384-dim, fast)
  - `all-mpnet-base-v2` (768-dim, high quality)
  - `multi-qa-MiniLM-L6-cos-v1` (384-dim, optimized for Q&A)
- Automatic storage in PostgreSQL with pgvector

### 2. Semantic Search (`/search_text`)
- Fast similarity search using pgvector's optimized cosine distance
- Returns top-k most similar text chunks
- Configurable result count (1-20)
- Uses the same model as embedding generation

## Usage

### Embedding Text Files

**CLI:**
```bash
rescuebox text_embeddings /embed_text /path/to/texts "all-MiniLM-L6-v2,langchain,800,100"
```

**Parameters:**
- Directory path with text files
- Model name (default: all-MiniLM-L6-v2)
- Chunker (default: langchain)
- Chunk size (default: 800)
- Chunk overlap (default: 100)

**Output:**
```json
{
  "/path/to/file1.txt": [0.123, 0.456, ...],
  "/path/to/file2.md": [0.789, 0.012, ...]
}
```

### Searching Text

**CLI:**
```bash
rescuebox text_embeddings /search_text "your search query" "all-MiniLM-L6-v2,5"
```

**Parameters:**
- Query text
- Model name (must match embedding model, default: all-MiniLM-L6-v2)
- Top K results (default: 5)

**Output:**
```json
{
  "query": "your search query",
  "model": "all-MiniLM-L6-v2",
  "top_k": 5,
  "results": [
    {
      "id": 123,
      "path": "/path/to/relevant/file.txt",
      "similarity": 0.8543
    },
    {
      "id": 456,
      "path": "/path/to/another/file.md",
      "similarity": 0.7821
    }
  ]
}
```

## How It Works

### Embedding Generation
1. Scans directory for text files
2. Reads and chunks each file
3. Generates embeddings for each chunk using SentenceTransformer
4. Averages chunk embeddings to create file-level embedding
5. Stores in PostgreSQL with pgvector for efficient similarity search

### Semantic Search
1. Encodes query text using the same model
2. Uses pgvector's `<=>` operator for optimized cosine distance
3. Returns top-k most similar embeddings
4. Calculates similarity score (1 - cosine_distance)

## Performance Optimization

### pgvector Integration
The search endpoint uses pgvector's native vector operations:
```sql
SELECT path, 1 - (embedding <=> query) as similarity
FROM text_embeddings
ORDER BY embedding <=> query
LIMIT k
```

**Benefits:**
- ✅ **Fast**: Index-accelerated vector search
- ✅ **Scalable**: Handles millions of embeddings efficiently
- ✅ **Accurate**: Uses proper cosine distance calculation
- ✅ **Memory efficient**: Optimized C implementation

### Indexing
For better performance with large datasets, create an IVFFlat index:
```sql
CREATE INDEX ON text_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

## Model Information

### all-MiniLM-L6-v2
- **Dimensions**: 384
- **Speed**: Fast
- **Use case**: General purpose, production deployments
- **Performance**: 68.06 on SBERT benchmark

### all-mpnet-base-v2
- **Dimensions**: 768
- **Speed**: Medium
- **Use case**: High-quality embeddings
- **Performance**: 69.57 on SBERT benchmark

### multi-qa-MiniLM-L6-cos-v1
- **Dimensions**: 384
- **Speed**: Fast
- **Use case**: Question-answering, information retrieval
- **Performance**: Optimized for asymmetric semantic search

## Dependencies

- `sentence-transformers`: Embedding generation
- `langchain-text-splitters`: Text chunking
- `sqlmodel`: Database ORM
- `pgvector`: PostgreSQL vector extension
- `sqlalchemy`: Raw SQL queries for optimization

## Database Schema

```sql
CREATE TABLE text_embeddings (
    id SERIAL PRIMARY KEY,
    path VARCHAR NOT NULL,
    embedding VECTOR(384) NOT NULL
);

CREATE INDEX ON text_embeddings (path);
CREATE INDEX ON text_embeddings USING ivfflat (embedding vector_cosine_ops);
```

## Tips for Best Results

1. **Model Consistency**: Always use the same model for embedding and search
2. **Chunking**: Adjust chunk size based on your text length:
   - Short texts (tweets, titles): 200-400
   - Medium texts (paragraphs): 500-800
   - Long texts (articles): 800-1200
3. **Overlap**: Use 10-15% of chunk size for better context continuity
4. **Normalization**: Embeddings are automatically normalized for cosine similarity
5. **Top-K**: Start with 5-10 results and adjust based on recall needs

## Example Workflow

```bash
# 1. Embed a directory of documents
rescuebox text_embeddings /embed_text ./documents "all-MiniLM-L6-v2,langchain,800,100"

# 2. Search for relevant documents
rescuebox text_embeddings /search_text "machine learning algorithms" "all-MiniLM-L6-v2,10"

# 3. Results show most similar documents with similarity scores
```
