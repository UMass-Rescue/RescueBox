


#!/bin/sh


git checkout https://github.com/UMass-Rescue/RescueBox.git -b hackathon-main

cd RescueBox

# download models
  # https://drive.google.com/file/d/1mHdI2jYt1LFQzt5VMB5x1A9_plFWZTbF/view?usp=sharing

gdown 1mHdI2jYt1LFQzt5VMB5x1A9_plFWZTbF

unzip rescuebox_models.zip -d .

# RescueBox/src/deepfake-detection/deepfake_detection/onnx_models should contain 2 onnx models


# download demo files and docs
 # https://drive.google.com/file/d/1mCZyKGgK0ZjPxG3h2vWet0RQxaMxrTfB/view?usp=drive_link

gdown 1mCZyKGgK0ZjPxG3h2vWet0RQxaMxrTfB

unzip assets_rb_server.zip -d .

# follow the docs "rescuebox 2.1.0 usage.pdf" to run the models using demo files