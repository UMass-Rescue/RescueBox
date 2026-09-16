import os

import requests
import typer
from rich import print

os.environ["OLLAMA_HOST"] = "http://127.0.0.1:11434"


def check_ollama() -> bool:
    response = requests.get("http://127.0.0.1:11434/", timeout=5)
    if response.status_code == 200 and "Ollama" in response.text:
        return True
    return False


def use_ollama(func):
    def wrapper(*args, **kwargs):
        if not check_ollama():
            print("[red] Ollama is not running. Please start it and try again.")
            raise typer.Abort()
        return func(*args, **kwargs)

    return wrapper
