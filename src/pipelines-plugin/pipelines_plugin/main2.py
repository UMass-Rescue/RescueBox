import yaml
import typer
import time
from pathlib import Path
from typing import TypedDict, Any, Dict, List, Callable
from fastapi import HTTPException
import logging

from rb.lib.ml_service import MLService, get_ml_schema_func
from rb.api.models import (
    ResponseBody, TextResponse, TaskSchema, InputType, DirectoryInput, FileInput, TextInput,
    BatchDirectoryInput, BatchFileInput, BatchTextInput, ParameterType
)
from rescuebox_pipeline.rb_celery import app as rb_celery_app
from rescuebox_pipeline.rb_celery import run_pipeline_with_timeout_list
from celery.contrib.abortable import AbortableAsyncResult
from celery.canvas import chain

logger = logging.getLogger(__name__)

# It's better to have a clear way to import the generated pipeline runners
# For now, we will assume they are importable from a known location.
# This might need adjustment based on the project's structure.
import rescuebox_pipeline.rb_pipe as rb_pipeline

APP_NAME = "pipelines"
ml_service = MLService(APP_NAME)

# --- Constants for Type Mapping ---

INPUT_TYPE_MAP = {
    InputType.DIRECTORY: DirectoryInput,
    InputType.FILE: FileInput,
    InputType.TEXT: TextInput,
    InputType.TEXTAREA: TextInput,
    InputType.BATCHDIRECTORY: BatchDirectoryInput,
    InputType.BATCHFILE: BatchFileInput,
    InputType.BATCHTEXT: BatchTextInput,
}

PARAM_TYPE_MAP = {
    ParameterType.RANGED_FLOAT: float,
    ParameterType.FLOAT: float,
    ParameterType.ENUM: str,
    ParameterType.TEXT: str,
    ParameterType.RANGED_INT: int,
    ParameterType.INT: int,
}

# --- Helper Functions for Pipeline Execution ---

def _get_initial_pipeline_arg(schema: TaskSchema, inputs: Dict[str, Any]) -> Any:
    """Extracts the initial argument for the pipeline from the provided inputs based on the schema."""
    if not schema.inputs:
        raise ValueError("Pipeline has no defined inputs.")

    first_input_key = schema.inputs[0].key
    first_input_type = schema.inputs[0].input_type
    
    input_data_obj = inputs.get(first_input_key)
    if not input_data_obj:
        raise ValueError(f"Missing required input '{first_input_key}'.")

    if first_input_type in [InputType.DIRECTORY, InputType.FILE]:
        return input_data_obj.path
    elif first_input_type == InputType.TEXT:
        return input_data_obj.value
    
    raise ValueError(f"Could not determine initial argument for pipeline from input '{first_input_key}'.")

def _execute_pipeline_and_wait(pipeline_tasks: chain, initial_arg: Any, timeout: int = 120) -> (Any, AbortableAsyncResult):
    """Executes a Celery pipeline, waits for the result, and returns the final result and the sub-pipeline result object."""
    # Call the watcher task to execute the pipeline and handle timeouts
    watcher_result = run_pipeline_with_timeout_list.apply_async(
        args=[pipeline_tasks.tasks, initial_arg, timeout],
        serializer='pickle'
    )
    logger.debug(f"Watcher task ID: {watcher_result.id}")

    # Wait for the watcher task to return the ID of the actual pipeline chain
    main_pipeline_result = AbortableAsyncResult(watcher_result.id, app=rb_celery_app)
    sub_pipeline_id = main_pipeline_result.get(timeout=30)
    logger.info(f"Sub-pipeline task ID: {sub_pipeline_id}. Waiting for completion...")

    # Reconstruct the AsyncResult object for the sub-pipeline and wait for its final result
    sub_pipeline_result = AbortableAsyncResult(sub_pipeline_id, app=rb_celery_app)
    final_result = sub_pipeline_result.get(timeout=timeout + 10) # Add a grace period
    
    return final_result, sub_pipeline_result

