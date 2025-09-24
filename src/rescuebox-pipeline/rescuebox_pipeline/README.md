# RescueBox Pipeline

This directory contains a set of Python scripts that demonstrate how to build and run multi-step AI/ML pipelines using the RescueBox SDK. The pipelines are orchestrated using Celery to manage asynchronous task execution.

## Key Files

-   `rp_pipeline2.py`: A script that demonstrates a 3-step pipeline where the output of one task is passed to the next. The chain is: transcribe -> save_text_to_file -> summarize.
- `rb_pipeline.py`: A script that demonstrates how to start and then cancel a running pipeline. The chain is: transcribe -> summarize
-   `rb_celery.py`: Sets up and configures the Celery application, including the message broker.

-   `rb_client_all.py`: A client script used to initiate and test the rescuebox operations. needed only if you want to create new pipelines.
-   `rescue_box_api_client/`: A directory containing the auto-generated RescueBox API client code for interacting with rescuebox. needed only if client has to be regenerated.
        1.   `sdk_config.yaml`: Configuration file for generating the RescueBox API client
        2.  `run.bat`: A batch script for easily executing the sdk client generation from the command line.


## Usage

**Pre-Requisites:**
 1. checkout rescuebox source from GitHub
 2. pip or poetry install celery and SQLAlchemy
 3. Download and startup Rabbitmq broker. https://www.rabbitmq.com/docs/install-homebrew and brew install erlang@27
 2. start the rescuebox backend or run from docker container
 3. rescuebox plugin transcribe needs ffmpeg installed : https://www.ffmpeg.org/download.html
 4. rescuebox plugin summarize needs ollama server running https://ollama.com/download
   and model=llama3.2:3b  ( ollama pull llama3.2:3b)  installed


1.  **Start the Rescuebox backend**:  checkout repo and start RB server
    ```bash
    cd <RescueBox_HOME>
    poetry run python -m src.rb-api.rb.api.main
    ```
2.  **Start a Worker**: Run a Celery worker that connects to RB server and executes rescuebox operations.
     ```bash
     cd <RescueBox_HOME/sdk/rescuebox_pipeline>
     celery -A rb_celery  worker -l DEBUG --pool=solo
     or 
     celery -A rb_celery  worker -l DEBUG --pool=solo -E --statedb=worker.state
     ```

3. **Run a Pipeline with intermediate**: Run two rescuebox operations with an intermediate task.
        transcribe -> takes a input dir and outputs txt
        save_to_file -> intermediate task to persist this text to a file
        summarize -> takes this directory where file is saved and outputs a summary file

    ```bash
    cd <RescueBox_HOME/sdk/rescuebox_pipeline>
    python rp_pipeline2.py
    ```

4.  **Run a Pipeline**: Run the chain of rescuebox operations that will start chain and abort it.

    ```bash
    cd <RescueBox_HOME/sdk/rescuebox_pipeline>
    python rb_pipeline3.py
    ```
