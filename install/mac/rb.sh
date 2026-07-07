#!/usr/bin/env zsh

# check if brew exists
if command -v brew >/dev/null 2>&1; then
    echo "Homebrew is already installed. Updating package lists..."
    brew update
else
# 1. Install and Update Homebrew
	/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
	brew update
fi
# 2. Install Core Dependencies
brew install git
brew install pipx
pipx ensurepath
pipx install poetry
pipx ensurepath
source ~/.zshrc

# 3. Install Python 3.13 and Setup Alias
echo "Checking current Python version..."

# Check if python3 is installed, and extract the version (e.g., "3.11")
PY_VERSION="none"
if command -v python3 >/dev/null 2>&1; then
    PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")') 
fi

# Determine whether to install 3.13
if [[ "$PY_VERSION" == "3.12" || "$PY_VERSION" == "3.14" ]]; then
    echo "Python $PY_VERSION detected. Skipping Python 3.13 installation."
else
    echo "Python $PY_VERSION detected. Installing Python 3.13 via Homebrew..."
    brew install python@3.13
fi

echo 'alias python="python3"' >> ~/.zshrc
source ~/.zshrc
python -V

# 4. Install Ollama and OrbStack

if command -v docker &> /dev/null; then
    echo "Docker is already installed. Skipping OrbStack installation."
else
    echo "Bypassing Homebrew to avoid macOS security blocks..."

	# 1. Download the direct macOS DMG
	curl -L -o orbstack.dmg "https://orbstack.dev/download/mac"

	# 2. Mount the disk image silently
	echo "Mounting disk image..."
	hdiutil attach orbstack.dmg -nobrowse -quiet

	# 3. Copy the application directly to the system folder
	echo "Copying to Applications..."
	cp -R /Volumes/OrbStack/OrbStack.app /Applications/

	# 4. Unmount and clean up
	echo "Cleaning up..."
	hdiutil detach /Volumes/OrbStack -quiet
	rm orbstack.dmg

	# 5. Boot the engine silently (bypassing the UI)
	echo "Initializing OrbStack engine silently..."
	/Applications/OrbStack.app/Contents/MacOS/bin/orbctl start

	# 6. Wait for the Docker CLI tools to link (with a 30s failsafe)
	echo "Waiting for Docker tools to link..."
	timeout=30
	elapsed=0

	until command -v docker compose &> /dev/null; do
		if [ "$elapsed" -ge "$timeout" ]; then
			echo "Error: Timed out waiting for Docker Compose."
			exit 1
		fi
		sleep 1
		((elapsed++))
	done

	echo "Success! OrbStack is running and Docker is ready."
fi



# 5. Pull Local AI Models
brew install ollama
# 2. Start the Ollama background engine as a macOS service
echo "Starting Ollama server..."
brew services start ollama

# 3. Dynamically wait for the API to wake up and accept connections
echo "Waiting for Ollama to become ready..."
until curl -s http://localhost:11434/api/tags > /dev/null; do
    sleep 1
done
echo "Ollama is online!"
ollama pull ibm/granite4.1:3b
ollama pull moondream:latest
ollama pull gemma3:1b

# 6. Clone rescuebox repository and navigate
git clone https://github.com/UMass-Rescue/RescueBox.git
cd RescueBox

# 7. Install onnx models
brew install gdown
# get rb_3.1_onnx_models.zip
gdown --continue 1HSFbCLAO6Ap4K1NPZc8PoMrCtybapTGl
unzip -q -o rb_3.1_onnx_models.zip
rm -f rb_3.1_onnx_models.zip

# whisper model
gdown --continue "1bIf66wFc-joTBwPgjW9UJvHBN4R8b6Tm"
unzip ./models--Systran--faster-whisper-base.zip
mkdir -p ~/.cache/huggingface/hub
mv models--Systran--faster-whisper-base ~/.cache/huggingface/hub
rm -f ./models--Systran--faster-whisper-base.zip
		  
brew install ffmpeg
# 8. Copy FFmpeg Binary to Current Directory
cp "$(brew --prefix ffmpeg)/bin/ffmpeg" .

# 9. Install Python Setup Tools
brew install python-setuptools

# 10. Install python dependencies
poetry Install

# 11. Run Database Startup Scripts
# Using bash to execute them directly in case they lack execution permissions
bash startup/pgvector_start.sh
# bash startup/check_pgvector_db.sh

# 12. Start the rescuebox Application
#poetry run python -m rb.api.main &
#sleep 30
#poetry run python frontend/main.py &

echo "Install rescuebox completed ok !"

echo "run ./start_rb.sh in terminal to start RescueBox"
echo " open browser and enter http://localhost:8080 to use RescueBox"

# save script to a file  , set permissions and run it
# chmod +x rb.sh
#./rb.sh 2>&1 | tee rb.log