## Audio Transcription

### Installing requirements

1. Install ffmpeg
```
sudo apt update && sudo apt install ffmpeg
```
2. Install poetry with pipx
```
poetry lock ( refer dependencies listed in pyproject.toml)
```
3. Install dependencies
```
poetry install
```

### Starting the server

```
run_server

```

### Client command line example

```
sample file : src\rb-audio-transcription\tests\sample.mp3
cd src\rb-audio-transcription
typer rb_audio_transcription.main run audio/transcribe "C:\\work\\audio\\samples\\sample.mp3" "a:'int', b:'int within range',c: 0 , d: 5 , e:1"


negative test : typer rb_audio_transcription.main run audio/transcribe "sample.mp3" "'e1': 'example', 'e2' : 0.1, 'e3': 1"
ERROR:rb_audio_transcription.main:Invalid full path input for transcribe command: sample.mp3
Aborted.

```

### Command line tool
```
poetry run typer rb_audio_transcription.main --help
```
Transcribe a single file
```
poetry run typer rb_audio_transcription.main run audio/transcribe "sample.mp3"
```
