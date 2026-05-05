FROM python:3.14-slim

WORKDIR /app

RUN pip install --no-cache-dir uv==0.11.8

COPY pyproject.toml .
RUN uv sync --no-dev

COPY app/ app/

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD celery -A app.worker inspect ping

CMD ["uv", "run", "celery", "-A", "app.worker", "worker", "--loglevel=info"]
