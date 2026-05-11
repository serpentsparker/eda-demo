"""Worker service configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Worker service settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # AWS
    localstack_endpoint: str | None = None

    # SQS
    sqs_queue_url: str = "http://localhost:4566/000000000000/demo-queue"

    # Database
    database_url: str = (
        "postgresql+asyncpg://eda_user:eda_pass@localhost:5432/eda_demo"  # pragma: allowlist secret
    )

    # EventBridge
    eventbridge_bus_name: str = "demo-event-bus"

    @property
    def database_sync_url(self) -> str:
        """Synchronous database URL derived from DATABASE_URL for use with psycopg2."""
        return self.database_url.replace("+asyncpg", "+psycopg2", 1)


settings = Settings()
