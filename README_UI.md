
### Rescuebox remove electon Desktop and add nicegui frontend

- main reasons are : all python code , browser interface , ai-chat style user experience

- refer frontend/readme.md and frontend/docs for details

### runtime env
 windows does work , however
 - this branch is focussed on running in unity environment with  GPU


### GPU needs
 - GPU is mandatory for granite tool calling and ollama model like gemma3:4b for image-summary
 - granite-4.0-micro-Q4_0.gguf is downloaded and used this is done using llamma-cpp-python module
 - llamma-cpp-python python package on linux has to be compiled with gpu enabled

 - without gpu works however its very slow


### refer run_backend_server
    -script to check for cuda /cudnn / onnxruntime-gpu / docker / pgvector dependecies
    -starts the fastapi server and a developer-ui at http://localhost:8000 . Use this to test new plugin

### refer run_ui_server
   -script to start frontend ui for customer scenarios. for plugin developer this is really not needed
 




