# RescueBox from UMass Rescue Lab

This branch is specific to hackathon 2025 work.

**For Hackathon ideas** [issues](https://github.com/UMass-Rescue/RescueBox/issues)

Use this branch hackathon-plugins and steps below if you pick an issue that is plugins related.

Use the other branch hackathon for rescuebox infrastructure improvement ideas.

General howto documentation is available on the [Wiki](https://github.com/UMass-Rescue/RescueBox/wiki)
 --Overview and Plugins could be useful.


## Step-by-Step Setup [How To Video](https://drive.google.com/file/d/1q27_mH22k6PXDhHhPWR8KSby3HSlQ6uQ/view?usp=sharing)
To develop with VS Code on your laptop.

1. Install pre reqs : docker engine, git, google drive downloader gdown
    note: python and other runtime dependencies are in the container.

2. git checkout rescuebox branch = hackathon-plugins
  
3. refer RescueBox/.devcontainer/devcontainer.json , edit this file as per instructions in it.
  mounts : source=/home/user/RescueBox <-- this should be the RescueBox path from previous step #2

  start the rescuebox container "reopen in container" . open terminal insider container.

4. run script setup_rescuebox.sh on your laptop (host) , this must be executed to pull onnx models and demo files and howto videos, that are too large to push to git repo. the model files are manadatory to run existing models.

5.  inside the docker container, you must run cd /home/rbuserRescueBox and execute 'run_server', to start the rescuebox backend server.

6. note that the docker container has pre-reqs installed like : python , poetry.
  you now run cmds insider the container to start rescuebox backend server 
  your laptop contains the git source that will be mounted inside the container. this allows you to modify the  source code that runs inside your container
the setup of run docker container with pre-reqs and your host laptop with source allows you to quickly develop with rescuebox.

7. Rescuebox backend has a UI running on http://localhost:8000 , this will allow you to run existing models
 the new plugin you will develop will dynamically show up in the UI , refer web/rescuebox-autoui.





