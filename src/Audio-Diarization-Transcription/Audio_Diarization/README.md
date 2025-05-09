# Audio-Diarization

  

Speaker Diarization – Identifying and separating speakers in an audio file, transcribing the speech with timestamps and speaker labels.

  

This process aids child rescue efforts by distinguishing victim and abuser voices, providing crucial evidence for court proceedings.

  

## Installation

  

1.  **Clone the Repository**:

  

```bash

git clone https://github.com/UMass-Rescue/Audio-Diarization.git

cd Audio-Diarization

```

  

2.  **Install Dependencies:**

  

For the best results create a virtaul environment. You can use any method to create a virtual environment!

  

One of the ways to create a virtual environment is listed below

  

```bash

python -m venv <virtual_env_name>

```

  

Activate the virtual environment

```bash

source <virtual_env_name>/bin/activate

```

  

Install the required Python packages using the following command:

  

```bash

pip install -r requirements.txt

```

3.  **Access the model**

```bash

huggingface-cli login

```

You will be prompted to enter the access token which you can find: https://huggingface.co/settings/tokens

<img  width="937"  alt="diarization_accesstoken"  src="https://github.com/user-attachments/assets/5e766cd7-45ef-4b2b-8d80-cc608d86e77c"  />

  
(Incase there are issues with the token, you can contact us and one of us will provide it to you!)


4.  **Running the Flask-ML Server**

Start the Flask-ML server to work with RescueBox for predictions:

  

```bash

python transcribe_diarize_app.py

```

The server will start running on 127.0.0.1 5000

  

5.  **Download and run RescueBox Desktop from the following link: [Rescue Box Desktop](https://github.com/UMass-Rescue/RescueBox-Desktop/releases)**

  

Open the RescueBox Desktop application and register the model

<img  width="495"  alt="diarization_register"  src="https://github.com/user-attachments/assets/b223ff7b-e941-44d1-a6e8-7c95a46487a3"  />

  

Run the model

Set the Input and Output directory.

<img  width="749"  alt="diarization_directory"  src="https://github.com/user-attachments/assets/5cbb8304-59de-49b7-9fc6-78eb7a5e7e16"  />

  
  

Input directory should have an audio file and an output directory where the json file with the predictions will be outputted.

Results will be displayed

![image](https://github.com/user-attachments/assets/da0dc54d-b929-4ef0-b808-bfa10e9a87c4)

First make sure ffmpeg is installed on your system, if you don't already have it

### For MacOS  

If you already have homebrew you can use the command listed below to directly install ffmpeg. If not you can follow the [documentation](https://docs.brew.sh/Installation) to install homebrew and then use the command listed below.

```bash

brew  install  ffmpeg

```


### For Windows

Use this [link to install the ffmpeg executable](https://www.ffmpeg.org/download.html#build-windows). Click on the windows icon and use the windows build from gyan.dev

Follow the installation instructions mentioned in the installer

Add ffmpeg to the environment variables to make to accessible globally

  
  
### Running the Diarization and Transcription Model

Once you have ffmpeg installed on your system, make sure you open a new terminal for the changes to be reflected!

Now you can simply run the model.py file using the following command

```bash

python  model.py

```

The output will look something like this
<img width="813" alt="image" src="https://github.com/user-attachments/assets/57cb1b36-2174-4208-a50d-dce3099d7e5a" />
