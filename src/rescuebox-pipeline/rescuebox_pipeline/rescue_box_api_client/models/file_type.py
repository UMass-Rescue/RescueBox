from enum import Enum


class FileType(str, Enum):
    AUDIO = "audio"
    CSV = "csv"
    IMG = "img"
    JSON = "json"
    MARKDOWN = "markdown"
    TEXT = "text"
    VIDEO = "video"

    def __str__(self) -> str:
        return str(self.value)
