# need cuda path on unity linux
# after creating gpu environment
# checks for version 13 only , can be changed to 12.x i suppose 
#
# for CLIP torch python versions of cude specific to  PyTorch  pytorch-cu130 is installed 
#  by another script install_cuda_for_torch_clip_gpu.sh

# Get the OS and Architecture
OS=$(uname -s)
ARCH=$(uname -m)

if [[ "$OS" == "Linux" && "$ARCH" == "aarch64" ]]; then
    echo "Running on Linux aarch64 ARM."

    export CUDA_PATH=/usr/local/cuda-13.0
    export LIBRARY_PATH=$CUDA_PATH/targets/sbsa-linux/lib
    export LD_LIBRARY_PATH=$CUDA_PATH/targets/sbsa-linux/lib
    
    RC=`find $LD_LIBRARY_PATH -name "libcublas.so.13"`

    if [[ "$RC" == "" ]]; then
      echo "cuda lib not found , fix manually and retry"
      exit 1
    else
      echo "cuda setup ok"
    fi
fi
