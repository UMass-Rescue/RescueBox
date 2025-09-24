import yaml
import typer
import time
from pathlib import Path
from typing import TypedDict, Any, Dict
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
from celery import chain
from celery.contrib.abortable import AsyncResult

logger = logging.getLogger(__name__)
# It's better to have a clear way to import the generated pipeline runners
# For now, we will assume they are importable from a known location.
# This might need adjustment based on the project's structure.

import rescuebox_pipeline.rb_pipe as rb_pipeline

APP_NAME = "pipelines"
ml_service = MLService(APP_NAME)

ml_service.add_app_metadata(
    name="Pipelines Orchestrator",
    author="RescueBox Team",
    version="0.1.0",
    info="A plugin to define and run multi-step pipelines of other ML services.",
    plugin_name=APP_NAME,
)

# --- Type Mapping ---
# Map schema input types to Pydantic model types
INPUT_TYPE_MAP = {
    InputType.DIRECTORY: DirectoryInput,
    InputType.FILE: FileInput,
    InputType.TEXT: TextInput,
    InputType.TEXTAREA: TextInput,
    InputType.BATCHDIRECTORY: BatchDirectoryInput,
    InputType.BATCHFILE: BatchFileInput,
    InputType.BATCHTEXT: BatchTextInput,
}

# Map schema parameter types to Python types for CLI parsing
PARAM_TYPE_MAP = {
    ParameterType.RANGED_FLOAT: float,
    ParameterType.FLOAT: float,
    ParameterType.ENUM: str,
    ParameterType.TEXT: str,
    ParameterType.RANGED_INT: int,
    ParameterType.INT: int,
}


def create_dynamic_parser_func(schema_items: list, is_input: bool):
    """Creates a parser function with a dynamic signature for either inputs or parameters."""
    arg_defs = []
    print("------------------------------------------------")
    logger.debug(f"------------------------------------------------")
    for item in schema_items:
        key = item.key
        if is_input:
            # Inputs are positional arguments on the CLI, assume string type (e.g., path)
            arg_defs.append(f"{key}: str")
        else:
            # Parameters are options with defaults
            default = item.value.default
            cli_type_name = PARAM_TYPE_MAP.get(item.value.parameter_type, Any).__name__
            if isinstance(default, str):
                arg_defs.append(f"{key}: {cli_type_name} = '{default}'")
            else:
                arg_defs.append(f"{key}: {cli_type_name} = {default}")

    func_sig = f"def parser({', '.join(arg_defs)}):"

    # Build the function body that constructs the dictionary
    if is_input:
        body_lines = [
            "return {"
        ]
        for item in schema_items:
            key = item.key
            model_type = INPUT_TYPE_MAP.get(item.input_type)
            if model_type in [DirectoryInput, FileInput, BatchDirectoryInput, BatchFileInput]:
                body_lines.append(f"    '{key}': {model_type.__name__}(path={key}),")
            elif model_type in [TextInput, BatchTextInput]:
                body_lines.append(f"    '{key}': {model_type.__name__}(value={key}),")
        body_lines.append("}")
    else: # Parameters are simpler, just return the values
        body_lines = [
            "return {"
        ]
        for item in schema_items:
            body_lines.append(f"    '{item.key}': {item.key},")
        body_lines.append("}")

    func_body = "\n    ".join(body_lines)

    # Use exec to create the function in a controlled scope
    exec_globals = {
        'DirectoryInput': DirectoryInput, 'FileInput': FileInput, 'TextInput': TextInput,
        'BatchDirectoryInput': BatchDirectoryInput, 'BatchFileInput': BatchFileInput, 'BatchTextInput': BatchTextInput
    }
    local_scope = {}
    exec(func_sig + "\n    " + func_body, exec_globals, local_scope)
    return local_scope['parser']


