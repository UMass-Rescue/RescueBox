
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


### concurrent users can open rescuebox server and run jobs , these are saved based on browser session id, hence each user will only see their executions




