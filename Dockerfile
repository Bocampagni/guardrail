FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv globally
RUN pip install --no-cache-dir uv

# Copy dependency files first
COPY pyproject.toml uv.lock ./

# Install dependencies (creates .venv in /app/.venv)
RUN uv sync --frozen --no-cache

# Copy source code
COPY . .

# Download required NLTK data
RUN .venv/bin/python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"

# Ensure /app is importable and stdout is unbuffered
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

# Default entrypoint is uv so Makefile commands work
ENTRYPOINT ["uv", "run"]
CMD ["python"]