def _log_pipeline_task_chain(pipeline_result: AbortableAsyncResult):
    """Walks a completed pipeline chain backwards and logs the details of each task."""
    logger.info("--- Pipeline Task Details ---")
    current_task_result = pipeline_result
    while current_task_result:
        try:
            task_state = current_task_result.state
            task_id = current_task_result.id
            logger.info(f"  - Task ID: {task_id}, State: {task_state}")
            current_task_result = current_task_result.parent
        except Exception as e:
            logger.warning(f"Could not retrieve details for a parent task: {e}")
            current_task_result = None
    logger.info("-----------------------------")

# --- Dynamic Function and Schema Generation ---

def create_dynamic_parser_func(schema_items: list, is_input: bool) -> Callable:
    """Creates a parser function with a dynamic signature for either inputs or parameters."""
    # ... (Implementation remains the same as it's already modular)
    arg_defs = []
    for item in schema_items:
        key = item.key
        if is_input:
            arg_defs.append(f"{key}: str")
        else:
            default = item.value.default
            cli_type_name = PARAM_TYPE_MAP.get(item.value.parameter_type, Any).__name__
            arg_defs.append(f'{key}: {cli_type_name} = {repr(default)}')

    func_sig = f"def parser({', '.join(arg_defs)}):"
    body_lines = ["return {"]
    if is_input:
        for item in schema_items:
            model_type = INPUT_TYPE_MAP.get(item.input_type)
            if model_type in [DirectoryInput, FileInput, BatchDirectoryInput, BatchFileInput]:
                body_lines.append(f"    '{item.key}': {model_type.__name__}(path={item.key}),")
            else:
                body_lines.append(f"    '{item.key}': {model_type.__name__}(value={item.key}),")
    else:
        for item in schema_items:
            body_lines.append(f"    '{item.key}': {item.key},")
    body_lines.append("}")
    func_body = "\n    ".join(body_lines)

    exec_globals = { 'DirectoryInput': DirectoryInput, 'FileInput': FileInput, 'TextInput': TextInput, 'BatchDirectoryInput': BatchDirectoryInput, 'BatchFileInput': BatchFileInput, 'BatchTextInput': BatchTextInput }
    local_scope = {}
    exec(func_sig + "\n    " + func_body, exec_globals, local_scope)
    return local_scope['parser']

def create_composite_schema_func(p_def: Dict[str, Any]) -> Callable[[], TaskSchema]:
    """Creates a function that generates a composite TaskSchema for a full pipeline."""
    # ... (Implementation remains the same)
    def composite_schema_func() -> TaskSchema:
        final_inputs = []
        final_params = []
        processed_keys = set()
        if p_def['tasks']:
            first_task_service = p_def['tasks'][0]['service']
            first_schema_func = get_ml_schema_func(first_task_service)
            if first_schema_func:
                first_schema = first_schema_func()
                for i in first_schema.inputs:
                    if i.key not in processed_keys:
                        final_inputs.append(i)
                        processed_keys.add(i.key)
            else:
                logger.warning(f"Schema for first task '{first_task_service}' not found.")
                return TaskSchema(inputs=[], parameters=[])
        for task_def in p_def['tasks']:
            service_name = task_def['service']
            schema_func = get_ml_schema_func(service_name)
            if not schema_func: continue
            task_schema = schema_func()
            default_params = task_def.get('parameters', {})
            for param in task_schema.parameters:
                if param.key in processed_keys: continue
                processed_keys.add(param.key)
                if param.key in default_params:
                    try:
                        param.value.default = default_params[param.key]
                    except AttributeError:
                        logger.warning(f"Could not set default for param '{param.key}'.")
                final_params.append(param)
        return TaskSchema(inputs=final_inputs, parameters=final_params)
    return composite_schema_func

