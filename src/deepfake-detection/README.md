# DeepFake Image Classifier ONNX model
This repo demonstrates an example of how to run ONNX models. This example is aimed to help guide students in the first assignment in the Spring offering of 596E. Further improves can be made, especially when it comes to removing unnecessary dependencies (but this isn't a requirement in the first assignment).

This example uses a deep fake model that was originally created by students in the Fall 2024 offering of 596E. The model has been modified to work with ONNX models. The model is used to classify images as either real or fake.

## Steps to export the ONNX model

Exporting the ONNX model involved the following key steps:
1. Clone and set up the DeepFake repo found [here](https://github.com/aravadikesh/DeepFakeDetector/). Follow instructions on README.md to get the deep fake model running.
2. Configure [Rescue Box Desktop](https://github.com/UMass-Rescue/RescueBox-Desktop/releases) to work with the DeepFake repo. To test that the application works, send an example request where the input is the "images" folder from this (deepfake-image-onnx) repo. Once you get the deep fake model working, proceed to the next step.
3. Set a breakpoint at Line 95, right before the `output = net(image)` call in the `predict` function in `model_server.py` by adding the following line: `import pdb; pdb.set_trace()`.
4. Send a request to the Deepfake backend again using the same inputs from the RescueBox Desktop application. The breakpoint will be triggered in the backend.
5. Run the following python code to export the ONNX model.
```
torch.onnx.export(net, image, "deepfake_model.onnx", export_params=True, opset_version=16, do_constant_folding=True, input_names=["input"], output_names=["output"], dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}})
```

The resulting ONNX model will be saved as "deepfake_model.onnx" in the directory where the `model_server.py` exists.

## Steps to use the deep fake model

### Create virtual environment and install dependencies
Create a new virtual environment using any tool you prefer. I use `pipenv` for this example. You can use `conda` or `virtualenv` as well.

```bash
pipenv shell
```

Install the dependencies using the following command:

```bash
pip install -r requirements.txt
```

### Download the ONNX models
1. Download the ONNX models:  [DeepFake Models Google Drive](https://drive.google.com/drive/folders/14UJap0G5YkdQoXCbjclhrv5gxswtuDit?usp=drive_link).
2. In the root, create a directory named `onnx_models` and place the downloaded ONNX models into into it.
3. To test if it works, follow the steps for either running the Flask-ML server or the CLI. If there are any problems with Numpy, for example, `RuntimeError: Numpy is not available`, consider downgrading to a 1.X version of Numpy with the following commands:

```bash
pip uninstall numpy
pip install "numpy<2"
```

### Run the Flask-ML server

Run the following command to start the Flask-ML server:

```bash
python model_server_onnx.py
```

### Command line interface

The command line interface can be used to test the model. Run the following command to test the model:

```bash
# image_dir is the directory containing the images
python eval.py --dataset_path path/to/image_dir --models all
```

Run the following command to get more information:
```bash
python eval.py -h
```

### Download and run RescueBox Desktop from the following link: [Rescue Box Desktop](https://github.com/UMass-Rescue/RescueBox-Desktop/releases)

#### Open the RescueBox Desktop application and register the model
![RescueBox Desktop](images/register_model.png)

#### Run the model
![RescueBox Desktop](images/run_model.png)
![RescueBox Desktop](images/select_inputs.png)

#### View the results
![RescueBox Desktop](images/view_results.png)

#### Datasets
Here are links to the datasets we considered:

- [DDFD](https://cvlab.cse.msu.edu/dffd-dataset.html)
- [DeepfakeMNIST](https://github.com/huangjiadidi/DeepFakeMnist)
- [CIFAKE (Not humans)](https://www.kaggle.com/datasets/birdy654/cifake-real-and-ai-generated-synthetic-images)
- [DeepFakeFace](https://github.com/OpenRL-Lab/DeepFakeFace)

### Attribution
The deepfake model project was done by students in the Fall 24 offering of 596E. Their work has been modified to work with ONNX models here. Their repo can be found [here](https://github.com/aravadikesh/DeepFakeDetector/).

The model we're using was originally created by the authors of the following paper:

```bibtex
@InProceedings{Lanzino_2024_CVPR,
    author    = {Lanzino, Romeo and Fontana, Federico and Diko, Anxhelo and Marini, Marco Raoul and Cinque, Luigi},
    title     = {Faster Than Lies: Real-time Deepfake Detection using Binary Neural Networks},
    booktitle = {Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR) Workshops},
    month     = {June},
    year      = {2024},
    pages     = {3771-3780}
}
