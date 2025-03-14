import os

import ollama
import yaml
from rich import print

CHAT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "chat_config.yml")


def load_chat_config() -> dict:
    with open(CHAT_CONFIG_PATH) as stream:
        return yaml.safe_load(stream)


def download_model(chat_config: dict) -> None:
    ollama.pull(chat_config["model"]["name"])


def stream_output(user_content: str, chat_config: dict) -> str:
    download_model(chat_config)
    # print(user_content)
    # print(chat_config["prompt"]["system"])
    user_content = "in the context of rescuebox or RescueBox or RescueBox plugin " + user_content 
    stream = ollama.chat(
        model=chat_config["model"]["name"],
        messages=[
            {"role": "system", "content": chat_config["prompt"]["system"]},
            {"role": "user", "content": f"{chat_config["prompt"]["system"]}\n\n{user_content}" },
        ],
        stream=True,
    )

    print("[bold green]Answer:")
    buffer = ""
    for chunk in stream:
        buffer += chunk["message"]["content"]
        print(chunk["message"]["content"], end="", flush=True)
    return buffer
