#from typing import TypedDict
from typing_extensions import TypedDict,Annotated 
from flask_ml.flask_ml_server import MLServer, load_file_as_string
from flask_ml.flask_ml_server.models import (
    BatchTextInput,
    TextInput,
    BatchTextResponse,
    EnumParameterDescriptor,
    EnumVal,
    InputSchema,
    InputType,
    ParameterSchema,
    ResponseBody,
    TaskSchema,
    TextResponse,
)
import typer
import json
import logging
import requests
from pprint import pprint
from fastapi import APIRouter, Depends

demo_plugin_router = APIRouter()

app = typer.Typer()

logger = logging.getLogger("uvicorn.error")
logger.propagate = True
logger.setLevel(logging.DEBUG)



class TransformCaseInputs(TypedDict):
    text_inputs: BatchTextInput
    # texts: List[TextInput]


class TransformCaseParameters(TypedDict):
    to_case: str  # 'upper' or 'lower'


def create_transform_case_task_schema() -> TaskSchema:
    input_schema = InputSchema(key="text_inputs", label="Text to Transform", input_type=InputType.BATCHTEXT)
    parameter_schema = ParameterSchema(
        key="to_case",
        label="Case to Transform Text Into",
        subtitle="'upper' will convert all text to upper case. 'lower' will convert all text to lower case.",
        value=EnumParameterDescriptor(
            enum_vals=[EnumVal(key="upper", label="UPPER"), EnumVal(key="lower", label="LOWER")],
            default="upper",
        ),
    )
    return TaskSchema(inputs=[input_schema], parameters=[parameter_schema])

@app.command()
def run_demoapp(
    t_inputs: str = typer.Argument(
        str, help="Input text"
    ),
    t_case: Annotated[str, typer.Option("-to", help="The case to change to eg: 'upper' or 'lower'")] = "lower"
)-> str:
    '''
    This plugin transforms text input to upper or lower case output. It is a simple example of a rescuebox plugin.
    '''
    ti = TextInput(text = t_inputs)
    
    btp = BatchTextInput( texts = [ti])

    tp = TransformCaseInputs(text_inputs= btp)
    
    tpa = TransformCaseParameters( to_case = t_case )

    dt = {"inputs": tp, "parameters": tpa}
   
    
    response = requests.get("http://localhost:8000/demo/", data = json.dumps(dt,  default=vars),
                              headers={'Content-Type': 'application/json'})
    response_dict = response.json() 
    pprint("debug: " + str(response_dict))
    out = ""
    if response_dict["texts"]:
        pprint("input: " + response_dict["texts"][0]["title"])
        pprint("output: " + response_dict["texts"][0]["value"])
        out= response_dict["texts"][0]["value"]
    return out

@demo_plugin_router.get("/demo/")
def transform_case(inputs: TransformCaseInputs, parameters: TransformCaseParameters) -> ResponseBody:
    to_upper: bool = parameters["to_case"] == "upper"

    outputs = []
    for text_input in inputs["text_inputs"].texts:
        raw_text = text_input.text
        processed_text = raw_text.upper() if to_upper else raw_text.lower()
        outputs.append(TextResponse(value=processed_text, title=raw_text))

    return ResponseBody(root=BatchTextResponse(texts=outputs))


# @app.command()
# def test(name: str) -> str:
#     print(f"Hello world {name}")
#     return True