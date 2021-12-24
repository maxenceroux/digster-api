FROM python:3.8.9 as base

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

WORKDIR /app

FROM base as builder

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.0.5

RUN pip install "poetry==1.1.12"
RUN python -m venv /venv

COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt -o requirements.txt --without-hashes && /venv/bin/pip install -r requirements.txt



FROM base as final
COPY --from=builder /venv /venv
COPY Makefile Makefile
COPY ./digster_api/ ./digster_api/
COPY ./tests/ ./tests/
COPY ./alembic.ini ./alembic.ini
COPY docker-entrypoint.sh  ./
COPY docker-entrypoint-initdb.sh  ./
COPY docker-entrypoint-test.sh  ./
RUN chmod 777 ./docker-entrypoint.sh && chmod 777 ./docker-entrypoint-initdb.sh && chmod 777 ./docker-entrypoint-test.sh
