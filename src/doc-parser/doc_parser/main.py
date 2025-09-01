import typer
from rb.lib.ollama import use_ollama  # type: ignore
from rb.lib.docs import download_all_wiki_pages  # type: ignore

from doc_parser.chat import load_chat_config, stream_output
from doc_parser.vector_store import create_vector_store, search_vector_store
import glob
import os
import sys

app = typer.Typer()

def load_docs_and_create_vector_store():
    """
    Load all wiki pages and create the vector store.
    """
    all_docs = {}
    # Example Usage
    all_docs = download_all_wiki_pages()

    plugin_code_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    print(f"Loading {plugin_code_path}")
    
    for file in glob.glob(f"{plugin_code_path}/**/*.pyxx", recursive=True):
        with open(file, "r") as f:
            print(f"Loading {file}")
            try:
                all_docs[file] = f.read()
            except UnicodeDecodeError:
                print(f"Skipping {file} due to UnicodeDecodeError")
            all_docs[file] = f.read()

    create_vector_store(all_docs)

@use_ollama
@app.command()
def ask(
    question: str = typer.Argument(..., help="Ask a question against the docs"),
) -> str:
    """
    Ask a question against the docs
    """
    relevant_docs = search_vector_store(question)
    
    chat_config = load_chat_config()
    chat_config["prompt"]["system"] = chat_config["prompt"]["system"].format(
        reference_doc=relevant_docs
    )
    
    return stream_output(question, chat_config)

load_docs_and_create_vector_store()