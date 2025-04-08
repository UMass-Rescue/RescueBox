
#  Goal: make a single rescuebox.exe EXE with all plugins and run as a backend Server 
#  make UI installer a single EXE that will include the above rescuebox.exe

1 Make rescuebox EXE steps:

pyinstaller is used to make a single python exe. The output type is dir to speed up startup time.
cd to top level folder for rescuebox containing the rescuebox.spec file
install pre-reqs like ffmpg.exe for audio in this folder , as mentioned in the spec file.
run "poetry run pyinstaller rescuebox.spec"

this will create "dist" and "build"
"dist" is the single folder that contains all the python dependencies and rescuebox.exe 

start server : dist\rescuebox\rescuebox.exe , to confirm its able to start and stop it (contol-c)


2 Make rescuebox desktop on Windows steps, put these cmds in a file and run as script:

cd RescueBox-Desktop
# copy the rescuebox server folder from <RescueBox-HOME>/dist  to  RescueBox-Desktop/assets/rb_server

cmd /c npm cache clean --force
cmd /c npm cache verify
cmd /c npm install
cmd /c npm run postinstall
cmd /c npm run build
cmd /c npm run rebuild
cmd /c npm exec electron-builder -- --win

this will create a EXE in release/build , in windows for example : RescueBox-Desktop Setup 1.1.0.exe

3 Install Steps:

 double click to install the RescueBox-Desktop UI Exe on windows. this will extract the rescuebox exe that is bundled with it.
 Desktop UI will start this rescuebox exe server during install.
 Desktop UI will communicate with this rescuebox exe server and register all the plugins.
 subsequent restart of rescueBox Desktop UI will restart the rescuebox exe server.

Notes:
# there is one sqlite db that will be re used for initial install and subsequent restarts.
# 
