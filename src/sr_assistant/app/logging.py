from __future__ import annotations

import json
import sys
import typing as t
import uuid
from datetime import timezone

import logfire
from loguru import logger

if t.TYPE_CHECKING:
    from loguru import Message

import sr_assistant.app.utils as ut
from sr_assistant.app.database import (
    AsyncSQLModelSession,
    SQLModelSession,
    asession_factory,
    async_sessionmaker,
    session_factory,
    sessionmaker,
)
from sr_assistant.core.models import LogRecord
from sr_assistant.core.types import LogLevel

LOGGING_FORMAT = "{time:!UTC} | {level: <8} | {name}:{function}:{line} | {message} | {extra} | t:{thread.name}:{thread.id}"

logger.info("Initializing logging...")


class PostgresLogSink:
    """PostgreSQL sink for loguru that uses SQLModel."""

    def __init__(  # pyright: ignore [reportMissingSuperCall] # there's no super ...
        self,
        session_factory: sessionmaker[SQLModelSession] = session_factory,
    ) -> None:
        """Initialize the sink with database configuration.

        Args:
            session_factory (async_sessionmaker[SQLModelSession], optional):
                SQLModel session factory. Default is `session_factory`.
        """
        self.session_factory = session_factory

    def __call__(self, message: Message) -> None:
        """Process and store a log record.

        Handler calling this should be configured with ``serialize=True``.
        """
        serialized = json.loads(message)
        review_id = message.record["extra"].get("review_id")
        if not isinstance(review_id, uuid.UUID):
            review_id = uuid.UUID(review_id) if ut.is_uuid(review_id) else None
        record = LogRecord(
            timestamp=message.record["time"].astimezone(timezone.utc),
            level=LogLevel(message.record["level"].name),
            message=message.record["message"],
            module=message.record["module"],
            name=message.record["name"],  # pyright: ignore [reportCallIssue]
            function=serialized.get("function"),
            line=message.record["line"],
            extra=serialized.get("extra", {}),
            process=f"{message.record["process"].name}:{message.record['process'].id}",  # pyright: ignore [reportCallIssue]
            thread=f"{message.record["thread"].name}:{message.record['thread'].id}",  # pyright: ignore [reportCallIssue]
            review_id=review_id,
            exception=serialized.get("exception"),
            record=serialized,  # pyright: ignore [reportCallIssue]
        )

        with self.session_factory.begin() as session:
            session.add(record)


class AsyncPostgresLogSink:
    """A non-blocking PostgreSQL sink for loguru that uses SQLModel."""

    def __init__(  # pyright: ignore [reportMissingSuperCall] # there's no super ...
        self,
        asession_factory: async_sessionmaker[AsyncSQLModelSession] = asession_factory,
    ) -> None:
        """Initialize the sink with database configuration.

        Args:
            asession_factory (async_sessionmaker[AsyncSQLModelSession], optional):
                SQLModel session factory. Default is `asession_factory`.
        """
        self.asession_factory = asession_factory

    async def __call__(self, message: Message) -> None:
        """Process and store a log record.

        This method is called by loguru for each log record. It creates
        a LogRecord model and stores it in the database asynchronously.
        """
        serialized = json.loads(message)
        review_id = message.record["extra"].get("review_id")
        if not isinstance(review_id, uuid.UUID):
            review_id = uuid.UUID(review_id) if ut.is_uuid(review_id) else None
        record = LogRecord(
            timestamp=message.record["time"].astimezone(timezone.utc),
            level=LogLevel(message.record["level"].name),
            message=message.record["message"],
            module=message.record["module"],
            name=message.record["name"],  # pyright: ignore [reportCallIssue]
            function=serialized.get("function"),
            line=message.record["line"],
            extra=serialized.get("extra", {}),
            process=f"{message.record["process"].name}:{message.record['process'].id}",  # pyright: ignore [reportCallIssue]
            thread=f"{message.record["thread"].name}:{message.record['thread'].id}",  # pyright: ignore [reportCallIssue]
            review_id=review_id,
            exception=serialized.get("exception"),
            record=serialized,  # pyright: ignore [reportCallIssue]
        )

        async with self.asession_factory.begin() as session:
            session.add(record)


def configure_logging() -> None:
    """Configure logging.

    Must be called before models/schemas are imported.
    """
    logfire.configure(service_name="sr-assistant", environment="prototype")
    logfire.instrument_pydantic()
    logfire.instrument_sqlalchemy(enable_commenter=True)
    logfire.instrument_openai()
    logfire.instrument_anthropic()
    logfire.instrument_psycopg("psycopg")
    logfire.instrument_system_metrics()
    logfire.instrument_httpx(capture_all=True)
    logfire.log_slow_async_callbacks()

    logger.remove()

    sync_pg_sink = PostgresLogSink()
    # async_pg_sink = AsyncPostgresLogSink()

    # TODO: read level from config
    logger.configure(
        handlers=[
            dict(  # noqa: C408
                sink=sys.stderr,
                level="DEBUG",
                format=LOGGING_FORMAT,
                enqueue=True,
                catch=True,
                colorize=True,
            ),
            dict(  # noqa: C408
                sink="app.log", level="DEBUG", enqueue=True, catch=True, serialize=True
            ),
            dict(  # noqa: C408
                sink=sync_pg_sink,
                level="DEBUG",
                enqueue=True,
                catch=True,
                serialize=True,
            ),
            logfire.loguru_handler(),
        ],  # pyright: ignore [reportArgumentType]
    )
    logger.info("Logging initialized.")
