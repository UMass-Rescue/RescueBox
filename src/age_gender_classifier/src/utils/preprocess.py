import cv2 as cv
import logging
import numpy as np

logging.basicConfig(level=logging.INFO)  # shows logs in the system


def is_valid_image(pixel_string):
    """checks if pixel string exactly contains 48*48 = 2304 values"""
    pixel = pixel_string.strip().split()
    return len(pixel) == 48 * 48


def is_damaged(image, threshold_low=10, threshold_high=255, min_variance=10):
    """
    Detects damaged images based on pixel intensity distribution.
    - threshold_low: If pixels are below this, the image may be too dark.
    - threshold_high: If pixels are above this, the image may be too bright.
    - min_variance: If the variance is too low, image may lack details
    """
    if np.mean(image) < threshold_low or np.mean(image) > threshold_high:
        return True  # likely corrupted
    # Check if the image lacks details (variance too low)
    if np.mean(image) < min_variance:
        return True  # likely corrupted
    return False


def enhance_image(image):
    """kernel, sharpening, denoising, and bilateral filtering techniques for image preprocessing"""
    kernel = np.array([[0, -0.5, 0], [-0.5, 3, -0.5], [0, -0.5, 0]])  # Sharpening
    sharpened = cv.filter2D(image, -1, kernel)
    smoothed = cv.bilateralFilter(sharpened, d=3, sigmaColor=55, sigmaSpace=55)
    denoised = cv.fastNlMeansDenoising(
        smoothed, h=5, templateWindowSize=7, searchWindowSize=21
    )
    return denoised
