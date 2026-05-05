# CLAUDE.md

This file provides guidance to Claude when working in this repository.

---

## Project Overview

This project is a **demonstration of event-driven architecture** using Python, the Celery framework, and AWS services (EventBridge and SQS).

It is structured as a **mono-repo** containing two deployable services:

- **`api/`** — An asynchronous REST API built with FastAPI
- **`worker/`** — A background worker built with Celery for CPU-intensive tasks

Both services are shipped as Docker images and deployed to **AWS ECS or Kubernetes**. Infrastructure is provisioned with **Terraform**. Local development uses **Docker Compose** with **LocalStack** to emulate AWS services.

---

## Repository Structure

```
project-root/
├── api/                        # FastAPI async API
│   ├── app/
│   │   ├── routers/            # API route definitions
│   │   ├── schemas/            # Pydantic request/response models
│   │   ├── events/             # EventBridge event publishers
│   │   └── config.py
│   ├── Dockerfile
│   └── pyproject.toml
├── worker/                     # Celery background worker
│   ├── app/
│   │   ├── tasks/              # Celery task definitions
│   │   ├── events/             # EventBridge event consumers
│   │   └── config.py
│   ├── Dockerfile
│   └── pyproject.toml
├── infra/                      # Terraform infrastructure
│   ├── modules/
│   └── environments/
│       └── dev/
├── docker/
│   ├── docker-compose.yml      # Local dev environment
│   └── localstack/             # LocalStack config (emulates SQS, EventBridge)
├── tests/
│   ├── unit/
│   └── integration/            # Run against LocalStack only
├── .env.example
├── .github/
│   └── workflows/              # GitHub Actions CI/CD workflows
└── README.md
```

---

## Local Development Setup

### 1. Configure Environment Variables

Copy the example file and fill in the required values:

```bash
cp .env.example .env
```

Key environment variables (see `.env.example` for full reference):

```dotenv
# AWS Configuration
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_DEFAULT_REGION=eu-central-1

# LocalStack
LOCALSTACK_ENDPOINT=http://localhost:4566

# SQS
SQS_QUEUE_NAME=demo-queue
SQS_QUEUE_URL=http://localhost:4566/000000000000/demo-queue

# EventBridge
EVENTBRIDGE_BUS_NAME=demo-event-bus

# Celery
CELERY_BROKER_URL=sqs://localhost:4566
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# App
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
```

> ⚠️ Never commit `.env` or any file containing secrets to version control.

### 2. Start All Services Locally

```bash
docker compose -f docker/docker-compose.yml up --build
```

This starts the API, worker, LocalStack (SQS + EventBridge emulation), and Redis.

---

## Package & Dependency Management

