FROM tensorflow/tensorflow:2.3.0-gpu

RUN : \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        software-properties-common \
    && add-apt-repository -y ppa:deadsnakes \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        python3.8-venv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && :

WORKDIR /api
COPY pyproject.toml poetry.lock ./
#RUN poetry export -f requirements.txt | /venv/bin/pip install -r /dev/stdin

ENV POETRY_VERSION=1.1.5
RUN pip install "poetry==$POETRY_VERSION"
ENV POETRY_VIRTUALENVS_PATH=./

#RUN poetry config virtualenvs.create false
RUN poetry env use 3.8
RUN poetry install --no-interaction

COPY . .

RUN ls -lSht
RUN ./*-py3.8/bin/activate
CMD ["python", "-m", "uvicorn", "api.main:api", "--reload", "--host", "0.0.0.0"]
