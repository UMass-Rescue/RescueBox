from pathlib import Path
from typing import Iterable, Set, Callable
import logging

from .model import ensure_model_exists, describe_image, describe_image_json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff"}


def iter_image_files(directory: Path) -> Iterable[Path]:
    for path in directory.iterdir():
        if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
            yield path


def _process_images_generic(
    *,
    model: str,
    input_dir: str,
    output_dir: str,
    generate: Callable[[str, str], str],
    output_extension: str,
    log_prefix: str,
    generation_label: str,
) -> Set[str]:
    logger.info(
        f"{log_prefix}: start | model={model} | input_dir={input_dir} | output_dir={output_dir}"
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
    logger.info(f"{log_prefix}: discovered {len(images)} image(s) to process")
    for image_path in images:
        logger.info(f"{log_prefix}: processing -> {image_path.name}")
        try:
            logger.info(
                f"{log_prefix}: generating {generation_label} with model={model}"
            )
            generated_text = generate(model, str(image_path))
            out_file = output_path / (image_path.name + output_extension)
            logger.info(f"{log_prefix}: writing output -> {out_file.name}")
            out_file.write_text(generated_text, encoding="utf-8")
            processed_files.add(str(out_file))
            logger.info(f"{log_prefix}: done -> {image_path.name}")
        except Exception as e:
            logger.error(f"{log_prefix}: error processing {image_path.name}: {e}")

    if not processed_files:
        logger.warning(f"{log_prefix}: no files were processed")
    logger.info(f"{log_prefix}: complete | processed={len(processed_files)} file(s)")
    return processed_files


def process_images(model: str, input_dir: str, output_dir: str) -> Set[str]:
    return _process_images_generic(
        model=model,
        input_dir=input_dir,
        output_dir=output_dir,
        generate=describe_image,
        output_extension=".txt",
        log_prefix="ImageSummary",
        generation_label="description",
    )


def process_images_json(model: str, input_dir: str, output_dir: str) -> Set[str]:
    return _process_images_generic(
        model=model,
        input_dir=input_dir,
        output_dir=output_dir,
        generate=describe_image_json,
        output_extension=".json",
        log_prefix="ImageSummary(JSON)",
        generation_label="JSON",
    )
