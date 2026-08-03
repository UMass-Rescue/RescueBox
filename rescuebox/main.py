from importlib.metadata import version

import typer
from rich import print

app = typer.Typer()
management_app = typer.Typer()
__version__ = version("rescuebox")


@management_app.command()
def info() -> str:
    """
    Print info about the RescueBox CLI
    """
    message = f"RescueBox CLI with plugins {__version__}"
    print(message)
    return message


@management_app.command()
def list_plugins() -> list[str]:
    """
    List all plugins
    """
    from rescuebox.plugins import plugins  # Lazy Import

    print("Plugins:")
    plugin_list = []
    for plugin in plugins:
        print(f"- {plugin.full_name}, {plugin.cli_name}")
        plugin_list.append(plugin.cli_name)
    return plugin_list


app.add_typer(management_app, name="manage")


# Delay plugin loading to avoid circular import
def load_plugins():
    from rescuebox.plugins import plugins  # Import from __init__.py now

    return plugins


plugins = load_plugins()

for plugin in plugins:
    app.add_typer(plugin.app, name=plugin.cli_name)
