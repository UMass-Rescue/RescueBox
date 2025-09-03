Proposed workflow is a strategy for a hackathon environment. 
By using Docker and VS Code Dev Containers the time spent on environment steps is reduced.

-----

### 🛠️ Prerequisites

1.  **Docker Desktop**: Install and configure Docker Desktop for your OS (macOS or Windows), 
      ensuring sufficient CPU and memory resources are allocated.
2.  **VS Code**: Install Visual Studio Code.
3.  **Dev Containers Extension**: Install the "Dev Containers" extension from the VS Code Marketplace.

-----

### 🚀 Developer Workflow

1.  **Clone the Repository**: Clone the RescueBox repository to your local machine.

2.  **Edit `devcontainer.json`**: Open the project folder in a text editor and update the `devcontainer.json` file. You need to explicitly define the volume mount to ensure VS Code connects your local codebase to the container.
    ```json
    "mounts": [
      "source=C:/path/to/your/rescuebox/repo,target=/rb/Rescuebox,type=bind"
    ]
    ```

3.  **Open in Dev Container**: Open the RescueBox folder in VS Code. The Dev Containers extension will automatically detect the configuration file and prompt you to "Reopen in Container." This initiates a series of automated steps:
      * **Image Pull**: The `nb887/rb-dev:2.1.0` image is pulled from Docker Hub.
      * **Container Start**: A container is launched from the image.
      * **Volume Mount**: The local repository on your machine is mounted to `/rb/Rescuebox` inside the container.
      * **Backend Startup**: You need to run `./run_server &` command to start the backend server with hot-reloading enabled.
      * **Port Forwarding**: The container's port `8000` is exposed to your host machine, providing you autoui UI to access the backend.
      * **Start dependency**: You can start the ollama server in the container if you need it like plugin text-summary.
      * **Frontend Startup**: If you must use the electron frontend cd to RescueBox-Desktop and run `npm start` . This will start the UI. In case it does not confirm `xclock` shows up ok. check the errors during electron startup.
      
4.  **Develop and Test**: Once the container is running, open a web browser and navigate to `http://localhost:8000` to interact with the application. When you edit the code in your local folder, the backend server inside the container will **hot-reload** automatically, reflecting your changes in real-time.

5.  **Persist Changes**: Your code changes are saved directly to your local filesystem. You can commit these changes to GitHub as needed. If the container is stopped and restarted, it will always use the latest code from your mounted local directory.


