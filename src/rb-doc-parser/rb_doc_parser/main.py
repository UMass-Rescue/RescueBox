import typer
from rb.lib.docs import BASE_WIKI_URL, download_all_wiki_pages , get_rescuebox_code # type: ignore
from rb.lib.ollama import use_ollama  # type: ignore
from rb_doc_parser.chat import load_chat_config, stream_output

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
    reference_src = get_rescuebox_code()
    data = []
    for k , v in reference_doc.items():
        for l in v:
            s = str(l).replace("'","")
            if len(s) < 2:
                continue
            data.append(s)
    src = []
    for k, v in reference_src.items():
        for line in v:
            s = str(line).replace("''","")
            s = str(line).replace('\n',"")
            if len(s) < 2:
                continue
            src.append(s)
    
    # data.append(str(src))
    chat_config = load_chat_config()
    chat_config["prompt"]["system"] = chat_config["prompt"]["system"].format(
        reference_doc= data 
    )
    return stream_output(question, chat_config)
