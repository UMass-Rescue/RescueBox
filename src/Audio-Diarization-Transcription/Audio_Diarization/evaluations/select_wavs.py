import os
import random
import shutil


def select_random_wavs(input_folder, output_folder, sample_size=50):
    # Ensure the input path exists
    if not os.path.exists(input_folder):
        raise FileNotFoundError(f"Input folder '{input_folder}' does not exist.")

    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Get all .wav files from the input folder
    wav_files = [f for f in os.listdir(input_folder) if f.lower().endswith(".wav")]

    if len(wav_files) < sample_size:
        raise ValueError(
            f"Not enough .wav files in the input folder ({len(wav_files)} found, {sample_size} needed)."
        )

    # Randomly sample 50 unique .wav files
    selected_files = random.sample(wav_files, sample_size)

    # Copy selected files to the output folder
    for file_name in selected_files:
        src_path = os.path.join(input_folder, file_name)
        dst_path = os.path.join(output_folder, file_name)
        shutil.copy2(src_path, dst_path)

    print(f"✅ {sample_size} files copied to: {output_folder}")


# Function Call, Change the file path as needed
# select_random_wavs("input/folder/filepath", "/output/folder/filepath")
