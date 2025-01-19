FROM python:3.12-slim

EXPOSE 5050 8080
WORKDIR /usr/src/app
RUN pip install --no-cache-dir --upgrade pip==23.3 poetry

COPY ./app ./
WORKDIR /usr/src/

COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false && poetry install --no-root

CMD ["python3", "-m", "app"]