Use **`uv`** as the project manager. Install it from [pypi.org](https://pypi.org/project/uv/):

```bash
pip install uv
```

Install dependencies for each service:

```bash
cd api && uv sync
cd worker && uv sync
```

Add a new dependency:

```bash
uv add <package>
```

> Always install packages from the official [pypi.org](https://pypi.org). Do not use unofficial mirrors or sources.

---

## Common Commands

### Running the API locally (without Docker)

```bash
cd api
uv run uvicorn app.main:app --reload
```

### Running the Worker locally (without Docker)

```bash
cd worker
uv run celery -A app.worker worker --loglevel=info
```

### Pre-commit Hooks

Install hooks once after cloning — they run automatically on every `git commit`.

```bash
pip install pre-commit
pre-commit install

# Run all hooks manually against every file
pre-commit run --all-files

# Update hook versions to latest
pre-commit autoupdate
```

Hooks configured in `.pre-commit-config.yaml`:

| Hook | What it catches |
|---|---|
| `trailing-whitespace`, `end-of-file-fixer` | Whitespace hygiene |
| `check-yaml` / `check-toml` / `check-json` | Config file syntax errors |
| `check-merge-conflict` | Accidental merge conflict markers |
| `check-added-large-files` | Files > 500 KB |
| `no-commit-to-branch` | Direct commits to `main` |
| `detect-private-key` | PEM / RSA private keys |
| `ruff` + `ruff-format` | Python lint, auto-fix, formatting |
| `detect-secrets` | Leaked credentials and API keys (compares against `.secrets.baseline`) |
| `terraform_fmt` | Terraform formatting |
| `hadolint` | Dockerfile best-practice violations |

If `detect-secrets` flags a false positive, update the baseline:

```bash
# Regenerate baseline from the current state of the repo
detect-secrets scan --exclude-files '\.env.*' > .secrets.baseline

# Or audit interactively to mark items as non-secrets
detect-secrets audit .secrets.baseline
```

### Linting & Formatting

```bash
# Lint
uv run ruff check .

# Format
uv run ruff format .

# Auto-fix
uv run ruff check --fix .
```

### Running Tests

Each service has its own pytest configuration and must be run from its own directory
so that `app/` resolves to the correct service package (both services use `app/` as
their package root — running from the service directory avoids naming conflicts).

```bash
# API unit tests
cd api && uv run pytest -v

# Worker unit tests
cd worker && uv run pytest -v

# Integration tests (requires LocalStack running)
cd api && uv run pytest ../tests/integration/ -m integration -v

# With coverage report
cd api && uv run pytest --cov=app --cov-report=term-missing
cd worker && uv run pytest --cov=app --cov-report=term-missing

# With HTML coverage report
cd api && uv run pytest --cov=app --cov-report=html
```

---

## Technology Stack

| Concern | Tool |
|---|---|
| Language | Python 3.14 |
| API Framework | FastAPI |
| Task Queue | Celery |
| AWS SDK | boto3 |
| Infrastructure | Terraform |
| Containerisation | Docker + Docker Compose |
| Package Manager | uv |
| Linting & Formatting | ruff |
| Pre-commit Hooks | pre-commit |
| Secret Scanning | detect-secrets |
| Testing | pytest + pytest-cov |
| AWS Emulation (local) | LocalStack |
| CI/CD | GitHub Actions |
| Hosting | AWS ECS or Kubernetes |

---

## Coding Conventions

### General

- Follow **Google Python Style Guide** strictly.
- Use **Python 3.14** features and standard library where possible. Prefer native tools over third-party ones.
- All code must include **type hints** on function signatures and class attributes.
- Write **Google-style docstrings** for all public modules, classes, and functions.
- Maximum line length: **100 characters** (configured in `ruff`).

### Naming Conventions

- `snake_case` for variables, functions, and module names.
- `PascalCase` for class names.
- `UPPER_SNAKE_CASE` for constants.
- `_leading_underscore` for private/internal members.
- Be descriptive and explicit — avoid abbreviations unless they are universally understood (e.g. `id`, `url`).

### Code Style

- Use `ruff` for both linting and formatting. All code must pass `ruff check` and `ruff format` without errors before committing.
- Prefer immutability: use `tuple` over `list` and `frozenset` over `set` where applicable.
- Use `pydantic` models for all data validation and serialisation (request/response schemas, event payloads).
- Avoid wildcard imports (`from module import *`).
- Keep functions short and single-purpose. Prefer composition over inheritance.

### AWS & Celery

- Use **`boto3`** for all AWS interactions.
- Use **`celery`** for all background task definitions.
- All AWS clients and resources should be initialised via a shared factory/config to support LocalStack endpoint injection.
- Never hardcode AWS resource names or ARNs — always read from environment variables or config.

---

## Testing Conventions

- Use **`pytest`** for all tests.
- **Unit tests** (`tests/unit/`): test business logic in isolation, no external dependencies.
- **Integration tests** (`tests/integration/`): run against **LocalStack** only for local development. Do not mock AWS services — use LocalStack or a real AWS deployment.
- Use **`pytest-cov`** for coverage reports.
- Test files must mirror the source structure (e.g. `api/app/routers/foo.py` → `tests/unit/api/routers/test_foo.py`).
- Name test functions descriptively: `test_<what>_<expected_outcome>`.

---

## Infrastructure (Terraform)

- All infrastructure is defined in `infra/`.
- Currently one deployment environment: **`dev`** (`infra/environments/dev/`).
- Do not apply Terraform manually in production — use CI/CD pipelines.
- Always run `terraform plan` before `terraform apply`.
- Store Terraform state remotely (e.g. S3 + DynamoDB for locking) — never commit `.tfstate` files.

```bash
cd infra/environments/dev
terraform init
terraform plan
terraform apply
```

---

## CI/CD (GitHub Actions)

- Workflows are located in `.github/workflows/`.
- Claude may suggest and modify GitHub Actions workflows.
- Currently one deployment environment: **`dev`**.
- Standard pipeline should include:
  1. Lint & format check (`ruff`)
  2. Unit tests
  3. Build Docker images
  4. Integration tests against LocalStack
  5. Push Docker images to AWS ECR
  6. Deploy to `dev` environment (ECS or Kubernetes)
- Use **GitHub Secrets** for all sensitive values (AWS credentials, tokens). Never hardcode secrets in workflow files.

---

## Security & Reliability Best Practices

- **Never commit secrets**, credentials, `.env` files, or `.tfstate` files to version control. Use `.gitignore` to exclude them. The `detect-private-key` and `detect-secrets` pre-commit hooks enforce this automatically.
- **Use IAM least-privilege principles**: grant only the permissions required for each service.
- **Rotate credentials regularly** and use short-lived credentials (e.g. IAM roles) over long-lived access keys wherever possible.
- **Validate all inputs** at the API boundary using Pydantic models.
- **Handle errors explicitly**: avoid bare `except` clauses; catch specific exceptions and log meaningfully.
- **Use structured logging** (e.g. JSON format) to facilitate log aggregation in AWS CloudWatch.
- **Do not log sensitive data** (PII, credentials, tokens).
- **Pin dependency versions** in `pyproject.toml` to ensure reproducible builds.
- **Keep Docker images minimal**: use slim or distroless base images, and do not include dev dependencies in production images.
- **Use health checks** for all Docker services and ECS task definitions.
- **Idempotency**: design Celery tasks and EventBridge consumers to be idempotent — safe to retry on failure.
- **Dead-letter queues (DLQ)**: configure DLQs for all SQS queues to capture failed messages.
