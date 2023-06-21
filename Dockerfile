# Copyright 2023, Battelle Energy Alliance, LLC
FROM python:3.10
WORKDIR /cape2stix
RUN apt update
RUN apt install python3-pip git -y
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install poetry
COPY poetry.lock poetry.lock
COPY pyproject.toml pyproject.toml
COPY cape2stix ./cape2stix
COPY capeplugin ./capeplugin
COPY capesubd ./capesubd
COPY *.py ./
RUN poetry install
RUN yes | poetry cache clear --all .
RUN poetry run pip cache purge
ENTRYPOINT ["poetry", "run"]

