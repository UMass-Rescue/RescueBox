# Image Summary

Generate detailed descriptions for images using vision-capable LLMs via Ollama.

## Features

- **Batch Processing**: Process entire directories of images at once
- **Multiple Output Formats**: 
  - Plain text descriptions (`.txt`)
  - Structured JSON output (`.json`)
- **Flexible Model Selection**: Choose from multiple vision models based on your hardware capabilities
- **Comprehensive Descriptions**: Captures scene, objects, people, actions, visible text, lighting, and composition
- **Wide Format Support**: Handles `.png`, `.jpg`, `.jpeg`, `.bmp`, `.webp`, and `.tiff` files

## Supported Models

- **Gemma3 4B**: Small, runs on more hardware
- **Llama 3.2 11B**: More performant, fits consumer GPUs
- **Gemma3 27B**: Larger, powerful model
- **Llama 3.2 90B**: Most performant, requires significant VRAM

### Benchmark Results

Processing time per image (in seconds) across different hardware:

| Model        |  5090 | 3090 | 9950X3D | 2600X |
| ------------ | ----: | ---: | ------: | ----: |
| Gemma3 27B   |   6.4 | 11.1 |   142.8 | 269.5 |
| Gemma3 4B    |   2.2 |  4.2 |    36.3 | 117.4 |
| Llama3.2 11B | 109.7 |  6.4 |   533.2 | 367.7 |

**Notes:**
- Llama 3.2 90B could not be tested due to hardware limitations
- Llama 3.2 11B shows inconsistent performance, with some images processing quickly while others take significantly longer
- Gemma3 models demonstrate consistent, predictable performance

## Usage

### API Endpoints

- `/summarize-images` - Generate text descriptions
- `/summarize-images-json` - Generate structured JSON descriptions

### CLI

```bash
image-summary <input_dir>,<output_dir> <model>
```

## Output

For each input image, creates a corresponding file in the output directory:
- Text mode: `{filename}.{ext}.txt`
- JSON mode: `{filename}.{ext}.json`

JSON output includes structured data for scene, setting, objects with attributes, people and actions, visible text, and visual composition details.
