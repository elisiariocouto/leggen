FROM python:3.13-alpine AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable --no-group dev

FROM python:3.13-alpine

LABEL org.opencontainers.image.source="https://github.com/elisiariocouto/leggen"
LABEL org.opencontainers.image.authors="Elisiário Couto <elisiario@couto.io>"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.title="Leggen API"
LABEL org.opencontainers.image.description="Open Banking API for Leggen"
LABEL org.opencontainers.image.url="https://github.com/elisiariocouto/leggen"

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s CMD wget -q --spider http://127.0.0.1:8000/api/v1/health || exit 1

CMD ["/app/.venv/bin/leggen", "server"]
