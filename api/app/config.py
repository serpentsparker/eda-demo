"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """API service settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # AWS
    localstack_endpoint: str | None = None

    # EventBridge
    eventbridge_bus_name: str = "demo-event-bus"

    # Database
    database_url: str = (
        "postgresql+asyncpg://eda_user:eda_pass@localhost:5432/eda_demo"  # pragma: allowlist secret
    )


settings = Settings()
