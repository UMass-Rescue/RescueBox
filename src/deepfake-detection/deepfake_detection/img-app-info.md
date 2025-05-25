# Image Deepfake Detector

## Overview
This application is a machine learning-powered deepfake detection tool that analyzes image files to determine whether they contain manipulated/generated (fake) or real content. It uses a machine learning architecture with either a binary neural network or vision transformers to perform image classification. For information about evaluation, scroll to the end.

## Key Components
1. **Server for Image Classifier (`main.py`)**: 
   - Creates a Flask-based server to host the Image classifier model.
   - Contains code to work with the RescueBox client.
   - API can work with a path to a directory containing images and creates a CSV file containing output.
   - Applies the appropriate pre-processing steps and runs the model on a collection of images.
<!-- 
2. **Testing Code (`test.py`)**: 
   - Can be used to test datasets. 
   - Assumes all fake data files have "F" in the name and uses this to assign labels.
   - Outputs metrics. -->

---

## Evaluation

### Results Summary
The models were evaluated on both real and fake datasets with face cropping enabled. Below is a summary of their performance:

#### **Real Datasets**
1. **CelebA_Val**:
   - **BNext_M**: Excellent performance with very few misclassifications.
   - **BNext_S**: Strong performance but slightly more uncertain predictions compared to BNext_M.
   - **Transformer**: High accuracy with minimal uncertainty.
   - **TransformerDima**: Reliable but slightly more uncertain predictions.

2. **FFHQ**:
   - **BNext_M**: Perfect accuracy with no misclassifications.
   - **BNext_S**: Strong performance but slightly more uncertain predictions.
   - **Transformer**: High accuracy with minimal uncertainty.
   - **TransformerDima**: Reliable but more prone to uncertainty.

#### **Fake Dataset**
1. **Deepfake_v4**:
   - **BNext_M**: Strong performance with minimal misclassifications.
   - **BNext_S**: Excellent performance with very few misclassifications.
   - **Transformer**: High accuracy with minimal uncertainty.
   - **TransformerDima**: Reliable but slightly more uncertain predictions.

---

**Best Overall Performance**:

**BNext_M** and **TransformerDima** consistently perform well across both real and fake datasets, making them the most reliable choices for general use.

<!-- 2. **Do not use**:
   - **Resnet50** struggles with fake datasets and is not recommended for detecting deepfakes. Under development. -->

---

<!-- ### How to Reproduce the Results

1. **Prepare the Data**:
   - Create a `datasets` folder in the project directory.
   - For real images, use the CelebA and FFHQ datasets.
   - For fake images, use the Deepfake_v4 dataset.

2. **Run the Tests**:
   - Use the `test.py` script to evaluate the models on the datasets.
   - Ensure face cropping is enabled for consistent results.

3. **Analyze the Results**:
   - The output will include metrics such as F1 score, accuracy, and a confusion matrix for each model.

--- -->

### Conclusion
For most use cases, **BNext_M** and **TransformerDima** are the recommended models due to their consistent performance across datasets.