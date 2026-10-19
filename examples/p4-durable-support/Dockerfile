# Build from the repository root:
# docker build -f examples/p4-durable-support/Dockerfile -t p4-support .
FROM ghcr.io/astral-sh/uv:0.12.15 AS uv
FROM python:3.11.14-slim-bookworm
COPY --from=uv /uv /uvx /bin/
WORKDIR /srv/examples/p4-durable-support
COPY examples/p4-durable-support/pyproject.toml examples/p4-durable-support/uv.lock ./
RUN uv sync --frozen --no-dev
COPY examples/support_agent /srv/examples/support_agent
COPY examples/p4-durable-support/app ./app
COPY examples/p4-durable-support/migrations ./migrations
ENV PYTHONPATH=/srv/examples PYTHONDONTWRITEBYTECODE=1
# Access through a local-only host publication; these are demo credentials.
CMD ["uv", "run", "--frozen", "--no-dev", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
