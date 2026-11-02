"""Run the intermediary: python -m safe_match_intermediary (one worker, like rb-api)."""

import logging

import uvicorn

from .app import create_app
from .config import Settings

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def main() -> None:
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    for name in ("httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.WARNING)
    settings = Settings.from_env()
    app = create_app(settings)
    uvicorn.run(app, host=settings.host, port=settings.port, workers=1, log_config=None)


if __name__ == "__main__":
    main()
