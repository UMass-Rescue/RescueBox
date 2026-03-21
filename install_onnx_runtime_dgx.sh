# Remove all ONNX Runtime packages
poetry run pip uninstall onnxruntime onnxruntime-gpu -y

# Reinstall only the Ultralytics GPU wheel
poetry run pip install https://github.com/ultralytics/assets/releases/download/v0.0.0/onnxruntime_gpu-1.24.0-cp312-cp312-linux_aarch64.whl

# Confirm providers
poetry run python -c "import onnxruntime as ort; print(ort.get_available_providers())"

# confirm output ['TensorrtExecutionProvider', 'CUDAExecutionProvider', 'CPUExecutionProvider']

# also install , else error is: 
# Failed to load library /home/tester/.cache/pypoetry/virtualenvs/rescuebox--hzmPVnY-py3.12/lib/python3.12/site-packages/onnxruntime/capi/libonnxruntime_providers_cuda.so with error: libcudnn.so.9: cannot open shared object file: No such file or directory

sudo apt-get update
sudo apt-get install -y libcudnn9-cuda-13
