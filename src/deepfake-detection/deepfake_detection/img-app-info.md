# Image Deepfake Detector

## Overview
This application is a machine learning-powered deepfake detection tool that analyzes image files to determine whether they contain manipulated/generated (fake) or real content. It uses a ML architecture using a binary NN backbone to perform image classification. For evaluation metrics, scroll to the end.

## Key Components
1. **Server for Image Classifier (`model_server.py`)**: 
   - Creates a Flask-based server to host the Image classifier model
   - Contains code to work with RescueBox client.
   - API can work with path to directory containing images and creates a CSV file containing output.
   - Applies the appropriating pre-processing steps and runs the model on collection of images.

2. **Testing code (`test.py`)**: 
   - Can be used to test datasets. 
   - Assumes all fake data files have "F" in the name and uses this to assige labels.
   - Outputs metrics 

## Setup

### 1. Clone the required repositories and restructure code
Note the BNext repository needs to be cloned into the binary_deepfake_detection one. 
```bash
git clone https://github.com/aravadikesh/DeepFakeDetector.git
git clone https://github.com/fedeloper/binary_deepfake_detection.git
cd .\binary_deepfake_detection\
git clone https://github.com/hpi-xnor/BNext.git

```

Now move the files under `image_model` folder to the binary_deepfake_detection folder, replacing existing files if needed. Your structure should be like (you may have additional files) - 

```
binary_deepfake_detection\
│
├── BNext\                  # ML backbone code
├── pretrained\             # pretrained model ckpts
├── requirements.txt        # Python package dependencies
├── model.py                # code for ML model           
├── model_server.py         # Flask-ML server code   
├── test.py                 # Testing code
├── sim_data.py             # Data reading and preprocessing  
├── img-app-info.md         # Info 
└── client.py               # Flask-ML cli for server
```

### 2. Download weights and checkpoint

