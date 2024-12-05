# Video Deepfake Detector

## Overview
This application is a machine learning-powered deepfake detection tool that analyzes video files to determine whether they contain manipulated (fake) or original (real) content. It uses a pre-trained Xception neural network model to classify faces in videos.

## Project Structure
```
video_detector/
│
├── server.py               # Main Flask server implementation
├── video_evaluator.py      # Core video processing and deepfake detection logic
├── requirements.txt        # Python package dependencies
├── network/                # Neural network model definitions
│   └── models.py           
├── dataset/                # Data transformation utilities
│   └── transform.py        
└── app_info.md             # Application documentation
```

## Key Components
1. **VideoEvaluator (`video_evaluator.py`)**: 
   - Handles video processing and deepfake detection
   - Uses dlib for face detection
   - Applies a pre-trained Xception neural network for classification
   - Supports multiple output modes (video annotation, JSON results)

2. **MLServer (`server.py`)**: 
   - Creates a Flask-based server for processing video files
   - Provides a flexible API for deepfake detection
   - Supports batch processing of multiple videos
   - Offers different output formats (video, JSON, verbose JSON)

## Prerequisites
- Python 3.8+
- CUDA-compatible GPU (recommended but optional)
- OpenCV and PyTorch compatible system

## Environment Setup

### 1. Clone the Repository
```bash
git clone https://github.com/aravadikesh/DeepFakeDetector.git
cd video_detector
```

### 2. Create Virtual Environment
```bash
# Using venv
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# OR using conda
conda create -n deepfake-detector python=3.11
conda activate deepfake-detector
```

### 3. Install Additional System Dependencies
Some libraries like dlib require additional system packages:

#### On Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install cmake
sudo apt-get install -y libopenblas-dev liblapack-dev
sudo apt-get install -y libx11-dev libgtk-3-dev
conda install -c conda-forge libstdcxx-ng
```

#### On macOS (with Homebrew)
```bash
brew install cmake
brew install openblas
```

### On Windows

1. **Install CMake**: Download CMake from [https://cmake.org/download/](https://cmake.org/download/). During installation, ensure you check the option to add CMake to your system PATH.

2. **Install Visual Studio Build Tools**: Download and install the Visual Studio Build Tools from [https://visualstudio.microsoft.com/downloads/?q=build+tools#build-tools-for-visual-studio-2022](https://visualstudio.microsoft.com/downloads/?q=build+tools#build-tools-for-visual-studio-2022).

3. **Restart Your System**: After installation, restart your computer to ensure all environment variables are properly configured.

   
### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

## Running the Application

### Development Mode
```bash
# Activate your virtual environment first
python server.py
```

## Usage

### API Endpoints
- `/detect_deepfake`: Primary endpoint for deepfake detection
- Supports batch processing of multiple video files
- Configurable output formats:
  1. `json`: Basic detection results
  2. `json_verbose`: Detailed frame-by-frame analysis
  3. `video`: Annotated video output

### Example Request Parameters
- `video_paths`: List of video file paths to analyze
- `output_directory`: Directory to save results
- `output_format`: Choose between `json`, `json_verbose`, or `video`

## Model Details
- Architecture: Xception Neural Network
- Trained on facial manipulation detection dataset
- Binary classification: Real vs. Fake

## Limitations
- Requires clear, frontal face views
- May struggle with:
  - Heavily obstructed faces
  - Extreme lighting conditions
  - Very low-resolution videos

## Troubleshooting
- Ensure all dependencies are correctly installed
- Check CUDA and GPU drivers if using GPU acceleration
- Verify video file formats (MP4, AVI recommended)


