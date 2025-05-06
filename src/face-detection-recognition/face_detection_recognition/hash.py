import hashlib
from PIL import Image


def sha256_image(image_path, bbox):
    """
    Calculates the SHA256 hash of an image file.

    Args:
        image_path (str): The path to the image file.

    Returns:
        str: The SHA256 hash of the image as a hexadecimal string.
             Returns None if the file cannot be opened.
    """
    try:
        with Image.open(image_path) as img:
            x, y, width, height = bbox
            cropped_img = img.crop((x, y, x + width, y + height))
            img_bytes = cropped_img.tobytes()
            sha256_hash = hashlib.sha256(img_bytes).hexdigest()
            return sha256_hash
    except FileNotFoundError:
        print(f"Error: File not found at {image_path}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
