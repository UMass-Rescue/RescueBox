# 🔊 Audio-Diarization

Speaker Diarization is a system that identifies and separates speakers in an audio file, with their respective timestamps and speaker labels. This model is integrated with a Automatic Speech Recognition (ASR) model to transcribe each speaker's audio. This model efficiently inputs a folder with audio files and presents a csv file containing speaker separation with their corresponding time stamps and audio transcription.

  
This process aids child rescue efforts by distinguishing victim and abuser voices, providing crucial evidence for court proceedings and in distinguishing speakers from background noise during criminal investigations

## Initial Setup

1. Install ffmpeg

	First make sure ffmpeg is installed on your system, if you don't already have it

	#### For MacOS  

	If you already have homebrew you can use the command listed below to directly install ffmpeg. If not you can follow the [documentation](https://docs.brew.sh/Installation) to install homebrew and then use the command listed below.

	```bash

	brew  install  ffmpeg

	```


	#### For Windows

	Use this [link to install the ffmpeg executable](https://www.ffmpeg.org/download.html#build-windows). Click on the windows icon and use the windows build from gyan.dev

	Follow the installation instructions mentioned in the installer

	Add ffmpeg to the environment variables to make to accessible globally

2. Virtual Environment

	For the best results create a virtaul environment. You can use any method to create a virtual environment!

	One of the ways to create a virtual environment is listed below

	```bash

	python -m venv <virtual_env_name>

	```

	Activate the virtual environment

	#### For MacOS/Linux run 
	```bash

	source <virtual_env_name>/bin/activate

	```
	#### For Windows run 
	```bash

	cd <virtual_env_name>\Scripts
	.\activate

	```
3. Poetry
	To maintain the dependencies of the repository we use poetry, install poetry if you don't already have it.
	```
	pip install poetry
	```
	To download the dependencies simply run
	```
	poetry install
	```

You are now all done with the basic setup!

## Running the model on the cli

To run the model using the cli, use the following command

```
poetry run python src/Audio-Diarization-Transcription/Audio_Diarization/model_3endpoints.py /Audio_Diarization/diarize "src/Audio-Diarization-Transcription/Audio_Diarization/input src/Audio-Diarization-Transcription/Audio_Diarization/output" " "
```