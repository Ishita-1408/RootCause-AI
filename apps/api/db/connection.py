"""Database connection management for RootCause AI."""

import logging
from collections.abc import Generator
from contextlib import contextmanager

import psycopg
from psycopg import Connection

from apps.api.config import get_settings

logger = logging.getLogger(__name__)


def _create_connection() -> Connection:
    """Create a raw psycopg connection using configured settings."""
    settings = get_settings()

    if settings.database_url:
        return psycopg.connect(
            conninfo=settings.database_url,
            connect_timeout=settings.database_connect_timeout,
        )

    return psycopg.connect(
        host=settings.database_host,
        port=settings.database_port,
        dbname=settings.database_name,
        user=settings.database_user,
        password=settings.database_password,
        connect_timeout=settings.database_connect_timeout,
    )


@contextmanager
def get_db_connection() -> Generator[Connection, None, None]:
    """Provide a synchronous PostgreSQL database connection context.

    Ensures connection is closed deterministically.
    Never exposes credentials in logs.
    """
    conn = _create_connection()
    try:
        yield conn
    finally:
        conn.close()


def check_database_connection() -> bool:
    """Connect to PostgreSQL and execute SELECT 1 to verify connectivity.

    Returns True if connection succeeds, False otherwise.
    Never prints or logs database credentials.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                result = cur.fetchone()
                return result is not None and result[0] == 1
    except Exception as e:
        logger.warning(f"Database connectivity check failed (type={type(e).__name__})")
        return False
