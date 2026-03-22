# Image Summary

This plugin lets you generate rich descriptions for every image in a folder. 
For each image, it identifies the scene and setting, 
key objects and their attributes (colors, counts, positions), 
people and actions (if present), 
visible text (quoted verbatim), 
and notable visual details like lighting and composition. 
Input: a directory of images. Output: a matching directory of .txt files (one per image) containing the description.
Note: This plugin must be used with a GPU. it will work very slow with cpu only hardware.

## Inputs

- **Input Directory:** Path to a directory containing image files to describe.
- **Output Directory:** Path to a directory where text descriptions will be written. One `.txt` file is produced per input image.
- **File Filter (Optional):** Filter to specific files from a previous pipeline step.
- **Model:** Choose a supported vision-capable LLM (e.g. Gemma3 4B, Llama 3.2 11B, Gemma3 27B, Llama 3.2 90B).

## Supported Image Types

- .png, .jpg, .jpeg, .bmp, .webp, .tiff

## Outputs

- **Text Files:** For each input image, a corresponding `{original_filename}.txt` file is created in the output directory containing the description. Output files include the original image filename and extension to avoid naming collisions (e.g. `photo.jpg` → `photo.jpg.txt`).

### Sample Output

```
A living room with soft natural light from a large window. A beige sofa faces a wooden coffee table. 
On the table are two white mugs and a green plant. The text "Welcome" is visible on a small sign. 
The composition is centered, with warm afternoon lighting.
```

## Notes
- Descriptions are factual and avoid speculation; visible text is quoted verbatim when detected.
- Output files include the original image filename and extension to avoid naming collisions across formats.
- This plugin requires a GPU for reasonable performance; CPU-only hardware will run very slowly.
