
to make nsis windows bundler work with > 2 GB rescuebox pyinstaller dir

cargo tauri build  --bundles nsis --verbose <- full build
cargo tauri build  --bundles nsis --config src-tauri/tauri.fast.conf.json --verbose <- skip pyinstaller steps

https://sourceforge.net/projects/nsisbi/files/

C:\work\rel\v3\RescueBox\src-tauri\nsis nsis-binary-7423-2.zip
  https://sourceforge.net/projects/nsisbi/files/latest/download

1 replace C:\Users\foth2\AppData\Local\tauri\NSIS\makensis.exe with >2GB support exe

2 "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Tools\MSVC\14.29.30133\bin\Hostx64\x86\editbin.exe" /LARGEADDRESSAWARE C:\Users\foth2\AppData\Local\tauri\NSIS\makensis.exe

3 refer tauri-conf.json 
   "windows": {
      "nsis": {
        "template": "nsis/custom.nsi",
        "installMode": "perMachine"
      }
    },

4 Create a new file in your project: src-tauri\nsis\custom.nsi.

Grab the default Tauri v2 NSIS template from the official Tauri GitHub repository and paste it into that file.
    https://github.com/tauri-apps/tauri/blob/dev/crates/tauri-bundler/src/bundle/windows/nsis/installer.nsi
	
Near the top of the file, find the line that says SetCompressor /SOLID lzma.

5 edit custom.nsi to 

SetCompressor "lzma"

6 refer https://v2.tauri.app/distribute/windows-installer/#extending-the-installer to add more install steps 
 installer hooks to automatically install system dependencies that application requires like ollama, ufdr-mount pre-reqs
 
sample good output:

Running [tauri_bundler::utils] Command `C:\Users\foth2\AppData\Local\tauri\NSIS\makensis.exe  -INPUTCHARSET UTF8 -OUTPUTCHARSET UTF8 -V3 C:\work\rel\v3\RescueBox\src-tauri\target\release\nsis\x64\installer.nsi`
	 
Using lzma compression.

EXE header size:               52224 / 38400 bytes
Install code:                  66419 / 984492 bytes
Install data:             1178260876 / 2221747642 bytes
Uninstall code+data:           78782 / 84298 bytes
CRC (0xD2265F5F):                  4 / 4 bytes

Total size:               1178458305 / 2222854836 bytes (53.0%)
    Finished [tauri_bundler::bundle] 1 bundle at:
        C:\work\rel\v3\RescueBox\src-tauri\target\release\bundle\nsis\RescueBox_3.1.0_x64-setup.exe