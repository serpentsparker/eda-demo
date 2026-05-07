"""Alembic migration environment — async mode with asyncpg."""

import asyncio

from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from alembic import context
from app.config import settings
from app.models.jobs import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def do_run_migrations(connection: AsyncConnection) -> None:
    """Configure and execute migrations against the given connection."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Open an async engine connection and drive the migration run."""
    engine = create_async_engine(settings.database_url)
    async with engine.connect() as conn:
        await conn.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    """Entry point called by Alembic for online (connected) migrations."""
    asyncio.run(run_async_migrations())


run_migrations_online()