- Download the model backbone weights from [here](https://drive.google.com/file/d/1xyKnA6SsG4ZpguNQQrB6Yz-J5dzXYfKE/view), prefix the name with `middle_`, and move them to the `pretrained` folder. You should have `pretrained\middle_checkpoint.pth.tar`. Other backbone weights available [here](https://github.com/hpi-xnor/BNext/tree/main?tab=readme-ov-file).

- Create a `weights\` folder in the main program folder (`binary_deepfake_detection\`). Download the model checkpoint from [here](https://drive.google.com/file/d/16c5xIDvwN3DUD6JbO_cl7aj_xrijezWs/view?usp=drive_link) and place the downloaded file into the weights folder. Other checkpoints (trained on other datasets/using different backbones) can be found [here](https://drive.google.com/drive/folders/1rYtfozcq5eXK1a8tP8ouXrBFZs1e72dV).


### 3. Install Dependencies

`conda` and `pip` required for next steps. We create a new conda env with python 3.12 and install required libs.

```bash
conda create --name img_dfd
conda activate img_dfd
conda install python=3.12
pip install -r requirements.txt
```

### (Optional but recommended) Check and make sure GPU is enabled 

The retinaface model used doesn't support GPU on macOS as of now and I would recommend not using the model on macOS if you plan on using face cropping through retinaface.

If you want to use the GPU, please run the check_cuda.py to make sure CUDA is enabled. If you see CUDA is not available, you may need to reinstall the correct torch. Once you know which CUDA ver is needed for your GPU, you can find the system specific command [here](https://pytorch.org/get-started/locally/) once you select the appropriate options. 

Then run `pip uninstall torch` to uninstall the existing torch and then use the command you copied, which should look something like - `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/<your_cuda_ver>`

Now rerun the check_cuda file to check cuda is ready. 

You can try running the model now, it should process about 10 imgs per second. If it is still slow, the retinaface model may not be running on GPU (especially on windows) and the fix can be found here - https://www.tensorflow.org/install/pip#linux. Run `pip uninstall tensorflow` and follow the steps (for appropriate) system on the website.



## Usage

Now you can run `python model_server.py` and use the RescueBox GUI for interacting with the server. By default, port 5000 will be used. You may change the port used by running `python model_server.py --port <port>` where \<port> is port number you want to use. 
Example usage: `python model_server.py --port 8080` will run the server on port 8080.

The following options are available on the GUI - 

- **Path to the directory containing all the images**: As the name suggests, this is the path to the image directory which you want to classify.

- **Path to output file**: The server will create a csv file with results, this option will specify where the file should be stored.

- **Disable Facecrop**: If you have images which are preprocessed into face crops or are naturally selfie like single face closeups, you can choose `true` to disable the face cropping step.

- **Path to model ckpt**: If you want to use another model checkpoint (link in setup) you may download the relevant checkpoint and backbone weights (similarly to the checkpoint we used) and give the path to the new checkpoints. 

The output will be a csv file where each row is an image, its corresponding prediction and confidence level. The prediction may be `uncertain` if the model can't conclude anything or `error` if opening the image led to an error. `real` and `fake` prediction are predictions by a ML model and may be incorrect. The max confidence level is 1. 

## Evaluation 

I tested the model on 10k test images from the celeba dataset and ~9k fake imgs from the pggan_v2 dataset. Both of these are part of the DFFD dataset. I did the testing using a RTX 4090 GPU (on windows) and it took ~10 mins to classify all the images with face cropping disabled and ~23 mins with face cropping enabled.

### Results

Note: one of the images wasn't being read correctly so I am discarding it.


**Without face cropping**

F1: 0.9997500777

Accuracy: 0.9997500777

Number of images where prediction was uncertain - 11

Confusion matrix -

|      | Pred Real | Pred Fake |
|------|-----------|-----------|
| Real | 10000     | 0         |
| Fake | 5         | 8974      |

**With face cropping**

F1: 0.9985995888

Accuracy: 0.9985246658

Number of images where prediction was uncertain - 20

Confusion matrix -

|      | Pred Real | Pred Fake |
|------|-----------|-----------|
| Real | 9983    | 17         |
| Fake | 11         | 8968     |


Note: The model performs really well when looking at data similar to the training data (deepfakes made by methods included in DFFD). The above metrics show this. It may struggle with novel deepfake generation techniques though, StyleGAN2 is a good example as while testing, I did some testing with images from StyleGAN2 and they fooled the detector.

### How to reproduce the results

First we need to gather and prepare the data - 

- Create a folder called `datasets` (in the binary_deepfake_detection folder) if you don't have one already. Create a subfolder called `dffd` in this folder. 

- I used [CelebA](https://mmlab.ie.cuhk.edu.hk/projects/CelebA.html) dataset for real images. Download the `img_align_celeba.zip` file from [here](https://drive.google.com/drive/folders/0B7EVK8r0v71pTUZsaXdaSnZBZzg?resourcekey=0-rJlzl934LzC-Xp28GeIBzQ) for the real imgs. Extract all the imgs into a `img_align_celeba` folder in the `dffd` folder.

- I used pggan_v2 from the [dffd](https://cvlab.cse.msu.edu/dffd-dataset.html) dataset for fake images. Visit the page and fill the form for the access code, then you can access it using the link provided on the webpage or click [here](https://www.cse.msu.edu/computervision/dffd_dataset/). Download the pggan_v2 from the site and extract all the zip to `pggan_v2` folder in the `dffd` folder. You should have three subfolders titled test,train,validation in `pggan_v2`. Your `datasets` folder should look like - 

```
datasets\
│
├── dffd\               
      ├── img_align_celeba\             # real imgs
      ├── pggan_v2\                     # fake imgs
```

- Now run `test_data_prepare.py` file to extract and copy the test images into a common folder. you should have `datasets/test` now.

- Finally run the `test.py` file to test on these images. It will print out F1, accuracy and other info at the end.

