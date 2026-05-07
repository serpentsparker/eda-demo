"""Worker service configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Worker service settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # AWS
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_default_region: str = "eu-central-1"
    localstack_endpoint: str | None = None

    # SQS / Celery broker
    sqs_queue_name: str = "demo-queue"
    sqs_queue_url: str = "http://localhost:4566/000000000000/demo-queue"
    celery_broker_url: str = "sqs://localhost:4566"
    celery_result_backend: str = "redis://localhost:6379/0"

    # EventBridge
    eventbridge_bus_name: str = "demo-event-bus"


settings = Settings()