# Load pipeline definitions
try:
    pipelinefile  =Path(__file__).resolve().parent / "pipelines.yaml"
    print(f"debug pipelinefile: {pipelinefile}")
    with open(pipelinefile, 'r') as f:
        config = yaml.safe_load(f)
    print(f"debug pipeline yaml config: {config}")
except FileNotFoundError:
    config = {}
    print("Warning: pipelines.yaml not found. No pipelines will be loaded.")
    raise ValueError("pipelines.yaml not found.")

for pipeline_def in config.get('pipelines', []):
    pipeline_name = pipeline_def['name']
    short_title = pipeline_def['short_title']

    # --- Composite Schema Generation ---
    def create_composite_schema_func(p_def):
        def composite_schema_func() -> TaskSchema:
            final_inputs = []
            final_params = []
            processed_keys = set()

            # 1. Get inputs from the first task.
            if p_def['tasks']:
                first_task_service = p_def['tasks'][0]['service']
                first_schema_func = get_ml_schema_func(first_task_service)
                print(f"debug first_schema_func: {first_schema_func}")
                if first_schema_func:
                    first_schema = first_schema_func()
                    for i in first_schema.inputs:
                        if i.key not in processed_keys:
                            final_inputs.append(i)
                            processed_keys.add(i.key)
                else:
                    print(f"Warning: Schema for first task '{first_task_service}' not found.")
                    return TaskSchema(inputs=[], parameters=[])

            # 2. Iterate through all tasks to collect parameters.
            for task_def in p_def['tasks']:
                service_name = task_def['service']
                schema_func = get_ml_schema_func(service_name)
                if not schema_func: continue

                task_schema = schema_func()
                print(f"debug task_schema: {task_schema}")
                default_params = task_def.get('parameters', {})

                for param in task_schema.parameters:
                    if param.key in processed_keys: continue
                    processed_keys.add(param.key)

                    if param.key in default_params:
                        try:
                            param.value.default = default_params[param.key]
                        except AttributeError:
                            print(f"Warning: Could not set default for param '{param.key}'.")
                    
                    final_params.append(param)
            print(f"debug final_inputs: {final_inputs}")
            print(f"debug final_params: {final_params}")
            print("------------------------------------------------")
            return TaskSchema(inputs=final_inputs, parameters=final_params)
        print(f"debug composite_schema_func: {composite_schema_func}")
        print("------------------------------------------------")
        return composite_schema_func

    # --- Dynamically create types and parsers ---
    schema_func = create_composite_schema_func(pipeline_def)
    print(f"debug schema_func: {schema_func}")
    schema = schema_func()

    input_fields = {inp.key: INPUT_TYPE_MAP.get(inp.input_type, Any) for inp in schema.inputs}
    param_fields = {p.key: PARAM_TYPE_MAP.get(p.value.parameter_type, Any) for p in schema.parameters}

    InputsType = TypedDict(f"{pipeline_name}Inputs", input_fields)
    ParamsType = TypedDict(f"{pipeline_name}Params", param_fields)

    inputs_parser = create_dynamic_parser_func(schema.inputs, is_input=True)
    params_parser = create_dynamic_parser_func(schema.parameters, is_input=False)

    # --- Pipeline Trigger Function ---
    def create_pipeline_trigger(p_def, inputs_type, params_type):
        p_name = p_def['name']
        def trigger_pipeline(inputs: inputs_type, parameters: params_type) -> ResponseBody:
            if not rb_pipeline:
                return ResponseBody(root=TextResponse(value="Error: rb_pipeline module not available."))

            pipeline_tasks = getattr(rb_pipeline, f"run_{p_name}_pipeline", None)
            print(f"debug pipeline_tasks: {pipeline_tasks}")
            if not pipeline_tasks:
                return ResponseBody(root=TextResponse(value=f"Error: Pipeline runner for '{p_name}' not found."))

            # Dynamically construct the initial arguments for the celery chain based on the schema.
            if not p_def['tasks'] or not schema.inputs:
                 return ResponseBody(root=TextResponse(value=f"Error: Pipeline '{p_name}' has no inputs."))

            first_input_key = schema.inputs[0].key
            first_input_type = schema.inputs[0].input_type
            
            input_data_obj = inputs.get(first_input_key)
            if not input_data_obj:
                return ResponseBody(root=TextResponse(value=f"Error: Missing required input '{first_input_key}'."))

            initial_arg = None
            if first_input_type in [InputType.DIRECTORY, InputType.FILE]:
                initial_arg = input_data_obj.path
                # do not use initial_arg = str(input_data_obj.path)
            elif first_input_type == InputType.TEXT:
                initial_arg = input_data_obj.value
            
            if initial_arg is None:
                return ResponseBody(root=TextResponse(value=f"Error: Could not determine initial argument for pipeline from input '{first_input_key}'."))

            # This is also a simplification. We would need to pass the parameters
            # to the correct celery task in the chain, which the current generator doesn't fully support.
            logger.debug(f"-------\"{pipeline_tasks}\"----")
            pipeline_chain = pipeline_tasks()
            
            
            #pipeline_chains = chain(*pipeline_tasks)

            print("Applying chain...")
            

            # Call the watcher task to execute the pipeline and handle timeouts
            watcher_result = run_pipeline_with_timeout_list.apply_async(
                args=[pipeline_chain.tasks,initial_arg, 20], # Pass the list of tasks in the chain (increased timeout to 120 seconds)
                serializer='pickle'
            )
            
            logger.debug(f"Watcher task ID: {watcher_result.id}")
            
            # The watcher task itself will handle the timeout, so we just wait for its result
            main_pipeline_result = AbortableAsyncResult(watcher_result.id, app=rb_celery_app)
            logger.debug(f"run_pipeline_with_timeout_list id : {main_pipeline_result.id}")
            
            try:
                # The watcher returns the ID of the actual pipeline chain
                sub_pipeline_id = main_pipeline_result.get(timeout=30)
                logger.info(f"Sub-pipeline task ID: {sub_pipeline_id}. Waiting for completion...")

                # Reconstruct the AsyncResult object
                sub_pipeline_result = AbortableAsyncResult(sub_pipeline_id, app=rb_celery_app)

                # Now, wait for the sub-pipeline to complete to get the final result
                final_result = sub_pipeline_result.get(timeout=40) # Adjust timeout as needed
                
                logger.debug(f"Final pipeline result: {final_result}")

                # Walk the chain backwards to log all parent task IDs and states
                logger.info("--- Pipeline Task Details ---")
                current_task_result = sub_pipeline_result
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

                if isinstance(final_result, str):
                    return ResponseBody(root=TextResponse(value=final_result))

                # Fallback for other result types
                return ResponseBody(root=TextResponse(value=f"Task {sub_pipeline_id} completed with result: {str(final_result)}"))

            except Exception as e:
                try:
                    # Try to decode the exception message safely
                    error_message = str(e)
                except UnicodeDecodeError:
                    # If it fails, represent it with repr() which is always safe
                    error_message = repr(e)
                
                logger.error(f"Pipeline execution failed: {error_message}")
                
                if main_pipeline_result and not main_pipeline_result.ready():
                    main_pipeline_result.revoke(terminate=True)
                raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {error_message}")
        
        logger.debug(f"-------trigger_pipeline {trigger_pipeline}----")
        return trigger_pipeline

    # --- Add service with fully dynamic components ---
    print(f"debug generated pipeline_name: {pipeline_name}")
    print("------------------------------------------------")
    ml_service.add_ml_service(
        rule=f"/{pipeline_name}",
        ml_function=create_pipeline_trigger(pipeline_def, InputsType, ParamsType),
        inputs_cli_parser=typer.Argument(None, parser=inputs_parser),
        parameters_cli_parser=typer.Option(None, parser=params_parser),
        task_schema_func=schema_func,
        short_title=short_title,
    )

app = ml_service.app
