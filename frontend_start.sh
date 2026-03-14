# need cuda path on unity
# after creating gpu environment
# run  
module load cuda/13.1
export CUDA_PATH=/modules/opt/linux-ubuntu24.04-x86_64/nvhpc/Linux_x86_64/24.9/cuda/13.1

export LIBRARY_PATH=$CUDA_PATH/targets/x86_64-linux/lib
export LD_LIBRARY_PATH=$CUDA_PATH/targets/x86_64-linux/lib
RC=`find $LD_LIBRARY_PATH -name "libcublas.so.13"`

if [[ "$RC" == "" ]]; then
   echo "cuda lib not found , fix manually and retry"
   exit 1
else
  echo "cuda setup ok"
fi

# these may not be needed
export ORT_DISABLE_THREAD_AFFINITY=1
export ONNXRUNTIME_NUM_THREADS=1
export OMP_NUM_THREADS=1

# download granite model gguf
if [ ! -f "./granite-4.0-micro-Q4_0.gguf" ]; then
 echo "granite model download..."
curl -L -O https://huggingface.co/ibm-granite/granite-4.0-micro-GGUF/resolve/main/granite-4.0-micro-Q4_0.gguf
fi
if [ ! -f "./granite-4.0-micro-Q4_0.gguf" ]; then
 echo "granite gguf download failed, fix and retry"
 exit 1
fi

# install ffmpeg.exe
if [ ! -f "./ffmpeg" ]; then
   "ffmpeg download..."
   curl https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz -o f.tar.gz && \
   tar -xvf f.tar.gz && rm -f f*.gz && \
   chmod 755 ffmpeg-git-20240629-amd64-static/ffmpeg && \
   mv ffmpeg-git-20240629-amd64-static/ffmpeg .
   rm -rf ffmpeg-git-20240629-amd64-static
fi
if [ ! -f "./ffmpeg" ]; then
   echo "ffmpeg download failed, fix and retry"
   exit 1
fi

if [[ -n "$VIRTUAL_ENV" ]]; then
    echo "\n"
    echo "Virtual environment is now active."
    poetry run python frontend/main.py
    echo "\n"
else
    echo "Error: Virtual environment was not activated."
    echo "Cannot start poetry frontend for rescuebox"
fi

