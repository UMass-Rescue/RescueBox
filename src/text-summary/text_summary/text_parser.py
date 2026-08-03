from pathlib import Path

import PyPDF2


def parse_raw_text(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8")


def parse_pdf(file_path: Path) -> str:
    text = ""
    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text


# File extension to parser function mapping
PARSERS = {
    ".txt": parse_raw_text,
    ".pdf": parse_pdf,
    ".md": parse_raw_text,
}
