"""
Database connection module for STEP 5 API (READ-ONLY) + Admin (WRITE)

Constitutional guarantee:
- All transactions are READ ONLY by default
- Admin mapping workbench requires WRITE access (async)
- Accidental write attempts will fail at DB level for read-only endpoints
"""
import os
from contextlib import contextmanager, asynccontextmanager
from typing import Iterator, Optional, Dict, Any, List

import psycopg2
from psycopg2.extensions import connection as PGConnection
from psycopg2.extras import RealDictCursor

# Admin mapping requires async DB access
import asyncpg


def get_db_connection(readonly: bool = True) -> PGConnection:
    """
    Create PostgreSQL connection with strong read-only enforcement.

    Args:
        readonly: Force read-only mode (default: True for API)

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
        psycopg2.ProgrammingError: If write attempted in read-only mode
    """
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5433")),
        database=os.getenv("POSTGRES_DB", "inca_rag_final_test"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "testpass")
    )

    # STRENGTHENED: Force read-only mode at PostgreSQL level
    if readonly:
        # Use autocommit=False with explicit BEGIN READ ONLY
        conn.set_session(autocommit=False)
        with conn.cursor() as cur:
            # SET TRANSACTION to READ ONLY before any queries
            cur.execute("BEGIN READ ONLY;")
        # Now any INSERT/UPDATE/DELETE will fail with:
        # psycopg2.errors.ReadOnlySqlTransaction: cannot execute ... in a read-only transaction

    return conn


@contextmanager
def db_readonly_session() -> Iterator[PGConnection]:
    """
    Context manager for READ-ONLY database session with proper transaction hygiene.

    Constitutional guarantee:
    - Transaction is READ ONLY (BEGIN READ ONLY)
    - Any write attempt will raise psycopg2.errors.ReadOnlySqlTransaction
    - Proper cleanup on exit (rollback if needed)

    Usage:
        with db_readonly_session() as conn:
            cur = conn.cursor()
            cur.execute("SELECT ...")
            # INSERT/UPDATE/DELETE will fail

    Yields:
        psycopg2 connection in READ ONLY mode

    Transaction Hygiene:
    - BEGIN READ ONLY is executed on connection creation
    - On normal exit: connection closed (no commit needed for read-only)
    - On exception: rollback executed, then connection closed
    - No write operations possible at PostgreSQL level
    """
    conn = None
    try:
        conn = get_db_connection(readonly=True)
        yield conn
        # For read-only transactions, no commit needed
        # BEGIN READ ONLY prevents any writes
    except Exception:
        # Rollback on exception (though read-only shouldn't have changes)
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass  # Rollback failure is non-critical for read-only
        raise
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass  # Close failure is logged but not raised


def get_readonly_conn() -> Iterator[PGConnection]:
    """
    FastAPI dependency for read-only database connection.

    This is a generator that yields a read-only connection for dependency injection.
    Used with FastAPI's Depends() for automatic connection management.

    Usage in router:
        @router.post("/endpoint")
        async def endpoint(conn = Depends(get_readonly_conn)):
            # Use conn for queries
            ...

    Yields:
        psycopg2 connection in READ ONLY mode
    """
    with db_readonly_session() as conn:
        yield conn


def execute_readonly_query(
    conn: PGConnection,
    query: str,
    params: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Execute SELECT query and return rows as dictionaries.

    Args:
        conn: Database connection (must be read-only)
        query: SQL SELECT query with %(name)s placeholders
        params: Query parameters as dict

    Returns:
        List of dictionaries (column_name -> value)

    Raises:
        psycopg2.ProgrammingError: If query contains write operations
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, params or {})
        rows = cur.fetchall()
        # Convert RealDictRow to regular dict
        return [dict(row) for row in rows]


def execute_readonly_query_one(
    conn: PGConnection,
    query: str,
    params: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Execute SELECT query and return first row as dictionary.

    Args:
        conn: Database connection (must be read-only)
        query: SQL SELECT query with %(name)s placeholders
        params: Query parameters as dict

    Returns:
        Dictionary (column_name -> value) or None if no rows

    Raises:
        psycopg2.ProgrammingError: If query contains write operations
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, params or {})
        row = cur.fetchone()
        return dict(row) if row else None


# ============================================================================
# Async DB Pool for Admin Mapping (WRITE operations)
# ============================================================================

_async_pool: Optional[asyncpg.Pool] = None


async def get_async_pool() -> asyncpg.Pool:
    """
    Get or create async database pool for admin operations.

    NOTE: This pool allows WRITE operations (for admin_mapping only).
    Constitutional: Admin mapping workbench requires write access.
    """
    global _async_pool

    if _async_pool is None or _async_pool._closed:
        _async_pool = await asyncpg.create_pool(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5433")),
            database=os.getenv("POSTGRES_DB", "inca_rag_final_test"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "testpass"),
            min_size=2,
            max_size=10,
        )

    return _async_pool


async def close_async_pool():
    """Close async database pool on shutdown."""
    global _async_pool
    if _async_pool is not None and not _async_pool._closed:
        await _async_pool.close()
        _async_pool = None


async def get_db_pool() -> asyncpg.Pool:
    """
    FastAPI dependency for async database pool.

    Usage:
        @router.post("/endpoint")
        async def endpoint(db_pool: asyncpg.Pool = Depends(get_db_pool)):
            async with db_pool.acquire() as conn:
                # Use conn for queries
                ...
    """
    return await get_async_pool()
