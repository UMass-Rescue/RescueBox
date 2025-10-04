# RescueBox from UMass Rescue Lab

This branch is specific to hackathon 2025 work.

**For Hackathon ideas** [issues](https://github.com/UMass-Rescue/RescueBox/issues)

For details on design ideas refer rb_docs

General howto documentation is available on the [Wiki](https://github.com/UMass-Rescue/RescueBox/wiki)
 --Overview and Plugins could be useful.

To develop with VS Code

1. Install pre reqs : docker engine , git , google drive downloader gdown

2. git checkout rescuebox branch = hackathon
  
3. refer RescueBox/.devcontainer/devcontainer.json , edit this file as per instructions.
  mounts : source=/c/work/rel/RescueBox <-- this should be the RescueBox path from previous step #2

  start the rescuebox container "reopen in container"

4. run script setup_rescuebox.sh on your laptop (host) , this must be executed to pull onnx models , demo files that are too large to push to git repo. these files are manadatory to run existing models. After this  script runs all the files 
needed to run rescuebox is now available in this folder on your laptop.

5. note that the docker container has pre-reqs installed like : python , poetry , ollama .
  you now run cmds insider the container to start rescuebox backend server and other services (see notes below).
  your laptop contains the git source that will be mounted inside the container. this allows you to modify the  source code that runs inside your container
the setup of run docker container with pre-reqs and your host laptop with source allows you to quickly develop with rescuebox.

Notes:
1. Inside the docker container , you must run RescueBox/pre-req.sh , this starts up ollama serve , rescuebox backend server and rabbitmq server. 

2. Rescuebox backend has a UI running on http://localhost:8000 , this will allow you to run existing models
 Or
 Rescuebox electron UI is a different UI a customer UI that can also be started if neeeded from Rescuebox-Desktop folder in the container using npm start.

3. To run celery pipeline : start rabbitmq server , and celery-worker (RescueBox/src/rescuebox-pipeline/worker.sh) then run demo (RescueBox/src/rescuebox-pipeline/demo.sh one cmd at a time)

4. rb-docs : contains design docs specific to celery piplelines , async long running tasks using celery , dynamic plugin or pipeline-plugin. these have a common celery dependency 
other alternatives could be : Luigi / Dagster / Airflow / Temporal