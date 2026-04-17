# Multi-stage build for production. See DECISIONS.md DEC-09.

# --- Builder stage ---
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv pip install --system --no-cache .

# --- Runtime stage ---
FROM python:3.12-slim AS runtime

WORKDIR /app

# Non-root user. --create-home so $HOME exists and is writable; LiteLLM,
# CrewAI, and HuggingFace caches all drop into $HOME by default and a
# missing directory triggers PermissionError at first call.
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser && \
    mkdir -p /home/appuser/.cache && \
    chown -R appuser:appuser /home/appuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY --chown=appuser:appuser src/ src/
COPY --chown=appuser:appuser knowledge/ knowledge/

USER appuser
ENV HOME=/home/appuser \
    XDG_CACHE_HOME=/home/appuser/.cache

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
