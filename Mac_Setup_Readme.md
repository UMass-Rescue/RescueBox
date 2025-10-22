#  RescueBox Setup and Run Guide for MacOS users

This guide will help you set up and run the RescueBox application on macOS within a docker container.

##  Initial Setup

###  1. Install Docker (if not installed already)

```bash
# Install Docker Desktop from https://www.docker.com/products/docker-desktop

# Or use Homebrew
brew install --cask docker

# Verify installation
docker --version
```

##  Install and Configure XQuartz (specific for MAC users)

XQuartz is required to display GUI applications from Docker containers on macOS.

###  1. Install XQuartz

```bash
# Install XQuartz using Homebrew
brew  install  --cask  xquartz
```

###  2. Configure XQuartz
1. Restart your mac after installing for XQuartz to initialize properly
2. Open XQuartz from Applications/Utilities or Spotlight
3. Go to **XQuartz → Settings**
4. Navigate to the **Security** tab
5. Check the following option: **"Allow connections from network clients"**
6.  **Quit and restart XQuartz** for changes to reflect
7. Test that the changes have worked by running xclock from your local terminal
```bash
xclock
```
This should bring up a clock GUI window. 
 
---

##  Setup the Project Locally
  
###  1. Cloning git repository:
Clone https://github.com/UMass-Rescue/RescueBox/tree/hackathon
 
 If you are looking to make changes to only the backend/models and want to run UI within browser only- 
```bash
 git checkout hackathon-plugins
 ```

If you want to run the electron UI as well:
```bash
 git checkout hackathon
 ```
  
### 2.  Container Setup
1. Launch VS Code from your terminal where the cloned folder root is using
```bash
 code .
 ```
Or just open VSCode and navigate to the project root

2. Change the src path to your local path in devcontainer.json
```bash
"source=/path/to/RescueBox,target=/home/rbuser/RescueBox,type=bind"
```
3. Launch your container by clicking Cmd + Shift + P and selecting "Reopen in container" 

### 3.  Running the backend
Once the container is up, in a new terminal within the container run:
```bash
./run_server &
```
Validate that the backend runs on http://localhost:8000/. Validate endpoints: info and list_plugins

### 4.  Running the frontend
First validate that popup GUI works from inside the container by opening a new terminal (inside container env) and running:
```bash
xclock
```
 A clock GUI window should open up. If it does not, revisit the Install and Configure XQuartz section and check if anything is missing. If this works fine, proceed to run frontend:

```bash
cd  RescueBox-Desktop
npm install
export DISPLAY=:0
npm start
```

A separate GUI window for the electron UI should open up and the models should load. 

---