def create_pipeline_trigger(p_def: Dict[str, Any], schema: TaskSchema) -> Callable:
    """
    Creates the main trigger function for a specific pipeline definition.
    This function will be executed when the corresponding API endpoint is called.
    """
    p_name = p_def['name']
    
    def trigger_pipeline(inputs: Dict[str, Any], parameters: Dict[str, Any]) -> ResponseBody:
        """The actual function that executes the pipeline when triggered."""
        try:
            pipeline_tasks_func = getattr(rb_pipeline, f"run_{p_name}_pipeline", None)
            if not pipeline_tasks_func:
                raise ValueError(f"Pipeline runner for '{p_name}' not found.")

            initial_arg = _get_initial_pipeline_arg(schema, inputs)
            pipeline_chain = pipeline_tasks_func()

            final_result, sub_pipeline_result = _execute_pipeline_and_wait(pipeline_chain, initial_arg)
            logger.debug(f"Final pipeline result: {final_result}")

            _log_pipeline_task_chain(sub_pipeline_result)

            if isinstance(final_result, str):
                return ResponseBody(root=TextResponse(value=final_result))
            else:
                return ResponseBody(root=TextResponse(value=f"Task {sub_pipeline_result.id} completed with result: {str(final_result)}"))

        except Exception as e:
            logger.error(f"Pipeline execution failed: {repr(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {repr(e)}")
            
    return trigger_pipeline

def generate_and_register_pipeline(pipeline_def: Dict[str, Any], ml_service: MLService):
    """
    Takes a pipeline definition, generates all necessary components (schema, parsers, trigger),
    and registers it as an ML service endpoint.
    """
    pipeline_name = pipeline_def['name']
    short_title = pipeline_def['short_title']

    # 1. Create the composite schema function and the schema itself.
    schema_func = create_composite_schema_func(pipeline_def)
    schema = schema_func()

    # 2. Create dynamic types and CLI parsers based on the schema.
    input_fields = {inp.key: INPUT_TYPE_MAP.get(inp.input_type, Any) for inp in schema.inputs}
    param_fields = {p.key: PARAM_TYPE_MAP.get(p.value.parameter_type, Any) for p in schema.parameters}
    InputsType = TypedDict(f"{pipeline_name}Inputs", input_fields)
    ParamsType = TypedDict(f"{pipeline_name}Params", param_fields)
    inputs_parser = create_dynamic_parser_func(schema.inputs, is_input=True)
    params_parser = create_dynamic_parser_func(schema.parameters, is_input=False)

    # 3. Create the main pipeline trigger function.
    pipeline_trigger_func = create_pipeline_trigger(pipeline_def, schema)

    # 4. Register the fully constructed pipeline as an ML service.
    ml_service.add_ml_service(
        rule=f"/{pipeline_name}",
        ml_function=pipeline_trigger_func,
        inputs_cli_parser=typer.Argument(None, parser=inputs_parser),
        parameters_cli_parser=typer.Option(None, parser=params_parser),
        task_schema_func=schema_func,
        short_title=short_title,
    )
    logger.info(f"Successfully registered pipeline: '{pipeline_name}'")

def main():
    """Main function to load configurations and register all pipelines."""
    ml_service.add_app_metadata(
        name="Pipelines Orchestrator",
        author="RescueBox Team",
        version="0.1.0",
        info="A plugin to define and run multi-step pipelines of other ML services.",
        plugin_name=APP_NAME,
    )

    try:
        pipeline_file = Path(__file__).resolve().parent / "pipelines.yaml"
        with open(pipeline_file, 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        logger.error("CRITICAL: pipelines.yaml not found. No pipelines will be loaded.")
        return

    pipelines = config.get('pipelines', [])
    if not pipelines:
        logger.warning("No pipelines defined in pipelines.yaml.")
        return

    for pipeline_def in pipelines:
        try:
            generate_and_register_pipeline(pipeline_def, ml_service)
        except Exception as e:
            pipeline_name = pipeline_def.get('name', 'unknown')
            logger.error(f"Failed to register pipeline '{pipeline_name}': {repr(e)}", exc_info=True)

# --- Application Entry Point ---
if __name__ == "__main__":
    main()

app = ml_service.app
