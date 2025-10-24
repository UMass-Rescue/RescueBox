#!/bin/sh

# this script runs on your laptop, its the only script that run on laptop
# all the other scripts are run insider the container.
# its purpose is to download files from google drive for rescuebox that is too large to checkin.

git checkout https://github.com/UMass-Rescue/RescueBox.git -b hackathon-plugins

cd RescueBox

# download models to run existing rescuebox 2.1.0 plugins
  # https://drive.google.com/file/d/1mHdI2jYt1LFQzt5VMB5x1A9_plFWZTbF/view?usp=sharing

gdown 1mHdI2jYt1LFQzt5VMB5x1A9_plFWZTbF

unzip rescuebox_models.zip -d .

# example : RescueBox/src/deepfake-detection/deepfake_detection/onnx_models should contain 2 onnx models


# download demo files and docs
 # https://drive.google.com/file/d/1mCZyKGgK0ZjPxG3h2vWet0RQxaMxrTfB/view?usp=drive_link
  # gdown 1mCZyKGgK0ZjPxG3h2vWet0RQxaMxrTfB

# download videos for hackathon
 # 1q27_mH22k6PXDhHhPWR8KSby3HSlQ6uQ

gdown 1q27_mH22k6PXDhHhPWR8KSby3HSlQ6uQ
unzip rb_videos.zip -d .

# follow the videos to run the models