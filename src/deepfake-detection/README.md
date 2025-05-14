# Deepfake Detection

This project uses pretrained ONNX models to detect deepfakes in images. It supports multiple models for inference, including **BNext_M_ModelONNX**, **BNext_S_ModelONNX**, **TransformerModelONNX**, **TransformerModelDimaONNX**, and **Resnet50ModelONNX**.

Follow the instructions below to run the CLI tool.

### Install dependencies

Run this in the root directory of the project:
```bash
poetry install
```

Activate the environment:
```bash
poetry env activate
```

### Using the CLI

The `deepfake-detection` CLI processes a directory of images and outputs prediction files. Run this in the root directory of the project:
```bash
poetry run deepfake-detection --dataset_path <input_dir> --models [all|BNext_M_ModelONNX,BNext_S_ModelONNX,..] --facecrop [True|False]
```
- `--dataset_path`: Path to the directory containing images to analyze.
- `--models`: Comma-separated list of models to use (default: all).
- `--facecrop`: Enable face cropping before inference (default: false).


### Attribution and License

For attribution and license details of the models and code used in this project, see the `LICENSES` directory.
