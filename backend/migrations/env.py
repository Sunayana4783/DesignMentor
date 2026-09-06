import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool, create_engine
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import models so they are registered
from app.db.base import Base
import app.models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Get DB URL from environment — convert async URL to sync for alembic
db_url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))

# Convert asyncpg URL to psycopg2 for alembic (sync)
sync_url = (
    db_url
    .replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    .replace("postgres://", "postgresql+psycopg2://")
    .replace("postgresql://", "postgresql+psycopg2://")
)

config.set_main_option("sqlalchemy.url", sync_url)


def run_migrations_offline() -> None:
    context.configure(
        url=sync_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(sync_url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
