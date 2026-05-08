# EDA Demo

A demonstration of **event-driven architecture** using Python and AWS services (EventBridge + SQS + PostgreSQL).

## Services

| Service | Description |
|---|---|
| `api/` | Async REST API built with FastAPI |
| `worker/` | Background job worker that polls SQS via boto3 |

Both services are shipped as Docker images and deployed to AWS ECS or Kubernetes. Infrastructure is provisioned with Terraform. Local development uses Docker Compose with LocalStack.

## Quick Start

### Prerequisites

- Docker & Docker Compose
- [`uv`](https://pypi.org/project/uv/) (`pip install uv`)
- [`pre-commit`](https://pre-commit.com/) (`pip install pre-commit`)

### 1. Configure environment

```bash
cp .env.example .env
```

### 2. Start all services

```bash
docker compose -f docker/docker-compose.yml up --build
```

This starts:
- FastAPI API on `http://localhost:8000`
- SQS worker (polls demo-queue via boto3)
- LocalStack (SQS + EventBridge) on `http://localhost:4566`
- PostgreSQL on `localhost:5432`

### 3. Explore the API

```
GET  /health
POST /jobs
GET  /jobs/{job_id}
```

Interactive docs: `http://localhost:8000/docs`

## Development

```bash
# Install dependencies (add --extra dev for testing and linting tools)
cd api && uv sync --extra dev
cd worker && uv sync --extra dev
cd integration && uv sync

# Install git hooks (run once after cloning)
pre-commit install

# Lint & format (run from within each service directory)
cd api && uv run ruff check . && uv run ruff format .
cd worker && uv run ruff check . && uv run ruff format .

# Unit tests — no infrastructure required
cd api && uv run pytest -v
cd worker && uv run pytest -v

# End-to-end integration tests — require the full stack
docker compose -f docker/docker-compose.yml up --build -d
cd integration && uv run pytest -v
```

## Pre-commit Hooks

This project uses [pre-commit](https://pre-commit.com/) to enforce quality and security checks on every commit.

| Hook | Purpose |
|---|---|
| `trailing-whitespace` | Remove trailing whitespace |
| `end-of-file-fixer` | Ensure files end with a newline |
| `check-yaml` / `check-toml` / `check-json` | Validate config file syntax |
| `check-merge-conflict` | Block accidental merge conflict markers |
| `check-added-large-files` | Reject files > 500 KB |
| `no-commit-to-branch` | Prevent direct commits to `main` |
| `detect-private-key` | Block PEM/RSA private keys |
| `ruff` + `ruff-format` | Python lint, auto-fix, and format |
| `detect-secrets` | Scan for leaked credentials and API keys |
| `terraform_fmt` | Auto-format Terraform files |
| `hadolint` | Lint Dockerfiles |

```bash
# Install hooks into .git/hooks
pre-commit install

# Run all hooks against every file (useful after first install)
pre-commit run --all-files

# Update hook versions
pre-commit autoupdate
```

The `detect-secrets` hook compares against `.secrets.baseline`. If a legitimate
secret-like string is flagged as a false positive, add it to the baseline:

```bash
detect-secrets scan > .secrets.baseline   # regenerate from scratch
# or audit interactively
detect-secrets audit .secrets.baseline
```

## Infrastructure

```bash
cd infra/environments/dev
terraform init
terraform plan
terraform apply
```

## Architecture

```
Client → FastAPI (api/) → EventBridge → SQS (demo-queue) → Worker (worker/)
                                                                  ↓
                                                     PostgreSQL (job status)
                                                     EventBridge (outcome event)
```
