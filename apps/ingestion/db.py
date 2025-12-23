"""
Database connection and transaction management.
"""
import os
from contextlib import contextmanager
from typing import Iterator

import psycopg2
from psycopg2.extensions import connection as PGConnection


def get_db_connection() -> PGConnection:
    """
    Create PostgreSQL connection.

    Connection parameters from environment variables:
    - POSTGRES_HOST (default: localhost)
    - POSTGRES_PORT (default: 5433)
    - POSTGRES_DB (default: inca_rag_final_test)
    - POSTGRES_USER (default: postgres)
    - POSTGRES_PASSWORD (required)

    Returns:
        psycopg2 connection object

    Raises:
        psycopg2.OperationalError: If connection fails
    """
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5433")),
        database=os.getenv("POSTGRES_DB", "inca_rag_final_test"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "testpass")
    )
    return conn


@contextmanager
def db_transaction() -> Iterator[PGConnection]:
    """
    Context manager for database transaction.

    Usage:
        with db_transaction() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO ...")
            # Auto-commit on success, rollback on exception

    Yields:
        psycopg2 connection with auto-commit/rollback
    """
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute_query(conn: PGConnection, query: str, params: tuple = ()) -> list:
    """
    Execute SELECT query and return all rows.

    Args:
        conn: Database connection
        query: SQL SELECT query
        params: Query parameters (for %s placeholders)

    Returns:
        List of tuples (rows)
    """
    with conn.cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def execute_write(conn: PGConnection, query: str, params: tuple = ()) -> None:
    """
    Execute INSERT/UPDATE/DELETE query.

    Args:
        conn: Database connection
        query: SQL write query
        params: Query parameters (for %s placeholders)
    """
    with conn.cursor() as cur:
        cur.execute(query, params)
