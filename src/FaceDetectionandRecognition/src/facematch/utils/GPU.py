import os

import tensorflow as tf

from src.facematch.utils.logger import log_warning


def check_cuDNN_version():
    try:
        # Get the current cuDNN versions
        cudnn_version = tf.sysconfig.get_build_info()["cudnn_version"]

        # Define the minimum required versions for compatibility
        required_cudnn_version = "9.3.0"

        # Check compatibility
        if cudnn_version < required_cudnn_version:
            log_warning(
                "Forcing CPU usage due to version mismatch. Requires cuDNN version 9.3.0 or above "
            )
            os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Disable GPU usage

    except KeyError:
        log_warning("No cuDNN found. Forcing CPU usage.")
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
