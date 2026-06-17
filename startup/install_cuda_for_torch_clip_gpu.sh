poetry run pip install --upgrade torch torchvision --index-url https://download.pytorch.org/whl/cu130 > /dev/null 2>&1

# no torch in rescuebox
# RC=`poetry run python -c "import torch; print(torch.cuda.is_available())"`

import onnxruntime as ort

# Check for NVIDIA GPU
cuda_available = "CUDAExecutionProvider" in ort.get_available_providers()

# Check for AMD / Intel Windows GPU (if using onnxruntime-directml)
dml_available = "DmlExecutionProvider" in ort.get_available_providers()

echo ""
if [[ "$cuda_available" == "True" ]]; then
    echo "==============================="
    echo "embeddings plugin using CLIP will use GPU"
    echo "==============================="
else
   echo "embeddings plugin using CLIP will not use gpu , CPU only"
fi


