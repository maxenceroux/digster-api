FROM python:3.8.9 as base

# Set environment variables for Python behavior
ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

WORKDIR /app

FROM base as builder

# Set environment variables for pip and poetry behavior
ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.0.5

# Install Poetry and virtualenv
RUN pip install "poetry==1.1.12"
RUN python -m venv /venv

# Install Rust (needed for orjson and other Rust-based dependencies)
RUN apt-get update && apt-get install -y curl build-essential && \
    curl https://sh.rustup.rs -sSf | sh -s -- -y

# Add Rust to PATH for the build environment
ENV PATH="/root/.cargo/bin:$PATH"

# Copy project files and install dependencies
COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt -o requirements.txt --without-hashes && /venv/bin/pip install -r requirements.txt

FROM base as final

# Install additional packages for your app
RUN apt-get update
RUN apt-get install -y ffmpeg libsm6 libxext6

# Copy the virtual environment from the builder stage
COPY --from=builder /venv /venv

# Copy application code and entry scripts
COPY Makefile Makefile
COPY ./digster_api/ ./digster_api/
COPY ./tests/ ./tests/
COPY ./alembic.ini ./alembic.ini
COPY docker-entrypoint.sh  ./
COPY docker-entrypoint-initdb.sh  ./
COPY docker-entrypoint-test.sh  ./
COPY docker-entrypoint-worker-color.sh  ./
COPY docker-entrypoint-worker-genre.sh  ./

# Make the entry scripts executable
RUN chmod 777 ./docker-entrypoint.sh && \
    chmod 777 ./docker-entrypoint-worker-genre.sh && \
    chmod 777 ./docker-entrypoint-worker-color.sh && \
    chmod 777 ./docker-entrypoint-initdb.sh && \
    chmod 777 ./docker-entrypoint-test.sh

# Define the entrypoint for the container
ENTRYPOINT ["./docker-entrypoint.sh"]
