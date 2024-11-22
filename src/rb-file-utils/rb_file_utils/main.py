import os
from typing import Annotated

import typer

app = typer.Typer()


@app.command()
def ls(
    path: str = typer.Argument(..., help="The path to list files from"),
) -> list[str]:
    """
    List files in a directory
    """
    if not os.path.exists(path):
        print(f"Path {path} does not exist")
        raise typer.Abort()
    if not os.path.isdir(path):
        print(f"Path {path} is not a directory")
        raise typer.Abort()

    for file in os.listdir(path):
        print(file)

    return os.listdir(path)


@app.command()
def op(path: str = typer.Argument(..., help="The path to open")) -> str:
    """
    Open a file
    """
    if not os.path.exists(path):
        print(f"Path {path} does not exist")
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
    if not os.path.exists(path):
        print(f"Path {path} does not exist")
        raise typer.Abort()
    with open(path, "r") as f:
        for _ in range(n):
            print(f.readline())

    return path
