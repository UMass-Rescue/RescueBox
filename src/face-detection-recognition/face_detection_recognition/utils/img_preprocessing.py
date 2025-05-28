import os
import cv2

# Define input and output directories
input_dir = "benchmark_testing/LFWdataset/new_sample_queries"
output_dir = "benchmark_testing/LFWdataset/resized_queries"

# Ensure output directory exists
# The time is reduced to 540s but the accuracy is also reduced to 0.69
os.makedirs(output_dir, exist_ok=True)

for filename in os.listdir(input_dir):
    if filename.lower().endswith(("png", "jpg", "jpeg", "bmp", "gif")):
        img_path = os.path.join(input_dir, filename)
        # Read the image
        image = cv2.imread(img_path)

        scale_percent = 50  # Reduce size by 50%
        width = int(image.shape[1] * scale_percent / 100)
        height = int(image.shape[0] * scale_percent / 100)
        dim = (width, height)

        resized = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)

        # Save resized image
        output_path = os.path.join(output_dir, filename)
        cv2.imwrite(output_path, resized)
        print(f"Resized and saved: {output_path}")

print("All images have been resized and saved successfully.")
