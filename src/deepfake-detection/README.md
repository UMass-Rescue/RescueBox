# DeepFake Detection Module

## Overview
This module provides a deepfake detection system capable of analyzing images to determine if they are authentic or AI-generated. The system uses an ONNX-optimized deep learning model originally developed by students in the Fall 2024 offering of 596E, with modifications to support ONNX runtime for improved performance and deployment flexibility. It supports multiple models for inference, including **BNext_M_ModelONNX**, **BNext_S_ModelONNX**, **TransformerModelONNX**, **TransformerModelDimaONNX**, and **Resnet50ModelONNX**.


### Model Details
- Input: RGB images (standardized size)
- Output: Binary classification (Real/Fake) with confidence scores
- Framework: ONNX (deployed)

## Installation

### Install dependencies

Run this in the root directory of the project:
```bash
poetry install
```

Activate the environment:
```bash
poetry env activate
```

### RescueBox
1. Clone RescueBox from [here](https://github.com/UMass-Rescue/RescueBox)
2. Create ```src/deepfake-detection/deepfake_detection/onnx_models```
2. Download the [models](https://drive.google.com/drive/u/2/folders/14UJap0G5YkdQoXCbjclhrv5gxswtuDit) into ```onnx_models```
3. Run ```poetry install``` in the root of the project
4. Run ```./run_server``` in the root of the project 
5. In a separate terminal, navigate to ```RescueBox/RescueBox-Desktop/```.
    -  Run ```npm i```. Make sure to use Node 20 or lower, but not Node 22 (due to issues with binary files)
    -  Run   ```npm run start```
7. Register the models on Rescuebox and begin!


## Model Export Process
To export the original PyTorch model to ONNX format:
- Clone the original DeepFake repository: [DeepFake Detector](https://github.com/aravadikesh/DeepFakeDetector/)
Run the export command:
```python
torch.onnx.export(
    net, 
    image, 
    "deepfake_model.onnx",
    export_params=True,
    opset_version=16,
    do_constant_folding=True,
    input_names=["input"],
    output_names=["output"],
    dynamic_axes={
        "input": {0: "batch_size"},
        "output": {0: "batch_size"}
    }
)
```

## Citations
The model is based on the following model and dataset:

```bibtex
@InProceedings{Lanzino_2024_CVPR,
    author    = {Lanzino, Romeo and Fontana, Federico and Diko, Anxhelo and Marini, Marco Raoul and Cinque, Luigi},
    title     = {Faster Than Lies: Real-time Deepfake Detection using Binary Neural Networks},
    booktitle = {Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR) Workshops},
    month     = {June},
    year      = {2024},
    pages     = {3771-3780}
}
```


## Acknowledgments
- Original model development: Students from Fall 2024 offering of 596E
- Original repository: [DeepFake Detector](https://github.com/aravadikesh/DeepFakeDetector/)
- UMass Rescue team for integration support
