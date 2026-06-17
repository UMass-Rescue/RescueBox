# Text Summarization

Text Summarization uses an LLM to summarize text and PDF files in a directory. For each file, it produces a clear, concise summary that captures the main points, structure, and tone of the original document.

## Inputs

- **Input Directory:** Path to a directory containing text or PDF files to summarize.
- **Output Directory:** Path to a directory where summary files will be written.
- **Model:** Choose a supported LLM (e.g. gemma3:1b, gemma3:4b)
             not currently available : deepseek-r1:1.5b, deepseek-r1:7b, llama3.2:3b.

## Supported File Types

- .txt, .pdf, .md

## Outputs

- **Text Files:** For each input file, a corresponding `{original_filename}.txt` file is created in the output directory containing the summary (e.g. `document.pdf` → `document.txt`).

### Sample Output

```
The document discusses the key principles of machine learning. It outlines the main approaches 
including supervised and unsupervised learning, and explains how models are trained and evaluated. 
The tone is instructional and focused on practical applications.
```

Results can be viewed in the Jobs page.
