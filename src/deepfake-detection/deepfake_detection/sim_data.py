from os import listdir
from os.path import isdir

import numpy as np
from PIL import Image


class defaultDataset:
    def __init__(self, dataset_path, resolution=224):
        assert isdir(dataset_path), f"Dataset path {dataset_path} does not exist."
        self.dataset_path = dataset_path
        self.resolution = resolution
        self.images = []
        for image_path in listdir(dataset_path):
            if (
                image_path.lower().endswith(".jpg")
                or image_path.lower().endswith(".png")
                or image_path.lower().endswith(".jpeg")
            ):
                self.images.append(dataset_path + "/" + image_path)

    def __len__(self):
        return len(self.images)

    def read_image(self, path):
        image = Image.open(path).convert("RGB")
        original_res = image.size
        # Return the original image without any processing
        return image, original_res

    def __getitem__(self, i):
        try:
            image, res = self.read_image(self.images[i])
        except:
            print(f"Error reading image {self.images[i]}")
            return None
        sample = {
            "image_path": self.images[i],
            "image": image,  # Now returns the PIL image directly
            "is_real": np.array([1 if "R_" in self.images[i] else 0]),
            "original_res": res,
        }
        return sample
