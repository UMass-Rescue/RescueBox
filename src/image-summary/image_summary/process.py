from pathlib import Path
from typing import Iterable, List, Set
import logging

from .model import ensure_model_exists, describe_image, describe_images_batch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff"}


def iter_image_files(directory: Path, file_filter: List[Path]) -> Iterable[Path]:
    # Resolve paths so chained pipeline paths match directory.iterdir() reliably.
    allowed = {p.resolve() for p in file_filter}
    for path in directory.iterdir():
        if (
            path.is_file()
            and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
            and path.resolve() in allowed
        ):
            yield path


def process_images(model: str, input_dir: str, output_dir: str, file_filter: List[Path]) -> Set[str]:
    logger.info(
        "ImageSummary: start | model=%s | input_dir=%s | output_dir=%s", model, input_dir, output_dir
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
    images = list(iter_image_files(input_path, file_filter))
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


def process_images_batch(model: str, input_dir: str, output_dir: str, file_filter: List[Path]) -> Set[str]:
    """
    Like :func:`process_images`, but uses chunked multi-image Ollama requests
    (chunk size: env ``IMAGE_SUMMARY_MAX_IMAGES_PER_BATCH``) with up to five
    concurrent chunks (env ``IMAGE_SUMMARY_BATCH_PARALLEL_WORKERS``), then
    writes one ``.txt`` per image.

    Falls back to per-file :func:`describe_image` for any path still missing a
    description after batching.
    """
    logger.info(
        "ImageSummary (batch): start | model=%s | input_dir=%s | output_dir=%s",
        model,
        input_dir,
        output_dir,
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
    images = list(iter_image_files(input_path, file_filter))
    logger.info("ImageSummary (batch): discovered %d image(s) to process", len(images))
    path_strs = [str(p) for p in images]

    summaries: dict[str, str] = {}
    if path_strs:
        try:
            summaries = describe_images_batch(model, path_strs)
        except Exception as e:
            logger.warning(
                "ImageSummary (batch): batch path failed (%s); falling back to per-file.",
                e,
            )
            summaries = {}
        for p in path_strs:
            if not (summaries.get(p) or "").strip():
                try:
                    summaries[p] = describe_image(model, p)
                except Exception as e2:
                    logger.error("ImageSummary (batch): error describing %s: %s", Path(p).name, e2)
                    summaries[p] = ""

    for image_path in images:
        key = str(image_path)
        logger.info("ImageSummary (batch): writing output for -> %s", image_path.name)
        try:
            summary_text = summaries.get(key, "")
            out_file = output_path / (image_path.name + ".txt")
            out_file.write_text(summary_text, encoding="utf-8")
            processed_files.add(str(out_file))
            logger.info("ImageSummary (batch): done -> %s", image_path.name)
        except Exception as e:
            logger.error("ImageSummary (batch): error writing %s: %s", image_path.name, e)

    if not processed_files:
        logger.warning("ImageSummary (batch): no files were processed")
    logger.info("ImageSummary (batch): complete | processed=%d file(s)", len(processed_files))
    return processed_files
