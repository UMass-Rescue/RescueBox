# RescueBox from UMass Rescue Lab


This release has been tested on Windows 11 64-bit hardware. The software does work if you run it on a machine with only a CPU; try it out with a few images or audio files. GPU strongly recommended.

-----------------------
Notes for Developers Only:

**Pre-requisites for windows/macos/Linux ** 

1. python 3.13 , poetry 
      checkout git repo src and run poetry install

2. install **ollama and pull models** ibm/granite4.1:3b, moondream:latest, gemma3:4b , gemma3:1b
	see "startup\ollama_check.sh"

3. **install and run pgvector docker container** on macos/Linux/windows 

	"startup\docker-compose.yml"       
	"startup\pgvector_start.sh"
	"startup\check_pgvector_db.sh"

4. **download and extract onnx models** from :
    	https://umass-my.sharepoint.com/:u:/g/personal/jaikumar_umass_edu/IQAiVKIZKA8QT6EEVDLqmc5NAWuYAy8wl9I3K2Ken5G7lLc?e=w8DjIl
		
    	extract rb_3.1_onnx_models.zip to rescuebox <ROOT> or top level directory ( where "src" folder exists)
        

5. **install ffmpeg.exe** for audio transcribe https://www.osxexperts.net/ffmpeg81arm.zip

6. start **backend server**
     poetry run python -m rb.api.main , confirm by accessing http://localhost:8000

7. start **frontend UI server**
     poetry run python frontend/main.py, confirm by accessing http://localhost:8080


NOTES:

** for macos** poetry toml file are upto date.

**Frontend (NiceGUI) developer docs:** [frontend/docs/README.md](frontend/docs/README.md) — workflow, database, tests, and related topics.

**src-tauri** folder to build windows rescuebox installer. src-tauri\nsis\README.txt for current build notes.

**image-embeddings** converted to onnx model , text embeddings onnx convert pending..
  
on windows : frontend.spec and backend.spec run with pyinstaller to create exe and package with src-tauri build steps.

on linux : run_backend_server and run_ui_server was used to demo nvidia/cuda gpu with dgx-spark server

See the [LICENSE](LICENSE) file for license details.

