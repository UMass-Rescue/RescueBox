# Builder Stage
FROM nikolaik/python-nodejs:python3.12-nodejs24-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    # prevents python creating .pyc files
    PYTHONDONTWRITEBYTECODE=1 \
    \
    # pip
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    \
    # poetry
    # https://python-poetry.org/docs/configuration/#using-environment-variables
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    # do not ask any interactive question
    POETRY_NO_INTERACTION=1

# prepend poetry and venv to path
ENV PATH="~/.local/bin:.:$PATH"

# Install Poetry
RUN pip install pipx && \
    pipx ensurepath && \
    pipx install poetry

# for age-gender plugin
RUN apt-get update && apt-get install -y  curl libgl1 libglib2.0-0
RUN /usr/local/bin/pip install opencv-python-headless

# for audio ffmpeg
RUN apt-get install -y ffmpeg

# Install Git if needed for dependencies or project operations
RUN apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /rb

RUN git clone https://github.com/UMass-Rescue/RescueBox.git

# run poetry install to get dependencies
RUN cd /rb/RescueBox && ~/.local/bin/poetry sync && ~/.local/bin/poetry install

# run npm install to get desktop/autoui dependencies
RUN python -m pip install setuptools
RUN cd /rb/RescueBox/RescueBox-Desktop && apt-get update && apt-get install -y build-essential && npm install && npm run build:dll
RUN cd /rb/RescueBox/web/rescuebox-autoui && npm install

ENV PATH="/usr/local/bin:/root/.local/bin:/rb/.venv/bin:$PATH"

CMD ["sleep", "infinity"]