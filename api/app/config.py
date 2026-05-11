"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """API service settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # AWS
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_default_region: str = "eu-central-1"
    localstack_endpoint: str | None = None

    # EventBridge
    eventbridge_bus_name: str = "demo-event-bus"

    # SQS
    sqs_queue_name: str = "demo-queue"
    sqs_queue_url: str = "http://localhost:4566/000000000000/demo-queue"

    # Database
    database_url: str = (
        "postgresql+asyncpg://eda_user:eda_pass@localhost:5432/eda_demo"  # pragma: allowlist secret
    )

    # App
    api_host: str = "0.0.0.0"
    api_port: int = 8000


settings = Settings()
