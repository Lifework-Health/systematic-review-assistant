from __future__ import annotations

import os
import re
from logging.config import fileConfig
from typing import NoReturn
from urllib.parse import parse_qs, urlparse

from dotenv import find_dotenv, load_dotenv
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

from alembic import context
from sr_assistant.core.models import *

ENV_TO_DOTENV = {
    "local": ".env.local",
    "test": ".env.test",
    "prototype": ".env",
}


def mask_pg_dsn(dsn: str) -> str:
    """Mask sensitive parts of a PostgreSQL DSN.

    Examples:
        postgresql://user:pass@host/db?sslmode=verify-full
        -> postgresql://****:****@host/db?sslmode=verify-full

        postgresql://user:pass@host/db?password=secret&sslmode=verify-full
        -> postgresql://****:****@host/db?password=****&sslmode=verify-full
    """
    if "://" in dsn:
        parsed = urlparse(dsn)
        # Start with scheme
        masked = f"{parsed.scheme}://"

        # Add masked credentials if present
        if parsed.username or parsed.password:
            masked += "****:****"
        masked += f"@{parsed.hostname}"

        # Add port if present
        if parsed.port:
            masked += f":{parsed.port}"

        # Add path
        masked += parsed.path

        # Handle query params - mask sensitive ones
        if parsed.query:
            params = parse_qs(parsed.query)
            masked_params = []
            for k, v in params.items():
                # Mask values of sensitive parameters
                if k.lower() in {"password", "user", "username", "credentials"}:
                    masked_params.append(f"{k}=****")
                else:
                    masked_params.append(f"{k}={v[0]}")
            masked += "?" + "&".join(masked_params)

        return masked
    # Handle key=value format
    return re.sub(r"(user|password|username|credentials)=[^'\s&]+", r"\1=****", dsn)


valid_envs = ENV_TO_DOTENV.keys()


def die(msg: str) -> NoReturn:
    msg = f"ERROR: {msg}"
    raise SystemExit(msg)


env = os.getenv(
    "ENVIRONMENT",
    os.getenv("SRA_ENVIRONMENT", os.getenv("SRA_ENV", os.getenv("ENV", ""))),
)
if env not in valid_envs:
    die(f"Unknown (SRA_)ENVIRONMENT|(SRA_)ENV: got {env!r}, want {valid_envs!r}")

print(f"env: {env!r}")
env_file = find_dotenv(f"{ENV_TO_DOTENV[env]}")

if not env_file:
    die(f"missing .env file for env {env!r} (expected: {ENV_TO_DOTENV[env]})")

print(f"loading {env_file!r}")
load_dotenv(env_file, override=True)

# Safety checks
pg_dsn: str = os.getenv("SRA_DATABASE_URL", os.getenv("DATABASE_URL", ""))
if not pg_dsn:
    die("SRA_DATABASE_URL|DATABASE_URL environment variable is required")
pg_dsn = pg_dsn.replace("%", "%%")
masked_pg_dsn = mask_pg_dsn(pg_dsn)
print(f"pg_dsn: {masked_pg_dsn}")

if env in ["prototype"]:
    # Matches Supabase production database URL pattern
    prod_pattern = r"pooler.supabase\.com.*/postgres$"
    if not re.search(prod_pattern, pg_dsn):
        die(
            f"ENVIRONMENT is {env!r} but production database URL not detected, got {masked_pg_dsn}, expected {prod_pattern}"
        )
    if not pg_dsn.startswith("postgresql+psycopg://"):
        die(
            f"env {env!r} pg_dsn does not start with 'postgresql+psycopg://', got {masked_pg_dsn}"
        )
elif env == "test":
    # Matches Supabase test database URL pattern
    test_pattern = r"pooler.supabase\.com.*/sra_integration_test.*"
    if not re.search(test_pattern, pg_dsn):
        die(
            rf"ENVIRONMENT is '{env!r}' but test database URL not detected, got {masked_pg_dsn}, expected {test_pattern}"
        )
    if not pg_dsn.startswith("postgresql+psycopg://"):
        die(
            f"env {env!r} pg_dsn does not start with 'postgresql+psycopg://', got {masked_pg_dsn}"
        )

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

config.set_main_option("sqlalchemy.url", pg_dsn)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# Note: SQlModel.metadata has access to all tables inheriting from SQLModel
target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


IGNORE_TABLES = [
    # LangGraph Postgres Checkpointer tables, ideally in separate schema
    "checkpoint_blobs",
    "checkpoints",
    "checkpoint_writes",
    "checkpoint_migrations",
]


def include_object(object, name, type_, reflected, compare_to) -> bool:
    """Whether to include an object in the schema diff."""
    return not (
        (
            type_ == "table"
            and (name in IGNORE_TABLES or object.info.get("skip_autogenerate", False))
        )
        or (type_ == "column" and object.info.get("skip_autogenerate", False))
    )


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
