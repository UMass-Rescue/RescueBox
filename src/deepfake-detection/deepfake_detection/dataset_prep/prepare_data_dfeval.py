import os
import shutil
from pathlib import Path
import pandas as pd


def copy_images(dest_dir, max_images=10):
    # Load metadata
    df = pd.read_csv(
        os.path.join("datasets", "Deepfake-Eval-2024", "image-metadata-publish.csv")
    )
    df = df[df["Finetuning Set"] == "Test"]
    df = df[~df["Filename"].str.contains("webp", na=False)]  # Exclude "webp" files
    df["name"] = (
        df["Ground Truth"].apply(lambda x: "F_" if x == "Fake" else "R_")
        + df["Filename"]
    )
    filenames = df["name"].values.tolist()
    filenames = filenames[:max_images]

    # Define source and destination directories
    source_dir = os.path.join("datasets", "Deepfake-Eval-2024", "image_data")
    os.makedirs(dest_dir, exist_ok=True)

    # Supported image extensions
    img_extensions = {".jpg", ".jpeg", ".png"}
    images_copied = 0

    print(f"Copying images from {source_dir} to {dest_dir}...")
    for file_name in filenames:
        if images_copied >= max_images:
            print(f"Reached the maximum limit of {max_images} images.")
            break

        # Remove the prefix ("F_" or "R_") to match the actual file in the source directory
        actual_file_name = file_name[2:]
        file_path = os.path.join(source_dir, actual_file_name)

        # Check if the file exists and has a valid extension
        print(f"Checking file: {file_path}, Exists: {os.path.isfile(file_path)}")
        if (
            os.path.isfile(file_path)
            and Path(file_path).suffix.lower() in img_extensions
        ):
            try:
                dest_path = os.path.join(dest_dir, file_name)
                shutil.copy(file_path, dest_path)
                images_copied += 1
            except Exception as e:
                print(f"Error copying {file_path}: {e}")
        else:
            print(
                f"Skipped: {actual_file_name} (File not found or unsupported extension)"
            )

    print(f"Copied {images_copied} images to {dest_dir}.")


# Destination directory and function call
destination_directory = os.path.join("sample_input")
copy_images(destination_directory)
