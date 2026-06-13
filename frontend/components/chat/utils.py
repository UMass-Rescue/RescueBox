import logging

from frontend.design_tokens import Design

# Legacy name kept for imports / __all__; prefer Design in new code.
UIStyling = Design

logger = logging.getLogger(__name__)

_LATEST_INPUT_AREA = {"container": None}


def set_latest_input_area(container):
    _LATEST_INPUT_AREA["container"] = container


def get_latest_input_area():
    return _LATEST_INPUT_AREA["container"]
