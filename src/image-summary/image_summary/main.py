import json
import logging
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TypedDict, cast

import typer
from pydantic import DirectoryPath
from rb.api.models import (
    DirectoryInput,
    EnumParameterDescriptor,
    EnumVal,
    FileFilterDirectory,
    InputSchema,
    InputType,
    ParameterSchema,
    ResponseBody,
    TaskSchema,
    TextResponse,
)
from rb.lib.ml_service import MLService
from rb.lib.utils import (
    collect_inline_file_filter,
    extract_filter_id,
    load_saved_filter,
)

from image_summary.model import SUPPORTED_MODELS
from image_summary.process import (
    SUPPORTED_IMAGE_EXTENSIONS,
    ImageSummaryFilePair,
    process_images,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_NAME = "image_summary"


class ImageSummaryInputDirectory(FileFilterDirectory):
    """``input_dir`` must contain at least one supported raster image (see ``process``)."""

    path: DirectoryPath
    file_extensions: list[str] = list(SUPPORTED_IMAGE_EXTENSIONS)


class Inputs(TypedDict):
    input_dir: ImageSummaryInputDirectory
    output_dir: DirectoryInput  # Optional: from chained BatchFileResponse filter


class Parameters(TypedDict):
    model: str


def task_schema() -> TaskSchema:
    input_dir_schema = InputSchema(
        key="input_dir",
        label="Path to the directory containing the input images",
        input_type=InputType.DIRECTORY,
    )
    output_dir_schema = InputSchema(
        key="output_dir",
        label="Path to the directory for the output summaries",
        input_type=InputType.DIRECTORY,
    )
    parameter_schema = ParameterSchema(
        key="model",
        label="Model to use for image description",
        value=EnumParameterDescriptor(
            enum_vals=[
                EnumVal(key=model_id, label=model_info["display_name"])
                for model_id, model_info in SUPPORTED_MODELS.items()
            ],
            default=list(SUPPORTED_MODELS.keys())[0],
        ),
    )
    return TaskSchema(
        inputs=[input_dir_schema, output_dir_schema],
        parameters=[parameter_schema],
    )


server = MLService(APP_NAME)

script_dir = os.path.dirname(os.path.abspath(__file__))
info_file_path = os.path.join(script_dir, "app-info.md")
with open(info_file_path, "r", encoding="utf-8") as f:
    info = f.read()

server.add_app_metadata(
    plugin_name=APP_NAME,
    name="Describe Images",
    author="UMass RescueLab",
    version="3.0.0",
    info=info,
    gpu=True,
    make_threadsafe=False,
)


# Note: filter helper implementations live in `rb.lib.utils` for reuse across plugins.


def summarize_images(
    inputs: Inputs,
    parameters: Parameters,
) -> ResponseBody:
    raw = cast(Mapping[str, Any], inputs)
    input_dir = inputs["input_dir"].path
    output_dir = inputs["output_dir"].path
    model = parameters["model"]
    if "file_filter" in raw:
        files = raw["file_filter"].files
    else:
        files = []
    logger.info("files are %s", files)
    # Use shared helper utilities (from rb.lib.utils) to extract filter id and resolve inputs/output patterns
    filter_id = extract_filter_id(inputs, parameters)
    file_filter = collect_inline_file_filter(inputs, input_dir)
    output_patterns: list[str] = []
    if filter_id:
        saved_inputs, saved_patterns = load_saved_filter(filter_id, input_dir)
        if saved_inputs:
            file_filter = saved_inputs
        if saved_patterns:
            output_patterns = saved_patterns

    has_ff = "file_filter" in raw
    logger.info(
        "ImageSummary API: received request | model=%s | input_dir=%s | output_dir=%s | file_filter=%s",
        model,
        input_dir,
        output_dir,
        has_ff,
    )
    file_pairs = process_images(model, input_dir, output_dir, file_filter)

    # If output patterns were not obtained from a persisted filter, collect them from uploaded files
    if not output_patterns:
        try:
            output_filter_files = raw.get("output_filter").files
        except (AttributeError, KeyError, TypeError):
            output_filter_files = []

        if output_filter_files:
            for pf in output_filter_files:
                try:
                    p = Path(pf.path)
                    if p.exists():
                        content = p.read_text(encoding="utf-8")
                        for line in content.splitlines():
                            line = line.strip()
                            if line:
                                output_patterns.append(line)
                except (OSError, AttributeError, TypeError, UnicodeDecodeError):
                    # Ignore malformed filter files
                    continue

    # If any output patterns provided, filter pairs by summary text content.
    # Preserve processing order (same as pipeline / CLIP order when file_filter is set).
    if output_patterns:
        matched_pairs: list[ImageSummaryFilePair] = []
        for pair in file_pairs:
            out_file = pair["output_path"]
            try:
                txt = Path(out_file).read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for pat in output_patterns:
                if pat in txt:
                    matched_pairs.append(pair)
                    break
        file_pairs = matched_pairs

    result_files = [p["output_path"] for p in file_pairs]

    # file_pairs: explicit input_path → output_path for each artifact (API contract for UIs / pipelines).
    payload = {
        "image_summary": True,
        "input_dir": str(Path(input_dir).resolve()),
        "files": list(result_files),
        "file_pairs": file_pairs,
    }
    response = TextResponse(value=json.dumps(payload))
    logger.info("ImageSummary API: response ready | files=%d", len(result_files))
    return ResponseBody(root=response)


def inputs_cli_parse(input_str: str) -> Inputs:
    input_dir, output_dir = input_str.split(",")
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    if not input_dir.exists():
        raise ValueError("Input directory does not exist.")
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    try:
        return {
            "input_dir": ImageSummaryInputDirectory(path=input_dir),
            "output_dir": DirectoryInput(path=output_dir),
        }
    except Exception as e:
        logger.error("Error parsing CLI inputs: %s", e)
        raise typer.Abort() from e


def parameters_cli_parse(model: str) -> Parameters:
    return {"model": model}


server.add_ml_service(
    rule="/summarize-images",
    ml_function=summarize_images,
    inputs_cli_parser=typer.Argument(
        parser=inputs_cli_parse, help="Input and output directory paths"
    ),
    parameters_cli_parser=typer.Argument(
        parser=parameters_cli_parse, help="Model to use for description"
    ),
    short_title="Describe Images",
    order=0,
    task_schema_func=task_schema,
)

app = server.app

if __name__ == "__main__":
    app()
