from typing import Any, Callable, Sequence

import numpy as np
from PIL import Image


class Compose:
    def __init__(self, transforms: Sequence[Callable[[Any], Any]]):
        self.transforms = transforms

    def __call__(self, img: Any) -> Any:
        # pass img through each transform in sequence
        for t in self.transforms:
            img = t(img)
        return img


class InterpolationMode:
    BILINEAR = Image.BILINEAR


class Resize:
    def __init__(self, size: int, *, interpolation=InterpolationMode.BILINEAR):
        # size = target shorter side length
        self.size = size
        self.interpolation = interpolation

    def __call__(self, img: Image.Image) -> Image.Image:
        w, h = img.size
        # determine new size so that the shorter side == self.size
        if w < h:
            new_w = self.size
            new_h = int(h * (self.size / w))
        else:
            new_h = self.size
            new_w = int(w * (self.size / h))
        return img.resize((new_w, new_h), self.interpolation)


class CenterCrop:
    def __init__(self, size: int):
        self.size = size  # we assume a square crop

    def __call__(self, img: Image.Image) -> Image.Image:
        w, h = img.size
        new_w, new_h = self.size, self.size
        left = (w - new_w) // 2
        top = (h - new_h) // 2
        return img.crop((left, top, left + new_w, top + new_h))


class ToImage:
    def __call__(self, img: Any) -> np.ndarray:
        # if it’s already an array, assume H×W×C uint8
        if isinstance(img, np.ndarray):
            return img
        # else assume PIL.Image
        return np.array(img, copy=False)


class ToDtype:
    def __init__(self, dtype: type, *, scale: bool = False):
        # dtype should be a NumPy dtype, e.g. np.float32
        self.dtype = dtype
        self.scale = scale

    def __call__(self, arr: np.ndarray) -> np.ndarray:
        orig_dtype = arr.dtype  # ← capture this first
        # cast (no copy if we don't need one)
        arr = arr.astype(self.dtype, copy=False)
        # if we asked to scale *and* we started from ints, divide by the max
        if self.scale and np.issubdtype(orig_dtype, np.integer):
            max_val = np.iinfo(orig_dtype).max
            arr = arr / max_val
        return arr


class Normalize:
    def __init__(self, mean: Sequence[float], std: Sequence[float]):
        self.mean = np.array(mean, dtype=np.float32).reshape((1, 1, 3))
        self.std = np.array(std, dtype=np.float32).reshape((1, 1, 3))

    def __call__(self, arr: np.ndarray) -> np.ndarray:
        # Ensure array is float32 and in HWC format
        if arr.ndim != 3 or arr.shape[2] != 3:
            raise ValueError("Expected input of shape (H, W, 3)")
        return (arr - self.mean) / self.std
