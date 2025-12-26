#!/usr/bin/env python3
"""
DB Doctor - Database Connection Diagnostic Tool

Constitutional: This script verifies DB connection before any work begins.
Run this before starting API or running E2E tests.

Usage:
    python apps/api/scripts/db_doctor.py

Exit codes:
    0 - Connection successful + tables verified
    1 - Connection failed (see diagnostic output)
"""
import os
import sys
from typing import Dict, List, Tuple

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def get_env_config() -> Dict[str, str]:
    """Read DB configuration from environment."""
    # Read from DB_* first (new contract), fallback to POSTGRES_* (legacy)
    config = {
        'host': os.getenv("DB_HOST") or os.getenv("POSTGRES_HOST", "127.0.0.1"),
        'port': os.getenv("DB_PORT") or os.getenv("POSTGRES_PORT", "5433"),
        'database': os.getenv("DB_NAME") or os.getenv("POSTGRES_DB", "inca_rag_final"),
        'user': os.getenv("DB_USER") or os.getenv("POSTGRES_USER", "postgres"),
        'password': os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD", "postgres"),
    }
    return config


def mask_password(password: str) -> str:
    """Mask password for logging."""
    if not password:
        return "MISSING"
    return '*' * len(password)


def check_connection(config: Dict[str, str]) -> Tuple[bool, str]:
    """
    Test database connection.

    Returns:
        (success, message)
    """
    try:
        import psycopg2
    except ImportError:
        return False, "❌ psycopg2 not installed (run: pip install psycopg2-binary)"

    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=int(config['port']),
            database=config['database'],
            user=config['user'],
            password=config['password'],
            connect_timeout=5
        )

        # Test query
        cur = conn.cursor()
        cur.execute('SELECT 1 as test')
        result = cur.fetchone()
        cur.close()
        conn.close()

        if result == (1,):
            return True, "✅ Connection successful"
        else:
            return False, f"❌ Query returned unexpected result: {result}"

    except Exception as e:
        error_msg = str(e)

        # Provide diagnostic hints
        hints = []
        if "password authentication failed" in error_msg:
            hints.append("  💡 Hint: DB_PASSWORD mismatch")
            hints.append("     - Check container: docker exec inca_pg_step14 env | grep POSTGRES_PASSWORD")
            hints.append("     - Check .env file or export DB_PASSWORD=...")

        if "could not connect to server" in error_msg:
            hints.append("  💡 Hint: DB connection refused")
            hints.append("     - Check container: docker ps | grep inca_pg")
            hints.append("     - Check port: DB_PORT=5433 (not 5432)")

        if "does not exist" in error_msg:
            hints.append("  💡 Hint: Database name mismatch")
            hints.append("     - Check container: docker exec inca_pg_step14 env | grep POSTGRES_DB")
            hints.append("     - Expected: DB_NAME=inca_rag_final")

        if "::1" in error_msg or "IPv6" in error_msg:
            hints.append("  💡 Hint: IPv6 connection issue")
            hints.append("     - Try: export DB_HOST=127.0.0.1 (not localhost)")

        hint_text = "\n".join(hints) if hints else ""
        return False, f"❌ Connection failed: {error_msg}\n{hint_text}"


def check_tables(config: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    Check existence of critical tables.

    Returns:
        (success, messages)
    """
    import psycopg2

    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=int(config['port']),
            database=config['database'],
            user=config['user'],
            password=config['password'],
            connect_timeout=5
        )

        cur = conn.cursor()

        # Check critical tables
        critical_tables = [
            'proposal_coverage_universe',
            'proposal_coverage_mapped',
            'coverage_standard',
        ]

        messages = []
        all_exist = True

        for table in critical_tables:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = %s
                )
            """, (table,))
            exists = cur.fetchone()[0]

            if exists:
                # Count rows
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                messages.append(f"  ✅ {table}: {count} rows")
            else:
                messages.append(f"  ❌ {table}: NOT FOUND")
                all_exist = False

        cur.close()
        conn.close()

        return all_exist, messages

    except Exception as e:
        return False, [f"  ❌ Table check failed: {e}"]


def main():
    """Run diagnostics."""
    print("=" * 60)
    print("DB Doctor - Database Connection Diagnostics")
    print("=" * 60)
    print()

    # Step 1: Show config
    print("📋 Configuration (from environment):")
    config = get_env_config()
    print(f"  DB_HOST:     {config['host']}")
    print(f"  DB_PORT:     {config['port']}")
    print(f"  DB_NAME:     {config['database']}")
    print(f"  DB_USER:     {config['user']}")
    print(f"  DB_PASSWORD: {mask_password(config['password'])}")
    print()

    # Step 2: Test connection
    print("🔌 Testing connection...")
    success, message = check_connection(config)
    print(message)
    print()

    if not success:
        print("=" * 60)
        print("❌ DB Doctor: Connection failed")
        print("=" * 60)
        print()
        print("Common fixes:")
        print("  1. Check container is running:")
        print("     docker ps | grep inca_pg")
        print()
        print("  2. Verify container credentials:")
        print("     docker exec inca_pg_step14 env | grep POSTGRES")
        print()
        print("  3. Set environment variables:")
        print("     export DB_HOST=127.0.0.1")
        print("     export DB_PORT=5433")
        print("     export DB_NAME=inca_rag_final")
        print("     export DB_USER=postgres")
        print("     export DB_PASSWORD=postgres")
        print()
        print("  4. Or create .env file (see apps/api/.env.example)")
        print()
        sys.exit(1)

    # Step 3: Check tables
    print("🗂️  Checking critical tables...")
    tables_ok, table_messages = check_tables(config)
    for msg in table_messages:
        print(msg)
    print()

    # Final verdict
    print("=" * 60)
    if tables_ok:
        print("✅ DB Doctor: All checks passed")
        print("=" * 60)
        print()
        print("You can now start the API:")
        print("  cd apps/api")
        print("  uvicorn app.main:app --port 8001")
        print()
        sys.exit(0)
    else:
        print("⚠️  DB Doctor: Connection OK, but some tables missing")
        print("=" * 60)
        print()
        print("This may be expected if you haven't run data ingestion yet.")
        print("Check ingestion scripts or migration files.")
        print()
        sys.exit(0)  # Not a hard failure


if __name__ == '__main__':
    main()
