import os
from pydub import AudioSegment

def convert_flac_to_wav(input_folder, output_folder):
    if not os.path.exists(input_folder):
        raise FileNotFoundError(f"Input folder '{input_folder}' does not exist.")
    
    os.makedirs(output_folder, exist_ok=True)

    flac_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.flac')]

    for file_name in flac_files:
        input_path = os.path.join(input_folder, file_name)
        output_path = os.path.join(output_folder, file_name.replace('.flac', '.wav'))

        audio = AudioSegment.from_file(input_path, format="flac")
        audio.export(output_path, format="wav")

        print(f"Converted: {file_name} → {os.path.basename(output_path)}")

    print(f"\nConversion complete! {len(flac_files)} files processed.")

# Function Call, Change the file path as needed
# convert_flac_to_wav("input/folder/filepath", "output/folder/filepath")
