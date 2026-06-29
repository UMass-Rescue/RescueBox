import onnxruntime as ort

print(ort.get_available_providers())
# Should include 'CUDAExecutionProvider' when the wheel is correct
