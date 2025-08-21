from pathlib import Path
from typing import Iterable, Set
import logging

from .model import ensure_model_exists, describe_image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff"}


def iter_image_files(directory: Path) -> Iterable[Path]:
    for path in directory.iterdir():
        if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
            yield path


def process_images(model: str, input_dir: str, output_dir: str) -> Set[str]:
    logger.info(
        f"ImageSummary: start | model={model} | input_dir={input_dir} | output_dir={output_dir}"
    )
    ensure_model_exists(model)
    input_path = Path(input_dir)
    if not input_path.exists():
        raise ValueError(f"Input directory '{input_dir}' does not exist.")
    if not input_path.is_dir():
        raise ValueError(f"Input directory '{input_dir}' is not a directory.")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    processed_files: Set[str] = set()
    images = list(iter_image_files(input_path))
    logger.info(f"ImageSummary: discovered {len(images)} image(s) to process")
    for image_path in images:
        logger.info(f"ImageSummary: processing -> {image_path.name}")
        try:
            logger.info(f"ImageSummary: generating description with model={model}")
            summary_text = describe_image(model, str(image_path))
            # Include the original filename with extension to avoid collisions
            out_file = output_path / (image_path.name + ".txt")
            logger.info(f"ImageSummary: writing output -> {out_file.name}")
            out_file.write_text(summary_text, encoding="utf-8")
            processed_files.add(str(out_file))
            logger.info(f"ImageSummary: done -> {image_path.name}")
        except Exception as e:
            logger.error(f"ImageSummary: error processing {image_path.name}: {e}")

    if not processed_files:
        logger.warning("ImageSummary: no files were processed")
    logger.info(f"ImageSummary: complete | processed={len(processed_files)} file(s)")
    return processed_files
