# Image Deepfake Detector

## Overview
This application is a machine learning-powered deepfake detection tool that analyzes image files to determine whether they contain manipulated/generated (fake) or real content. It uses a machine learning architecture with either a binary neural network or vision transformers to perform image classification. For information about evaluation, scroll to the end.

## Key Components
1. **Server for Image Classifier (`main.py`)**: 
   - Creates a server to host the Image classifier model.
   - Contains code to work with the RescueBox client.
   - API can work with a path to a directory containing images and creates a CSV file containing output.
   - Applies the appropriate pre-processing steps and runs the model on a collection of images.

2. Input the **Path to the directory containing all the images". ".jpg", ".jpeg", ".png" are the file types supported
   Path to the output file , select a folder that has sufficient space for the csv file that contains the results.
   Optional choose Face cropping to true.

3   result prediction confidence scores are as follows:

   "likely fake" if confidence < 20%

   "weakly fake" if confidence < 40%
                
   "uncertain"   if confidence < 60%
                     
   "weakly real" if confidence < 80% 
   
   "likely real" if confidence < 100%
               