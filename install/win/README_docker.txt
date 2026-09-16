Install rescuebox 3.1 on windows 11 using docker, this is an alternate approach
this is used only for developer needs.

1 download rescuebox zip and extract zip to a folder

2 open powershell run as administartor ( right click on powershell icon and run as administartor) 
cd to folder from step 1 and run rb.ps1
 
  --this installs winget to download , docker desktop , winfsp for ufdr mount , ollama server for local models
    import certificate for rescuebox installer , starts pgvector as a docker container
	
3 double click on RescueBox_3.1.0_x64_en-US.msi , this installs rescuebox executables

  a. screen asks for models folder , choose the folder from step 1 where models.zip exists

  b. next choose a destination folder , make sure you have 10GB space in the folder you pick

  c. installer  extracts and starts the rescuebox app
   
  d. logs are located here :   C:\Users\<username>\AppData\Roaming\RescueBox\logs

  e. Code signing: install "Windows SDK Signing Tools for Desktop Apps" (Visual Studio Installer
     -> Individual components) so signtool.exe is available, or set SIGNTOOL_PATH to its full path.
     Local unsigned builds: set RESCUEBOX_SKIP_SIGN=1 before cargo tauri build.
  
4 Assumption/Issues: Nvidia GPU related driver, cuda, cudnn are installed and in the path for recuebox modules to detect and use.

  Docker engine may stop if windows server goes into sleep mode. make sure docker engine is running and pgvector docker image is running
  
  Docker Desktop is prone to engine failure if the server goes into sleep mode ,do these manually or re run powershell script rb.ps1.

	Check the Task Manager: Press Ctrl + Shift + Esc, go to the Details tab, and look for Docker Desktop.exe. If it is present, it may be hung. Right-click it and select End task.

	Update Docker Settings: Launch Docker Desktop and Ensure "Start Docker Desktop when you sign in to your computer" is enabled in the General settings to help it recover automatically after a reboot or wake event.
  
