# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Stage 1: builder — install the app + deps into an isolated virtualenv.
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# README.md is required because pyproject.toml references it as the readme.
COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install --upgrade pip \
    && pip install .

# ---------------------------------------------------------------------------
# Stage 2: final — copy only the venv, run as a non-root user.
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS final

LABEL org.opencontainers.image.title="url-shortener" \
      org.opencontainers.image.description="Base62 URL shortener CI/CD demo" \
      org.opencontainers.image.licenses="MIT"

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create an unprivileged user to run the service.
RUN groupadd --system app \
    && useradd --system --gid app --create-home --home-dir /home/app app

COPY --from=builder /opt/venv /opt/venv

USER app
WORKDIR /home/app

EXPOSE 8000

# The slim image has no curl, so probe /health from Python's stdlib instead.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)"]

ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
