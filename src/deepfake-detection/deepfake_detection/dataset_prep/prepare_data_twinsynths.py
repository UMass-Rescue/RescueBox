import os
import shutil
from pathlib import Path


def copy_images(source_dirs, dest_dir, max_images=10):
    os.makedirs(dest_dir, exist_ok=True)
    img_extensions = {".jpg", ".jpeg", ".png"}

    for source_dir in source_dirs:
        if "real" in source_dir:
            prefix = "R"
            print("works")
        elif "TwinSynths_GAN" in source_dir and "fake" in source_dir:
            prefix = "F_GAN"
            print("works2")
        elif "TwinSynths_DM" in source_dir and "fake" in source_dir:
            prefix = "F_DM"
            print("works3")
        images_copied = 0
        print(f"Copying images from {source_dir} to {dest_dir}...")
        for file_name in os.listdir(source_dir):
            if images_copied >= max_images:
                print(f"Reached the maximum limit of {max_images} images.")
                break
            file_path = os.path.join(source_dir, file_name)
            if (
                os.path.isfile(file_path)
                and Path(file_path).suffix.lower() in img_extensions
            ):
                try:
                    new_file_name = f"{prefix}_{file_name}"
                    dest_path = os.path.join(dest_dir, new_file_name)
                    shutil.copy(file_path, dest_path)
                    images_copied += 1
                except Exception as e:
                    print(f"Error copying {file_path}: {e}")

    print(f"Copied {images_copied} images to {dest_dir}.")


ts_dm_path = "datasets/TwinSynths/TwinSynths/TwinSynths_DM"
ts_gan_path = "datasets/TwinSynths/TwinSynths/TwinSynths_GAN"

source_directories = [
    ts_dm_path + "/0_real",
    ts_dm_path + "/1_fake",
    ts_gan_path + "/1_fake",
]
destination_directory = "sample_input"

copy_images(source_directories, destination_directory)
