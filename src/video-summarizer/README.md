# Video-Summarizer

This project provides a machine learning service to summarize videos by extracting frames and generating textual descriptions for each frame. The summaries are generated using the Gemma3 model by Google with Ollama.

## Setup Instructions ##

1. Clone the repository:
```bash
git clone https://github.com/sachint2001/Video-Summarizer.git
cd Video-Summarizer
```

2. Create and activate a virtual environment:
```bash
python -m venv myenv
source myenv/Scripts/activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Download and Install Ollama from https://ollama.com/download.

5. Download and install ffmpeg from https://ffmpeg.org/download.html.

## Project Structure ##

* app.py: Runs a Flask-based ML server that loads the Gemma model and provides an API for summarizing videos in a given directory.

* Results/: Directory containing results.

## Running the model ##

1. Make sure ollama is running first.

2. Run the following command to start the Flask-ML server:

```bash
python app.py
```

You will get the IP address and Port of the server which you can now register with RescueBox to try the model on.

In the RescueBox app, you can mention the fps you would like (how often frames should be extracted) and whether you would like audio content to be included in the summary or not.