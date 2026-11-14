# syntax=docker/dockerfile:1
# Build from the python/ workspace directory:
#   docker build -f apps/github_report/Dockerfile .
# The ignore file is python/.dockerignore.

FROM python:3.14-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

COPY pyproject.toml uv.lock ./
COPY packages ./packages
COPY apps ./apps

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --package github-report --no-dev --no-editable

FROM python:3.14-slim-bookworm AS runtime

RUN groupadd --system --gid 65532 app \
    && useradd --system --uid 65532 --gid app --home-dir /app --shell /usr/sbin/nologin app \
    && mkdir -p /app/github_reports \
    && chown app:app /app/github_reports

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MONOREPO_ROOT=/app

USER app

CMD ["github-report"]
