# Image Embeddings Plugin

This plugin generates image embeddings using OpenAI's CLIP (Contrastive Language-Image Pre-Training) models.

## Features

- Process all images in a directory
- Support for multiple image formats (JPG, PNG, BMP, GIF, TIFF, WebP)
- Two CLIP model options:
  - `openai/clip-vit-base-patch32` (Base model, faster)
  - `openai/clip-vit-large-patch14` (Large model, more accurate)
- Returns normalized embeddings for each image as JSON

## Usage

### CLI

```bash
rescuebox image_embeddings /embed_images /path/to/images "openai/clip-vit-base-patch32"
```

### Output Format

The plugin returns a JSON object mapping file paths to their embedding vectors:

```json
{
  "/path/to/image1.jpg": [0.123, 0.456, ...],
  "/path/to/image2.png": [0.789, 0.012, ...]
}
```

## Dependencies

- `transformers`: Hugging Face Transformers library
- `torch`: PyTorch for model inference
- `pillow`: Image processing library

## How It Works

1. Scans the input directory for image files
2. Loads the selected CLIP model
3. For each image:
   - Opens and converts to RGB
   - Processes through CLIP's image encoder
   - Normalizes the embedding vector
4. Returns all embeddings as JSON

## Model Information

### CLIP ViT-B/32
- Embedding dimension: 512
- Faster inference
- Good for general use cases

### CLIP ViT-L/14
- Embedding dimension: 768
- Higher accuracy
- Slower inference
