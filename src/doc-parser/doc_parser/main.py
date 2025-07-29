import typer
from rb.lib.docs import BASE_WIKI_URL, download_all_wiki_pages  # type: ignore
from rb.lib.ollama import use_ollama  # type: ignore
from doc_parser.chat import load_chat_config, stream_output

app = typer.Typer()


@app.command()
def open() -> str:
    """
    Open docs in the browser
    """
    typer.launch(BASE_WIKI_URL)
    return BASE_WIKI_URL


@use_ollama
@app.command()
def ask(
    question: str = typer.Argument(..., help="Ask a question against the docs"),
) -> str:
    """
    Ask a question against the docs
    """
    reference_doc = download_all_wiki_pages()
    
    chat_config = load_chat_config()
    print(chat_config)
    chat_config["prompt"]["system"] = chat_config["prompt"]["system"].format(
        reference_doc=reference_doc
    )

    return stream_output(question, chat_config)
