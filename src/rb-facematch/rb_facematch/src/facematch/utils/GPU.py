import os
import logging
import tensorflow as tf

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)



def check_cuDNN_version():
    try:
        # Get the current cuDNN versions
        cudnn_version = tf.sysconfig.get_build_info()["cudnn_version"]

        # Define the minimum required versions for compatibility
        required_cudnn_version = "9.3.0"

        # Check compatibility
        if cudnn_version < required_cudnn_version:
            logger.warn(
                "Forcing CPU usage due to version mismatch. Requires cuDNN version 9.3.0 or above "
            )
            os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Disable GPU usage

    except KeyError:
        logger.warn("No cuDNN found. Forcing CPU usage.")
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
