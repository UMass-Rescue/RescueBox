import os
from typing import Annotated

import typer
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG) # Set level for the handler
logger.addHandler(handler)

app = typer.Typer()


@app.command()
def ls(
    path: str = typer.Argument(..., help="The path to list files from"),
) -> list[str]:
    """
    List files in a directory
    """
    if not os.path.exists(path):
        typer.echo(f"Path {path} does not exist")
        raise typer.Abort()
    if not os.path.isdir(path):
        typer.echo(f"Path {path} is not a directory")
        raise typer.Abort()

    for file in os.listdir(path):
        typer.echo(file)

    return os.listdir(path)


@app.command()
def op(path: str = typer.Argument(..., help="The path to open")) -> str:
    """
    Open a file
    """
    if not os.path.exists(path):
        typer.echo(f"Path {path} does not exist")
        raise typer.Abort()
    typer.launch(path)
    return path


@app.command()
def head(
    path: str = typer.Argument(..., help="The path to the file to cat"),
    n: Annotated[int, typer.Option("-n", help="The number of lines to print")] = 10,
) -> str:
    """
    Print the first n lines of a file
    """
    logger.debug(f"head: {path}")
    with open(path, "r") as f:
        head_str = ""
        for _ in range(n):
            head_str += f.readline()
        typer.echo(head_str)
    return path
