from .cli import cli_router
from .probes import probes_router
from .ui import ui_router
from rb_deepfake_app.main import plugin_router

__all__ = ["cli_router", "probes_router", "ui_router", "plugin_router"]
