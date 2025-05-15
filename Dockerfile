# Base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# uv respects PIP_NO_CACHE_DIR for its pip operations
ENV PIP_NO_CACHE_DIR=off
# ENV UV_SYSTEM_PYTHON true # Removed to allow uv to manage Python version based on .python-version
# Explicitly set uv cache dir for build-time caching
ENV UV_CACHE_DIR=/root/.cache/uv

# Install git for git dependencies and build-essential for C extensions, then copy uv binary
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    build-essential && \
    rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create and set the working directory
WORKDIR /app

# Copy .python-version first to ensure uv uses it for subsequent Python operations
COPY .python-version /app/

# Install the Python version specified in .python-version
# uv will download and install it if not already matching the system Python.
RUN uv python install

# Copy project definition files required for dependency resolution and project build
COPY pyproject.toml uv.lock README.md /app/

# Install dependencies (excluding the project itself initially for better caching)
# This layer is cached as long as pyproject.toml/uv.lock/README.md don't change.
# uv will use the Python version it has just installed/verified.
RUN --mount=type=cache,target=${UV_CACHE_DIR} \
    uv sync --locked --no-install-project

# Copy the application source code and typings
COPY ./src /app/src
COPY ./typings /app/typings

# Install the project itself and any remaining dependencies
# This step should be faster if dependencies are already cached.
# uv will use the Python version it has just installed/verified.
RUN --mount=type=cache,target=${UV_CACHE_DIR} \
    uv sync --locked

# Expose the Streamlit port
EXPOSE 8501

# Default command to run the Streamlit app
# uv run will use the Python environment uv is managing.
CMD ["uv", "run", "streamlit", "run", "src/sr_assistant/app/main.py", "--server.port=8501", "--server.address=0.0.0.0"] 