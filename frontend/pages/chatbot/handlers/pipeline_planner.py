"""Pure planning helpers for pipeline step execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rb.api.models import TaskSchema

from frontend.chatbot.multi_tool_handler import (
    batch_items_have_age_gender_metadata,
    chain_output_to_input,
    coerce_pipeline_response,
    extract_batch_file_items,
)


@dataclass
class NextPipelineStepPlan:
    """Prepared data needed to render and submit the next pipeline form."""

    next_endpoint: str
    next_arguments: dict[str, Any]
    items: list[dict[str, Any]]
    has_age_gender_metadata: bool


def plan_next_pipeline_step(
    response_body: Any,
    next_call: dict[str, Any],
    next_schema: TaskSchema | None,
    *,
    coerce_response_fn=coerce_pipeline_response,
    chain_output_fn=chain_output_to_input,
    extract_items_fn=extract_batch_file_items,
    has_metadata_fn=batch_items_have_age_gender_metadata,
) -> NextPipelineStepPlan:
    """Compute next-step arguments and metadata-filter eligibility."""
    response_body = coerce_response_fn(response_body)
    next_endpoint = next_call["endpoint"]
    next_arguments = next_call["arguments"]
    if next_schema:
        next_arguments = chain_output_fn(response_body, next_arguments, next_schema)
    items = extract_items_fn(response_body)
    return NextPipelineStepPlan(
        next_endpoint=next_endpoint,
        next_arguments=next_arguments,
        items=items,
        has_age_gender_metadata=has_metadata_fn(items),
    )


def inject_filtered_paths_into_request(
    request_body: Any, filtered_paths: list[str] | None
) -> Any:
    """Inject file-filter payload for next call when metadata filtering was applied."""
    if filtered_paths is None:
        return request_body
    ff_value = {"files": [{"path": p} for p in filtered_paths]}
    if isinstance(request_body, dict):
        request_body.setdefault("inputs", {})["file_filter"] = ff_value
        return request_body
    inputs = getattr(request_body, "inputs", None)
    if isinstance(inputs, dict):
        inputs["file_filter"] = ff_value
        return request_body
    if inputs is not None:
        inputs.file_filter = ff_value
    return request_body
