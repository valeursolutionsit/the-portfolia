import os
from pathlib import Path
from dotenv import load_dotenv
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from backend.app.database import Base
from backend.app.models import *  # noqa: F401,F403

# Explicitly find and load the .env file from the project root directory
env_path = Path(__file__).resolve().parent.parent / ".env.example"
load_dotenv(dotenv_path=env_path)

config = context.config

# Fetch and verify DATABASE_URL
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError(f"DATABASE_URL not found! Checked path: {env_path}")

config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = config.get_main_option("sqlalchemy.url")
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()