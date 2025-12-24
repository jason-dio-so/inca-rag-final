#!/usr/bin/env python3
"""
STEP 6-B Phase 3-2: Initialize coverage_standard from Excel

Data Source (ABSOLUTE):
- data/담보명mapping자료.xlsx

Purpose:
- Create coverage_standard table with canonical coverage codes
- Create coverage_alias table with insurer-specific aliases
- This is the ONLY source of truth for canonical coverage codes
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv

load_dotenv()

EXCEL_PATH = "data/담보명mapping자료.xlsx"

def get_db_connection():
    """Get database connection from environment variables with Phase 3 fallback"""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5433")),
        database=os.getenv("DB_NAME", "inca_rag_final"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres")
    )

def create_tables(conn):
    """
    Verify coverage_standard and coverage_alias exist (created by 000_base_schema.sql)
    This function now only checks existence, does NOT create tables
    """
    with conn.cursor() as cur:
        # Check if tables exist
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'coverage_standard'
            )
        """)
        std_exists = cur.fetchone()[0]

        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'coverage_alias'
            )
        """)
        alias_exists = cur.fetchone()[0]

        if not std_exists or not alias_exists:
            raise RuntimeError(
                "Tables not found. Run 000_base_schema.sql first:\n"
                "psql -h localhost -p 5433 -U postgres -d inca_rag_final -f migrations/step6b/000_base_schema.sql"
            )

        print("✅ Tables verified: coverage_standard, coverage_alias")

def load_excel_data():
    """Load and parse Excel file"""
    df = pd.read_excel(EXCEL_PATH)

    # Extract canonical coverage_standard
    canonical = df[['cre_cvr_cd', '신정원코드명']].drop_duplicates()
    canonical.columns = ['coverage_code', 'coverage_name']

    # Extract aliases
    aliases = df[['cre_cvr_cd', 'ins_cd', '보험사명', '담보명(가입설계서)']].copy()
    aliases.columns = ['coverage_code', 'insurer_code', 'insurer_name', 'alias_name']

    return canonical, aliases

def insert_coverage_standard(conn, canonical_df):
    """Upsert canonical coverage codes"""
    with conn.cursor() as cur:
        records = canonical_df.to_records(index=False)
        execute_values(
            cur,
            """
            INSERT INTO coverage_standard (coverage_code, coverage_name)
            VALUES %s
            ON CONFLICT (coverage_code) DO UPDATE
            SET coverage_name = EXCLUDED.coverage_name,
                updated_at = CURRENT_TIMESTAMP
            """,
            records
        )
        conn.commit()
        print(f"✅ Upserted {len(canonical_df)} canonical coverage codes")

def insert_coverage_alias(conn, aliases_df):
    """Insert insurer-specific aliases"""
    with conn.cursor() as cur:
        records = aliases_df.to_records(index=False)
        execute_values(
            cur,
            """
            INSERT INTO coverage_alias (coverage_code, insurer_code, insurer_name, alias_name)
            VALUES %s
            ON CONFLICT (coverage_code, insurer_code, alias_name) DO NOTHING
            """,
            records
        )
        conn.commit()
        print(f"✅ Inserted {len(aliases_df)} coverage aliases")

def verify_data(conn):
    """Verify inserted data"""
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM coverage_standard")
        std_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM coverage_alias")
        alias_count = cur.fetchone()[0]

        cur.execute("""
            SELECT coverage_code, coverage_name
            FROM coverage_standard
            ORDER BY coverage_code
            LIMIT 5
        """)
        samples = cur.fetchall()

        print(f"\n📊 Verification:")
        print(f"   coverage_standard: {std_count} records")
        print(f"   coverage_alias: {alias_count} records")
        print(f"\n   Sample coverage_standard:")
        for code, name in samples:
            print(f"      {code}: {name}")

def main():
    print(f"🚀 Initializing coverage_standard from {EXCEL_PATH}")

    # Load data
    canonical, aliases = load_excel_data()
    print(f"📖 Loaded {len(canonical)} canonical codes, {len(aliases)} aliases")

    # Connect and initialize
    conn = get_db_connection()
    try:
        create_tables(conn)
        insert_coverage_standard(conn, canonical)
        insert_coverage_alias(conn, aliases)
        verify_data(conn)
        print("\n✅ coverage_standard initialization complete")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
