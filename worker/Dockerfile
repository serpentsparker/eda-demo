FROM python:3.14-slim

WORKDIR /app

RUN pip install --no-cache-dir uv==0.11.8

COPY pyproject.toml .
RUN uv sync --no-dev

COPY app/ app/

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import app.main"

CMD ["uv", "run", "python", "-m", "app.main"]
