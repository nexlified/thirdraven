import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlmodel import SQLModel

# Import all models so SQLModel.metadata is fully populated
import app.models.asset  # noqa: F401
import app.models.asset_event  # noqa: F401
import app.models.asset_extensions  # noqa: F401
import app.models.communication  # noqa: F401
import app.models.contact  # noqa: F401
import app.models.document  # noqa: F401
import app.models.event  # noqa: F401
import app.models.followup  # noqa: F401
import app.models.goal  # noqa: F401
import app.models.household  # noqa: F401
import app.models.import_job  # noqa: F401
import app.models.import_row  # noqa: F401
import app.models.interaction  # noqa: F401
import app.models.iso_reference  # noqa: F401
import app.models.life_event  # noqa: F401
import app.models.loan  # noqa: F401
import app.models.note  # noqa: F401
import app.models.observation  # noqa: F401
import app.models.organization  # noqa: F401
import app.models.person  # noqa: F401
import app.models.person_extensions  # noqa: F401
import app.models.person_life_event  # noqa: F401
import app.models.person_relationship  # noqa: F401
import app.models.raven_log  # noqa: F401
import app.models.raven_question  # noqa: F401
import app.models.reference  # noqa: F401
import app.models.relationship  # noqa: F401
import app.models.reminder  # noqa: F401
import app.models.subscription  # noqa: F401
import app.models.task  # noqa: F401
import app.models.transaction  # noqa: F401
import app.models.tracked_record  # noqa: F401
import app.models.user  # noqa: F401
import app.models.vocabulary  # noqa: F401
from app.core.config import get_settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()

config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
