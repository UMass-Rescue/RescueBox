
#  Goal: make a single rescuebox.exe EXE with all plugins and run as a backend Server
#  add pre-req installers, onxx files
#  make UI installer a single EXE that will include rescuebox.exe and the above artifacts
#  make a zip file of the installer + docs + licenses to be shared with customers

1 Make rescuebox EXE steps:

pyinstaller is used to make a single python exe. The output type is dir to speed up startup time.
cd to top level folder for rescuebox containing the rescuebox.spec file
install pre-reqs like ffmpg.exe for audio in this folder , as mentioned in the spec file.
run "poetry run pyinstaller rescuebox.spec"

also copy the onnx model files for all plugins.
example : src/age_and_gender_detection/models will need
the three version-RFB-640.onnx, age_googlenet.onnx,gender_googlenet.onnx model files.
run "poetry run pyinstaller rescuebox.spec"

this will create "dist" and "build"
"dist" is the single folder that contains all the python dependencies and rescuebox.exe.

copy the cuda12 dlls into the dist\rescuebox folder after the build is complete.
   https://umass-my.sharepoint.com/:u:/r/personal/jaikumar_umass_edu/Documents/2.1-build/cuda12_gpu_dlls.zip?csf=1&web=1&e=sM9U9s

start server : dist\rescuebox\rescuebox.exe , to confirm its able to start and stop it (contol-c)


2.1 copy the pre reqs for the desktop exe
  a these artifacts go into RecueBox-Desktop\assets\rb_server folder.
          https://umass-my.sharepoint.com/:u:/r/personal/jaikumar_umass_edu/Documents/2.1-build/assets_rb_server.zip?csf=1&web=1&e=cJIsbR
     demo -sample files for running plugins
     docs - rescuebox docs
     OllamaSetup.exe pre-req for text-summary plugin ,
     winfsp-2.x.msi pre-req for ufdr-plugin

  b copy the rescuebox server from pyinstaller output folder
          <RescueBox-HOME>/dist  to  RescueBox-Desktop/assets/rb_server

  c. these assets are large over 2GB hence needs fix
    download https://umass-my.sharepoint.com/:u:/r/personal/jaikumar_umass_edu/Documents/2.1-build/nsis-update.zip?csf=1&web=1&e=SXK85E

    extract and copy/overwrite C:\Users\<user-name>\AppData\Local\electron-builder\Cache\nsis with the unzip of nsis-binary-7423-2.zip

    all the sub folders like nsis-old-version\bin with get updated
    npm build will work ok without errors because RB is >  2 GB

  d update package.json to sign the ouput of the electron-builder
       "signtoolOptions": {
          "certificateFile": "rescuelab_cs.umass.edu.pfx",
          "certificatePassword": "changeMe"
        }

2.2 Make rescuebox desktop exe on Windows steps, put these cmds in a file and run as script:


cd RescueBox-Desktop
# copy the rescuebox server folder from <RescueBox-HOME>/dist  to  RescueBox-Desktop/assets/rb_server

cmd /c npm cache clean --force
cmd /c npm cache verify
cmd /c npm install
cmd /c npm run postinstall
cmd /c npm run build
cmd /c npm run rebuild
cmd /c npm exec electron-builder -- --win

this will create a EXE in "RescueBox-Desktop\release\build", in windows for example : RescueBox-Desktop Setup 2.1.0.exe

2.3 Make release zip with docs and licenses:

     download https://umass-my.sharepoint.com/:u:/r/personal/jaikumar_umass_edu/Documents/2.1-build/License%20%26%20Copyright.zip?csf=1&web=1&e=okCLn3
     extract the License&Copyright folder to the same folder with exe generated in step 2.2 that is "RescueBox-Desktop\release\build"

     copy the docs from RescueBox-Desktop\assets\rb_server\docs to RescueBox-Desktop\release\build\

     make a zip of these 3 : the exe + licenses + docs, this is the release artifact to be shared with customers

3 Install Steps:

 double click to install the RescueBox-Desktop UI Exe on windows. this will extract the rescuebox exe that is bundled with it.
 Desktop UI will start this rescuebox exe server during install.
 Desktop UI will communicate with this rescuebox exe server and register all the plugins.
 subsequent restart of rescueBox Desktop UI will restart the rescuebox exe server.

Notes:
# downloads from ondrive include onnx-files, model-demo files, pre-reqs :ollama+winfsp,  cuda12-dlls-for-gpu , nsis-2gb-fix, docs, licenses
# code sign exe required pfx file and password
