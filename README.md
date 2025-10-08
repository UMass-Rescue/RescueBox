# RescueBox from UMass Rescue Lab

Welcome to RescueBox! This document provides instructions for setting up and running the project, specifically for the 2025 Hackathon.

**For Hackathon ideas, please see our [issues page](https://github.com/UMass-Rescue/RescueBox/issues).**

For more detailed design and architecture documents, refer to the `rb-docs` directory. General documentation is also available on the [Wiki](https://github.com/UMass-Rescue/RescueBox/wiki).

## Table of Contents
- [Getting Started (TL;DR)](#getting-started-tldr)
- [Prerequisites](#prerequisites)
- [Step-by-Step Setup](#step-by-step-setup)
- [Running the Application](#running-the-application)
- [Troubleshooting](#troubleshooting)
- [Architecture Notes](#architecture-notes)

## Getting Started (TL;DR)

For experienced developers, here’s the fast track to get up and running:

1.  **Clone the repo and checkout the `hackathon` branch:**
    ```bash
    git clone https://github.com/UMass-Rescue/RescueBox.git
    cd RescueBox
    git checkout hackathon
    ```
2.  **Configure the dev container:**
    *   Open `.devcontainer/devcontainer.json`.
    *   Update the `source` path in the `mounts` section to your local repository path.
3.  **Launch the dev container:**
    *   Open the `RescueBox` folder in VS Code.
    *   Click "Reopen in Container" when prompted.
4.  **Download large files:**
    ```bash
    # On your host machine (not in the container)
    bash ./setup_rescuebox.sh
    ```
5.  **Start services:**
    ```bash
    # Inside the container
    bash ./pre-req.sh
    ```
    The backend UI is available at http://localhost:8000.

## Prerequisites

Before you begin, please ensure you have the following software installed:

- **Git:** For cloning the repository.
- **Docker Desktop:** To run the development container.
- **VS Code:** With the ["Dev Containers" extension](https://code.visualstudio.com/docs/devcontainers/containers) installed.
- **Python:** With `pip` to install `gdown`.
  ```bash
  pip install gdown
  ```

## Step-by-Step Setup . [How To Video](https://drive.google.com/file/d/1q27_mH22k6PXDhHhPWR8KSby3HSlQ6uQ/view?usp=sharing)

Follow these steps carefully to set up your development environment.

1.  **Clone and Checkout Branch:**
    Clone the repository and switch to the `hackathon` branch.
    ```bash
    git clone https://github.com/UMass-Rescue/RescueBox.git
    cd RescueBox
    git checkout hackathon
    ```

2.  **Configure Dev Container:**
    This is a critical step. The dev container needs to mount your local repository files.
    *   Open the `RescueBox/.devcontainer/devcontainer.json` file in VS Code.
    *   Locate the `mounts` section.
    *   Update the `source` path to point to the absolute path of your cloned `RescueBox` repository.
        *   **Example for Windows:** If you cloned to `C:\work\rel\RescueBox`, the source should be `/c/work/rel/RescueBox`.
        *   **Example for macOS/Linux:** If you cloned to `/home/user/RescueBox`, the source should be `/home/user/RescueBox`.

3.  **Start Dev Container:**
    *   Open the `RescueBox` folder in VS Code.
    *   A prompt will appear in the bottom-right corner. Click **"Reopen in Container"**.
    *   VS Code will now build and start the Docker container. This may take a few minutes.

4.  **Download Large Files:**
    On your host laptop (not in the container), run the setup script to download required ONNX models , howto Videos and demo files. You can use Git Bash or WSL on Windows.
    ```bash
    # From the root of your RescueBox repository
    bash ./setup_rescuebox.sh
    ```

## Running the Application

1.  **Start Services:**
    Inside the VS Code terminal (which is now a shell inside the container), run the `pre-req.sh` script to start the backend services (Ollama, RabbitMQ, RescueBox backend).
    ```bash
    # Inside the container
    bash ./pre-req.sh
    ```
    The backend UI will be available at http://localhost:8000.

2.  **(Optional) Run Electron UI:**
    To use the alternative electron desktop UI, open a new terminal in VS Code and run:
    ```bash
    # Inside the container
    cd Rescuebox-Desktop
    npm start
    ```
    This UI may need xServe XQuartz on macos.

3.  **(Optional) Run Celery Pipeline Demo:**
    To test the Celery pipeline, ensure RabbitMQ is running (from `pre-req.sh`). Then, in a new VS Code terminal, start the Celery worker.
    ```bash
    # Inside the container - start worker in a new terminal
    bash ./src/rescuebox-pipeline/worker.sh
    ```
    In another terminal, run the demo script commands one by one to see the pipeline in action.
    ```bash
    # Inside the container - in another new terminal
    # Execute commands from ./src/rescuebox-pipeline/demo.sh
    ```

## Troubleshooting

*(This section is a work in progress. Please add any common issues you encounter!)*

*   **Issue:** The dev container fails to run.
    *   **Solution:** Ensure Docker Desktop is running. Check the logs in the VS Code terminal for specific errors.
    you should use docker run cmdline to start the container and confirm it works outside of VS Code.

*   **Issue:** "ModuleNotFound error: No module named 'xxx" errors when running py scripts inside the container.
    *   **Solution:** ```poetry env info``` to confirm virtual env. run ```poetry install``` from top level RescueBox only.

## Architecture Notes

*   **Development Loop:** Your local source code is mounted into the container, so any changes you make on your host machine are immediately reflected inside the container.
*   **Celery Pipelines:** The `rb-docs` directory contains design documents about our asynchronous task processing using Celery. Alternatives like Luigi, Dagster, Airflow, and Temporal were considered.

**Important:** If you make changes to files *inside* the container that are not part of the mounted repository, they will be lost on restart. Be mindful of this.