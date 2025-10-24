"""Perceptual hashing module using the perception library."""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

import numpy as np
from PIL import Image
from perception import hashers

logger = logging.getLogger(__name__)

# Supported image extensions
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}

# Video extensions (for future support)
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}


class PerceptualHasher:
    """Perceptual hash generator using the Thorn perception library."""

    def __init__(self, hash_algorithm: str = "phash"):
        """
        Initialize the hasher with a specific algorithm.

        Args:
            hash_algorithm: Hash algorithm to use ('phash', 'average', 'dhash', 'wavelet', 'pdq')
        """
        self.hash_algorithm = hash_algorithm.lower()

        # Initialize the appropriate hasher based on algorithm
        if self.hash_algorithm == "phash" or self.hash_algorithm == "perceptual":
            self.hasher = hashers.PHash()
        elif self.hash_algorithm == "average":
            self.hasher = hashers.AverageHash()
        elif self.hash_algorithm == "dhash" or self.hash_algorithm == "difference":
            self.hasher = hashers.DHash()
        elif self.hash_algorithm == "wavelet":
            self.hasher = hashers.WaveletHash()
        elif self.hash_algorithm == "pdq":
            self.hasher = hashers.PDQ()
        else:
            raise ValueError(
                f"Unsupported hash algorithm: {hash_algorithm}. "
                f"Supported: phash, average, dhash, wavelet, pdq"
            )

    def compute_hash(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Compute perceptual hash for a single file.
        
        Args:
            file_path: Path to the image/video file
            
        Returns:
            Dictionary with 'hash_vector', 'hash_string', and 'file_path' or None if error
        """
        try:
            file_path = str(file_path)
            ext = Path(file_path).suffix.lower()
            
            if ext in IMAGE_EXTENSIONS:
                return self._compute_image_hash(file_path)
            elif ext in VIDEO_EXTENSIONS:
                # Video support can be added later
                logger.warning(f"Video hashing not yet implemented for {file_path}")
                return None
            else:
                logger.warning(f"Unsupported file type: {file_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error computing hash for {file_path}: {e}")
            return None

    def _compute_image_hash(self, file_path: str) -> Dict[str, Any]:
        """
        Compute hash for an image file.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Dictionary with hash information
        """
        # Compute the hash using the perception library
        hash_value = self.hasher.compute(file_path)
        
        # Convert hash to string representation
        hash_string = str(hash_value)
        
        # Convert to vector for ChromaDB
        # The perception library returns different types for different hashers
        # We need to convert to a consistent vector format
        hash_vector = self._hash_to_vector(hash_value)
        
        return {
            "hash_vector": hash_vector,
            "hash_string": hash_string,
            "file_path": file_path,
        }

    def _hash_to_vector(self, hash_value) -> List[float]:
        """
        Convert a hash value to a vector suitable for database storage.

        Args:
            hash_value: Hash value from perception library

        Returns:
            List of floats representing the hash as a vector
        """
        import base64

        # PDQ returns a numpy array directly
        if isinstance(hash_value, np.ndarray):
            # Flatten in case it's multidimensional
            return hash_value.flatten().astype(float).tolist()

        # The perception library hash objects have a hash attribute that's an integer
        # We need to convert this integer to a binary vector
        if hasattr(hash_value, 'hash'):
            hash_int = hash_value.hash
            # Convert to 64-bit binary representation (standard for perceptual hashes)
            binary_str = format(hash_int, '064b')
            return [float(bit) for bit in binary_str]

        # Try to get the integer value directly if it's an integer-like object
        try:
            hash_int = int(hash_value)
            # Convert to 64-bit binary representation
            binary_str = format(hash_int, '064b')
            return [float(bit) for bit in binary_str]
        except (ValueError, TypeError):
            pass

        # The perception library returns base64-encoded strings for hash values
        # Try to decode as base64 first
        hash_str = str(hash_value)
        try:
            # Decode base64 to get the raw hash bytes
            hash_bytes = base64.b64decode(hash_str)
            # Convert each byte to 8 bits (creates 64-bit vector for 8-byte hash)
            binary_str = ''.join(format(byte, '08b') for byte in hash_bytes)
            return [float(bit) for bit in binary_str]
        except Exception:
            # If base64 decoding fails, continue to other methods
            pass

        # For string-based hashes (like average, difference, perceptual)
        # Convert the binary string to a list of floats (0.0 or 1.0)
        # Remove any non-binary characters
        binary_str = ''.join(c for c in hash_str if c in '01')

        if binary_str:
            return [float(bit) for bit in binary_str]

        # Fallback: if we can't parse it, try to convert to bytes and then to floats
        try:
            hash_bytes = hash_value if isinstance(hash_value, bytes) else str(hash_value).encode()
            # Ensure we have at least 64 dimensions
            byte_list = [float(b) / 255.0 for b in hash_bytes]
            # Pad or truncate to 64 dimensions
            if len(byte_list) < 64:
                byte_list.extend([0.0] * (64 - len(byte_list)))
            return byte_list[:64]
        except:
            # Last resort: create a 64-dimensional vector from the string representation
            hash_str = str(hash_value)
            vector = [float(ord(c)) / 255.0 for c in hash_str[:64]]
            # Pad to 64 dimensions if needed
            if len(vector) < 64:
                vector.extend([0.0] * (64 - len(vector)))
            return vector[:64]

    def compute_directory_hashes(
        self,
        directory_path: str,
        recursive: bool = True,
        progress_callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Compute hashes for all supported files in a directory.
        
        Args:
            directory_path: Path to directory
            recursive: Whether to search recursively
            progress_callback: Optional callback function(current, total) for progress updates
            
        Returns:
            List of hash dictionaries
        """
        directory_path = Path(directory_path)
        
        # Find all supported files
        supported_files = []
        if recursive:
            for ext in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS:
                supported_files.extend(directory_path.rglob(f"*{ext}"))
        else:
            for ext in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS:
                supported_files.extend(directory_path.glob(f"*{ext}"))
        
        # Compute hashes
        hashes = []
        total = len(supported_files)
        
        for idx, file_path in enumerate(supported_files):
            hash_data = self.compute_hash(str(file_path))
            if hash_data:
                hashes.append(hash_data)
            
            # Progress callback
            if progress_callback:
                progress_callback(idx + 1, total)
        
        logger.info(
            f"Computed {len(hashes)} hashes from {total} files "
            f"in {directory_path} using {self.hash_algorithm}"
        )
        
        return hashes

    def compute_batch_hashes(
        self,
        file_paths: List[str],
        progress_callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Compute hashes for a batch of files.
        
        Args:
            file_paths: List of file paths
            progress_callback: Optional callback function(current, total) for progress updates
            
        Returns:
            List of hash dictionaries
        """
        hashes = []
        total = len(file_paths)
        
        for idx, file_path in enumerate(file_paths):
            hash_data = self.compute_hash(file_path)
            if hash_data:
                hashes.append(hash_data)
            
            # Progress callback
            if progress_callback:
                progress_callback(idx + 1, total)
        
        logger.info(f"Computed {len(hashes)} hashes from {total} files using {self.hash_algorithm}")
        
        return hashes

    @staticmethod
    def get_supported_algorithms() -> List[str]:
        """Get list of supported hash algorithms."""
        return ["phash", "average", "dhash", "wavelet", "pdq"]

    @staticmethod
    def get_algorithm_info(algorithm: str) -> Dict[str, str]:
        """
        Get information about a hash algorithm.
        
        Args:
            algorithm: Hash algorithm name
            
        Returns:
            Dictionary with algorithm information
        """
        info = {
            "phash": {
                "name": "Perceptual Hash (pHash)",
                "description": "DCT-based hash, robust to various transformations",
                "best_for": "Finding perceptually similar images with modifications",
            },
            "perceptual": {
                "name": "Perceptual Hash (pHash)",
                "description": "DCT-based hash, robust to various transformations",
                "best_for": "Finding perceptually similar images with modifications",
            },
            "average": {
                "name": "Average Hash",
                "description": "Simple and fast hash based on average pixel values",
                "best_for": "Quick duplicate detection with minimal changes",
            },
            "dhash": {
                "name": "Difference Hash (dHash)",
                "description": "Hash based on gradient/difference between adjacent pixels",
                "best_for": "Detecting similar images with different brightness/contrast",
            },
            "difference": {
                "name": "Difference Hash (dHash)",
                "description": "Hash based on gradient/difference between adjacent pixels",
                "best_for": "Detecting similar images with different brightness/contrast",
            },
            "wavelet": {
                "name": "Wavelet Hash",
                "description": "Haar wavelet-based hash for robust image comparison",
                "best_for": "Finding similar images with complex transformations",
            },
            "pdq": {
                "name": "PDQ Hash",
                "description": "Facebook's PDQ perceptual hash designed for large-scale image matching",
                "best_for": "Production-grade duplicate and near-duplicate detection at scale",
            },
        }
        return info.get(algorithm.lower(), {"name": algorithm, "description": "Unknown algorithm"})
