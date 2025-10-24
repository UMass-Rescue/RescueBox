import os
from typing import Annotated

import typer

app = typer.Typer()


@app.command()
def ls(
    path: str = typer.Argument(..., help="The path to list files from"),
) -> list[str] | str:
    """
    List files in a directory
    """
    if not os.path.exists(path):
        error = f"Path {path} does not exist"
        typer.echo(error)
        return error
    if not os.path.isdir(path):
        error = f"Path {path} is not a directory"
        typer.echo(error)
        return error

    for file in os.listdir(path):
        typer.echo(file)

    return os.listdir(path)


@app.command()
def op(path: str = typer.Argument(..., help="The path to open")) -> str:
    """
    Open a file
    """
    if not os.path.exists(path):
        error = f"Path {path} does not exist"
        typer.echo(error)
        return error

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
    if not os.path.exists(path):
        error = f"Path {path} does not exist"
        typer.echo(error)
        return error
    if not os.path.isfile(path):
        error = f"Path {path} is not a regular file"
        typer.echo(error)
        return error
    if n < 0:
        error = f"Number of lines to read cannot be negative"
        typer.echo(error)
        return error

    lines = []
    with open(path, "r") as f:
        for _ in range(n):
            line = f.readline()
            if not line:
                break

            lines.append(line)

    head_output = "".join(lines)
    typer.echo(head_output)

    return head_output
