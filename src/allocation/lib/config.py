from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.allocation.adapters import orm
from src.allocation.lib import settings

_SETTINGS = settings.get_settings()

get_session = sessionmaker(bind=create_engine(url=_SETTINGS.database.mysql_uri))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await configure_logging()
    orm.start_mappers()

    yield

    # Clean Services


async def configure_logging() -> None:
    """Set the basic configuration for structlog library.
    More info: https://www.structlog.org/en/stable/configuration.html
    """
    processors: list[structlog.types.Processor] = [
        structlog.processors.add_log_level,
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(
            fmt=_SETTINGS.logging.timestamp_format,
            utc=_SETTINGS.logging.timestamp_use_utc,
        ),
    ]
    if _SETTINGS.is_local_environment:
        processors.append(
            structlog.dev.ConsoleRenderer(pad_event=5, sort_keys=False)
        )
    else:
        processors.extend(
            [
                structlog.processors.dict_tracebacks,
                structlog.processors.KeyValueRenderer(
                    key_order=_SETTINGS.logging.key_render_order
                ),
            ]
        )

    structlog.configure(
        processors=processors,
        cache_logger_on_first_use=True,
    )