# EDA Demo

A demonstration of **event-driven architecture** using Python and AWS services (EventBridge + SQS + PostgreSQL).

## Services

| Service   | Description                                    |
| --------- | ---------------------------------------------- |
| `api/`    | Async REST API built with FastAPI              |
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

| Hook                                       | Purpose                                  |
| ------------------------------------------ | ---------------------------------------- |
| `trailing-whitespace`                      | Remove trailing whitespace               |
| `end-of-file-fixer`                        | Ensure files end with a newline          |
| `check-yaml` / `check-toml` / `check-json` | Validate config file syntax              |
| `check-merge-conflict`                     | Block accidental merge conflict markers  |
| `check-added-large-files`                  | Reject files > 500 KB                    |
| `no-commit-to-branch`                      | Prevent direct commits to `main`         |
| `detect-private-key`                       | Block PEM/RSA private keys               |
| `ruff` + `ruff-format`                     | Python lint, auto-fix, and format        |
| `detect-secrets`                           | Scan for leaked credentials and API keys |
| `terraform_fmt`                            | Auto-format Terraform files              |
| `hadolint`                                 | Lint Dockerfiles                         |

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

The system consists of two independently deployed services that communicate exclusively through events. The API never calls the worker directly — it publishes an event and returns immediately. The worker consumes from a queue and writes results back to the shared database.

```
                              JobRequested event
 ┌────────┐   POST /jobs   ┌─────────┐             ┌─────────────────┐
 │        │ ─────────────► │         │ ──────────► │   EventBridge   │
 │ Client │ ◄────────────  │ FastAPI │             │  demo-event-bus │
 │        │  202 Accepted  │  api/   │             └────────┬────────┘
 │        │                │         │                      │ job-requested-rule
 │        │ GET /jobs/{id} │         │                      ▼
 │        │ ─────────────► │         │             ┌─────────────────┐     ┌─────────────┐
 │        │ ◄─ job status  └────┬────┘             │   SQS Queue     │────►│   SQS DLQ   │
 └────────┘                     │ read/write       │   demo-queue    │     │ (after ×5)  │
                                │                  └─────────────────┘     └─────────────┘
                                │                           ▲
                                ▼                           │ polls
                           ┌─────────┐             ┌────────┴────────┐
                           │Postgres │◄─ status ── │    Worker       │
                           │  jobs   │   update    │   worker/       │
                           └─────────┘             └────────┬────────┘
                                                            │ JobCompleted / JobFailed events
                                                            ▼
                                                   ┌─────────────────┐
                                                   │   EventBridge   │
                                                   │  demo-event-bus │
                                                   └─────────────────┘
```

### Data flow

1. **Job submitted** — client sends `POST /jobs` with a `job_type` and `parameters`.
2. **Persisted immediately** — the API writes a `Job` record to PostgreSQL with `status=pending` before doing anything else. This ensures any subsequent status poll always finds the record.
3. **Event published** — the API sends a `JobRequested` event to EventBridge and returns `202 Accepted` with the `job_id`.
4. **Routed to SQS** — the `job-requested-rule` on EventBridge matches events from `eda-demo.api` with `detail-type: JobRequested` and delivers them to `demo-queue`.
5. **Worker picks up the message** — the worker long-polls SQS (up to 10 messages, 20 s wait) and dispatches each message to a thread pool.
6. **Job executed** — the worker updates status to `running`, runs the handler for the given `job_type`, then updates status to `completed` or `failed`.
7. **Outcome published** — the worker emits a `JobCompleted` or `JobFailed` event to EventBridge, then deletes the SQS message.
8. **Client polls status** — `GET /jobs/{job_id}` reads directly from PostgreSQL at any point.

### Technology choices

| Technology      | Role               | Why                                                                                                         |
| --------------- | ------------------ | ----------------------------------------------------------------------------------------------------------- |
| **FastAPI**     | REST API           | Async-native; automatic OpenAPI docs at `/docs`                                                             |
| **asyncpg**     | DB driver (API)    | High-performance async PostgreSQL driver; required by async SQLAlchemy                                      |
| **EventBridge** | Event bus          | Content-based routing rules decouple producers from consumers; no consumer address embedded in the producer |
| **SQS**         | Message queue      | At-least-once delivery, visibility timeout retries, and DLQ support without additional infrastructure       |
| **psycopg2**    | DB driver (worker) | Synchronous driver keeps the multi-threaded worker model straightforward                                    |
| **PostgreSQL**  | Job state          | Durable, queryable job state; allows status polling without a separate cache layer                          |

### Event catalogue

All events flow through the `demo-event-bus` EventBridge custom bus.

| Event          | Source            | Publisher | Key payload fields                                 |
| -------------- | ----------------- | --------- | -------------------------------------------------- |
| `JobRequested` | `eda-demo.api`    | API       | `job_id`, `job_type`, `parameters`, `requested_at` |
| `JobCompleted` | `eda-demo.worker` | Worker    | `job_id`, `result`, `completed_at`                 |
| `JobFailed`    | `eda-demo.worker` | Worker    | `job_id`, `error`, `failed_at`                     |

### Job lifecycle

```
POST /jobs
    │
    ▼
[ pending ] ──── worker picks up ────► [ running ]
                                            │
                              ┌─────────────┴─────────────┐
                           success                      failure
                              │                            │
                              ▼                            ▼
                        [ completed ]               [ failed ]
```

### Reliability

**Visibility timeout retry** — if a worker thread raises an unhandled exception, the SQS message is not deleted. After the visibility timeout (30 s) expires, SQS makes the message visible again for another attempt.

**Dead-letter queue** — after 5 failed receive attempts, the message moves to `demo-queue-dlq` and is excluded from further processing, preventing a poison message from blocking the queue.

**Write ordering** — the API commits the `Job` record to PostgreSQL before publishing the event, so the worker and any polling client always find the record when they look for it.

**Failure scope** — business-logic failures (unknown `job_type`, handler errors) are handled inside the worker: status is set to `failed`, an outcome event is published, and the SQS message is deleted. Only infrastructure failures (database unreachable, network error) propagate out and trigger a retry via visibility timeout.
