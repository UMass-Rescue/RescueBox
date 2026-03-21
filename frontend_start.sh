# need cuda path on unity
# after creating gpu environment
# run  
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

if [[ -n "$VIRTUAL_ENV" ]]; then
    echo "\n"
    echo "Virtual environment is now active."
    poetry run python frontend/main.py
    echo "\n"
else
    echo "Error: Virtual environment was not activated."
    echo "Cannot start poetry frontend for rescuebox"
fi

