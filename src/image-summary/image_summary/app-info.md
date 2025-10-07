# Image Summary

This plugin lets you generate rich descriptions for every image in a folder. For each image, it identifies the scene and setting, key objects and their attributes (colors, counts, positions), people and actions (if present), visible text (quoted verbatim), and notable visual details like lighting and composition. Input: a directory of images. Output: a matching directory of .txt files (one per image) containing the description.

## Inputs
- Input directory: A directory containing image files to describe.
- Output directory: A directory where text descriptions will be written. One `.txt` file is produced per input image.
- Model: Choose a supported vision-capable LLM.

## Supported Image Types
- .png, .jpg, .jpeg, .bmp, .webp, .tiff

## Outputs
- For each input image, a corresponding `{original_filename}.{ext}.txt` file is created in the output directory containing the description.

## Notes
- Descriptions are factual and avoid speculation; visible text is quoted verbatim when detected.
- Output files include the original image filename and extension to avoid naming collisions across formats.
