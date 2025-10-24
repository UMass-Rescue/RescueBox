# Builder Stage
FROM electronuserland/builder:base-03.25 AS builder

RUN apt-get update && apt-get install -y software-properties-common \
 x11-apps curl sudo vim libsm6 cmake git dos2unix fuse iproute2 net-tools iputils-ping  \
 build-essential clang  libxtst-dev \
 libxext6 libgl1 libglib2.0-0 libgconf-2-4 libasound2 libxtst6 libdrm2 libgbm1\
 libnotify-dev libnss3 libxkbcommon-x11-0 libsecret-1-dev libcap-dev  \
 libatk1.0-0 libatk-bridge2.0-0 libcups2 libgtk-3-0 libgbm-dev  \
 libxss1 gcc-multilib g++-multilib xvfb libxtst6  \
 libxrandr2 libxfixes3 libxcomposite1 libpangocairo-1.0-0 \
 libcanberra-gtk-module libcanberra-gtk3-module \
 gperf python3-dbusmock --no-install-recommends && \
 rm -rf /var/lib/apt/lists/*


RUN add-apt-repository ppa:deadsnakes/ppa && \
    DEBIAN_FRONTEND=noninteractive TZ=America/New_York apt-get install python3.12 python3.12-venv python3.10-venv python3-pip -y && \
    rm -rf /var/lib/apt/lists/* && \
    ln -s /usr/bin/python3.12 /usr/bin/python && \
    rm -f /usr/local/bin/python && \
    ln -s /usr/bin/python /usr/local/bin/python && \
    rm -rf /usr/lib/python3.12/EXTERNALLY-MANAGED

ENV PYTHONUNBUFFERED=1 \
    # prevents python creating .pyc files
    PYTHONDONTWRITEBYTECODE=1 \
    \
    # pip
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Install Poetry
RUN /usr/bin/pip install pipx
RUN /usr/local/bin/pipx install poetry
RUN pip install setuptools

RUN addgroup --gid 1000 rbuser && adduser --uid 1000 --gid 1000 --shell /bin/bash --home /home/rbuser rbuser

RUN sed -i /etc/sudoers -re 's/^%sudo.*/%sudo ALL=(ALL:ALL) NOPASSWD: ALL/g'
RUN echo '%rbuser ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

RUN cd /tmp && curl https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz -o f.tar.gz && \
    tar -xvf f.tar.gz && rm -f f*.gz && \
    cd /tmp && chmod 755 ffmpeg-git-20240629-amd64-static/ffmpeg && \
    cd  /tmp && mv ffmpeg-git-20240629-amd64-static/ffmpeg /usr/bin

RUN curl -fsSL https://ollama.com/install.sh | sh
    
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

USER rbuser

WORKDIR /home/rbuser

ENV PATH="/usr/bin:$PATH" \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_VIRTUALENVS_IN_PROJECT=false \
    POETRY_VIRTUALENVS_PATH=/home/rbuser/venv \
    # do not ask any interactive question
    POETRY_NO_INTERACTION=1

RUN mkdir -p /home/rbuser/venv && chmod 777 /home/rbuser/venv 

RUN pipx install poetry
ENV PATH="/home/rbuser/.local/bin:/home/rbuser/venv/bin:/usr/bin:$PATH"

RUN poetry config virtualenvs.path /home/rbuser/venv

RUN git clone https://github.com/UMass-Rescue/RescueBox.git -b hackathon-plugins

RUN cd /home/rbuser/RescueBox && poetry install && \ 
    poetry cache clear _default_cache --all -n

RUN cd /home/rbuser/RescueBox/RescueBox-Desktop && npm install && \
    npm cache clean --force

RUN pip install gdown && gdown 1mCZyKGgK0ZjPxG3h2vWet0RQxaMxrTfB && \
    unzip assets_rb_server.zip -d /home/rbuser/RescueBox/    
#  poetry 

RUN echo "export VENV=`ls /home/rbuser/venv/`" >> /tmp/envfile
RUN . /tmp/envfile; echo "PATH=/usr/bin:/home/rbuser/.local/bin:/home/rbuser/venv/$VENV/bin:$PATH" >> ~/.bashrc && \
   rm -f /tmp/envfile

# run npm install to get desktop/autoui dependencies
RUN cd /home/rbuser/RescueBox/web/rescuebox-autoui && npm install

USER root
RUN chown root /home/rbuser/RescueBox/RescueBox-Desktop/node_modules/electron/dist/chrome-sandbox
RUN chmod 4755 /home/rbuser/RescueBox/RescueBox-Desktop/node_modules/electron/dist/chrome-sandbox
USER rbuser

CMD ["sleep", "infinity"]

