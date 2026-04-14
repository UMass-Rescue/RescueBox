from pathlib import Path
from typing import Iterable, List
import logging

from rb.lib.plugin_io import ImageSummaryFilePair

from .model import ensure_model_exists, describe_image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff"}

# Serialize all image-summary work in this process so only one job talks to Ollama at a time.
# (Does not coordinate across multiple API worker processes—use a single worker or external lock.)
#_image_summary_lock = threading.Lock()


def iter_image_files(directory: Path, file_filter: List[Path]) -> Iterable[Path]:
    """
    Yield image paths to process. When ``file_filter`` is non-empty (e.g. pipeline / CLIP order),
    preserve that order. When empty, scan the directory in stable name order.
    """
    directory = directory.resolve()
    if file_filter:
        seen: set[Path] = set()
        for p in file_filter:
            rp = p.resolve()
            if rp in seen:
                continue
            seen.add(rp)
            if (
                rp.is_file()
                and rp.parent.resolve() == directory
                and rp.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
            ):
                yield rp
        return
    for path in sorted(
        (x for x in directory.iterdir() if x.is_file()),
        key=lambda p: p.name.lower(),
    ):
        if path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
            yield path


def process_images(model: str, input_dir: str, output_dir: str, file_filter: List[Path]) -> List[ImageSummaryFilePair]:
    """
    Process images (non-batch path). Runs under the same global lock as
    :func:`process_images_batch` so describe-images never overlaps another job
    in this process.
    """
    #with _image_summary_lock:
    return _process_images_unlocked(model, input_dir, output_dir, file_filter)


def _process_images_unlocked(
    model: str, input_dir: str, output_dir: str, file_filter: List[Path]
) -> List[ImageSummaryFilePair]:
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

    pairs: List[ImageSummaryFilePair] = []
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
            pairs.append(
                {
                    "input_path": str(image_path.resolve()),
                    "output_path": str(out_file.resolve()),
                }
            )
            logger.info(f"ImageSummary: done -> {image_path.name}")
        except Exception as e:
            logger.error(f"ImageSummary: error processing {image_path.name}: {e}")

    if not pairs:
        logger.warning("ImageSummary: no files were processed")
    logger.info(f"ImageSummary: complete | processed={len(pairs)} file(s)")
    return pairs


def process_images_batch(model: str, input_dir: str, output_dir: str, file_filter: List[Path]) -> List[ImageSummaryFilePair]:
    """
    Like :func:`process_images`, but uses chunked multi-image Ollama requests
    (chunk size: env ``IMAGE_SUMMARY_MAX_IMAGES_PER_BATCH``, default 1) with
    concurrent chunks (env ``IMAGE_SUMMARY_BATCH_PARALLEL_WORKERS``), then
    writes one ``.txt`` per image.

    Falls back to per-file :func:`describe_image` for any path still missing a
    description after batching.

    Only one image-summary job runs at a time per process (global lock), so
    concurrent HTTP clients queue here instead of hammering Ollama in parallel.
    """
    # with _image_summary_lock:
    return _process_images_batch_unlocked(model, input_dir, output_dir, file_filter)


def _process_images_batch_unlocked(
    model: str, input_dir: str, output_dir: str, file_filter: List[Path]
) -> List[ImageSummaryFilePair]:
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

    pairs: List[ImageSummaryFilePair] = []
    images = list(iter_image_files(input_path, file_filter))
    logger.info("ImageSummary (batch): discovered %d image(s) to process", len(images))
    path_strs = [str(p) for p in images]

    summaries: dict[str, str] = {}
    if path_strs:
        summaries = {}
        for p in path_strs:
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
            pairs.append(
                {
                    "input_path": str(image_path.resolve()),
                    "output_path": str(out_file.resolve()),
                }
            )
            logger.info("ImageSummary (batch): done -> %s", image_path.name)
        except Exception as e:
            logger.error("ImageSummary (batch): error writing %s: %s", image_path.name, e)

    if not pairs:
        logger.warning("ImageSummary (batch): no files were processed")
    logger.info("ImageSummary (batch): complete | processed=%d file(s)", len(pairs))
    return pairs
