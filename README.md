# RescueBox from UMass Rescue Lab


This release has been tested on Windows 11 64-bit hardware. The software does work if you run it on a machine with only a CPU; try it out with a few images or audio files. However for large scale work, because the processing is dependent on machine learning models, you won't see good performance unless you run on a machine that has a modern NVIDIA GPU card.

-----------------------
Notes for Developers Only:

**Frontend (NiceGUI) developer docs:** [frontend/docs/README.md](frontend/docs/README.md) — workflow, database, tests, and related topics.

**src-tauri** folder to build windows rescuebox installer. src-tauri\nsis\README.txt for current build notes.

**image-embeddings** converted to onnx model , text embeddings onnx convert pending..

See the [LICENSE](LICENSE) file for license details.

