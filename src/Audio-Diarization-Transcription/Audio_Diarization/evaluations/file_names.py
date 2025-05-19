import os


def list_files(input_folder, output_file="file_list.txt"):
    if not os.path.exists(input_folder):
        raise FileNotFoundError(f"Folder '{input_folder}' does not exist.")

    files = os.listdir(input_folder)

    with open(output_file, "w") as f:
        for file in files:
            f.write(file + "\n")

    print(f"File names written to: {output_file}")


# Function Call, Change the file path as needed
# list_files("input/folder/filepath", "output_file_list.eval")
