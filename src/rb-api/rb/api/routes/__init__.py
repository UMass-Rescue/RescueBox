from .cli import cli_router
from .probes import probes_router
from .ui import ui_router
from rb_deepfake_app.main import deepfake_plugin_router
from rb_demo_app.main import demo_plugin_router

__all__ = ["cli_router", "probes_router", "ui_router", "demo_plugin_router" "deepfake_plugin_router"]
