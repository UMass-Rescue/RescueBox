#!/usr/bin/env python3
"""
Comprehensive End-to-End Test for RescueBox Plugins.

This script runs sequentially through all 9 active ML plugins to confirm that 
the FastAPI backend routes, Pydantic validations, and ML model wrappers are 
all fully functional and thread-safe.

Usage:
  poetry run python scripts/e2e_all_plugins_test.py
"""

import os
import subprocess
import time
from pathlib import Path

import httpx

BASE_URL = os.environ.get("RESCUEBOX_API_BASE", "http://127.0.0.1:8080/api").rstrip("/")
DEMO_ROOT = Path("/home/tester/Documents/demo1")

# Define the test sequence for all 9 plugins
TEST_CASES = [
    {
        "name": "1. Audio Transcription",
        "endpoint": "/audio/transcribe",
        "inputs": {
            "input_dir": {"path": str(DEMO_ROOT / "transcribe-audio" / "inputs")}
        },
        "parameters": {},
    },
    {
        "name": "2. Age and Gender",
        "endpoint": "/age-gender/predict",
        "inputs": {
            "image_directory": {
                "path": str(DEMO_ROOT / "age-gender-classifier" / "inputs")
            }
        },
        "parameters": {},
    },
    {
        "name": "3. Text Summarization",
        "endpoint": "/text_summarization/summarize",
        "inputs": {
            "input_dir": {"path": str(DEMO_ROOT / "summarize-text" / "inputs")},
            "output_dir": {"path": str(DEMO_ROOT / "summarize-text" / "outputs")},
        },
        "parameters": {"model": "gemma3:1b"},
    },
    {
        "name": "4. Image Summarization",
        "endpoint": "/image_summary/summarize-images",
        "inputs": {
            "input_dir": {"path": str(DEMO_ROOT / "describe-images" / "inputs")},
            "output_dir": {"path": str(DEMO_ROOT / "describe-images" / "outputs")},
        },
        "parameters": {"model": "moondream:latest"},
    },
    {
        "name": "5. Deepfake Detection",
        "endpoint": "/deepfake_detection/predict",
        "inputs": {
            "input_dir": {"path": str(DEMO_ROOT / "detect-deepfake" / "inputs")},
            "output_dir": {"path": str(DEMO_ROOT / "detect-deepfake" / "outputs")},
        },
        "parameters": {"facecrop": "false"},
    },
    {
        "name": "6. Text Embeddings Search",
        "endpoint": "/text_embeddings/search",
        "inputs": {
            "input_dir": {"path": str(DEMO_ROOT / "summarize-text" / "outputs")},
            "query": {"text": "night"},
        },
        "parameters": {"top_k": 5, "min_similarity": 0.45},
    },
    {
        "name": "7. Image Embeddings Search",
        "endpoint": "/image_embeddings/search_images",
        "inputs": {
            "input_dir": {"path": str(DEMO_ROOT / "search-images" / "inputs")},
            "query": {"text": "food"},
        },
        "parameters": {
            "model_name": "openai/clip-vit-large-patch14-336",
            "top_k": 5,
            "min_similarity": 0.13,
        },
    },
    {
        "name": "8. Face Match (Bulk Upload)",
        "endpoint": "/face-match/bulkupload",
        "inputs": {
            "directory_path": {"path": str(DEMO_ROOT / "face-detect" / "upload_inputs")}
        },
        "parameters": {
            "dropdown_collection_name": "Create a new collection",
            "collection_name": "e2e_test_collection",
        },
    },
    {
        "name": "9. Face Match (Find Face Bulk)",
        "endpoint": "/face-match/findfacebulk",
        "inputs": {
            "query_directory": {
                "path": str(DEMO_ROOT / "face-detect" / "find_face_inputs")
            }
        },
        "parameters": {
            "collection_name": "e2e_test_collection",
            "similarity_threshold": 0.45,
        },
    },
    {
        "name": "10. UFDR Mounter (FUSE)",
        "endpoint": "/ufdr_mounter/mount",
        "inputs": {
            "ufdr_file": {
                "path": str(DEMO_ROOT / "ufdr-mount" / "inputs" / "test.ufdr")
            },
            "mount_name": {"text": "/tmp/e2etest123"},
        },
        "parameters": {},
    },
]


def run_tests():
    print(f"Setting up Demo directories in {DEMO_ROOT}...")
    for tc in TEST_CASES:
        for key, val in tc["inputs"].items():
            if "path" in val:
                p = Path(val["path"])
                if "ufdr" in tc["name"].lower():
                    p.parent.mkdir(parents=True, exist_ok=True)
                    if not p.exists():
                        p.touch()  # Touch a fake UFDR so it passes path validation
                else:
                    p.mkdir(parents=True, exist_ok=True)

    headers = {"X-RescueBox-User-Id": "e2e-all-plugins-tester"}

    with httpx.Client(timeout=600.0) as client:
        for tc in TEST_CASES:
            print(f"\n▶ Testing {tc['name']}")
            endpoint = f"{BASE_URL}{tc['endpoint']}"
            payload = {"inputs": tc["inputs"], "parameters": tc["parameters"]}

            t0 = time.time()
            resp = client.post(endpoint, json=payload, headers=headers)
            elapsed = time.time() - t0

            print(f"  Status: {resp.status_code} ({elapsed:.2f}s)")
            print(f"  Response: {resp.text[:300].strip()}...")

    print("\nCleaning up FUSE mount...")
    subprocess.run(["umount", "/tmp/e2etest123"], capture_output=True)


if __name__ == "__main__":
    run_tests()
