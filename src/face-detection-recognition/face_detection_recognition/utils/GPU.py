import os
import ctypes
from face_detection_recognition.utils.logger import log_warning


def check_cuDNN_version():
    try:
        libcudnn = ctypes.CDLL("libcudnn.so")
        # Check if the library is loaded correctly
        if libcudnn is None:
            raise OSError("cuDNN library not found.")
        # Define the return type of the function
        # This is a common pattern for C functions that return size_t
        # ctypes.c_size_t is used to represent the size type in C which is typically an unsigned integer
        libcudnn.cudnnGetVersion.restype = ctypes.c_size_t
        version_num = libcudnn.cudnnGetVersion()

        # cuDNN versions are usually like 8302 -> 8.3.2, or 9300 -> 9.3.0
        major = version_num // 1000
        minor = (version_num % 1000) // 100
        patch = version_num % 100

        cudnn_version_str = f"{major}.{minor}.{patch}"
        required_version = (9, 3, 0)

        if (major, minor, patch) < required_version:
            log_warning(
                f"Forcing CPU usage due to version mismatch. Detected cuDNN {cudnn_version_str}, requires >= 9.3.0."
            )
            os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

    except OSError:
        log_warning("cuDNN not found. Forcing CPU usage.")
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
