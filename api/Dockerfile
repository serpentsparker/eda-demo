FROM python:3.14-slim

WORKDIR /app

RUN pip install --no-cache-dir uv==0.11.8

COPY pyproject.toml .
RUN uv sync --no-dev

COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
