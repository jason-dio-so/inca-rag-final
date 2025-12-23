"""
Validation and report generation.

Generates reports to verify:
- Ingestion pipeline completion
- coverage_standard integrity
- Synthetic chunk policy compliance
- UNMAPPED coverage detection
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from psycopg2.extensions import connection as PGConnection


def get_document_stats(conn: PGConnection) -> Dict[str, Any]:
    """Get document statistics by insurer and document type."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                i.insurer_code,
                d.document_type,
                COUNT(*) as doc_count
            FROM document d
            JOIN product p ON d.product_id = p.product_id
            JOIN insurer i ON p.insurer_id = i.insurer_id
            GROUP BY i.insurer_code, d.document_type
            ORDER BY i.insurer_code, d.document_type
        """)

        return [
            {"insurer": row[0], "doc_type": row[1], "count": row[2]}
            for row in cur.fetchall()
        ]


def get_chunk_stats(conn: PGConnection) -> Dict[str, int]:
    """Get chunk statistics."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE is_synthetic = false) as original_chunks,
                COUNT(*) FILTER (WHERE is_synthetic = true) as synthetic_chunks,
                COUNT(*) as total_chunks
            FROM chunk
        """)

        row = cur.fetchone()
        return {
            "original_chunks": row[0] or 0,
            "synthetic_chunks": row[1] or 0,
            "total_chunks": row[2] or 0
        }


def get_alias_stats(conn: PGConnection) -> Dict[str, Any]:
    """Get coverage_alias mapping statistics."""
    with conn.cursor() as cur:
        # Total entities
        cur.execute("SELECT COUNT(*) FROM chunk_entity")
        total_entities = cur.fetchone()[0] or 0

        # Mapped entities
        cur.execute("SELECT COUNT(*) FROM chunk_entity WHERE coverage_code IS NOT NULL")
        mapped_entities = cur.fetchone()[0] or 0

        # Unmapped entities
        unmapped = total_entities - mapped_entities

        # Success rate
        success_rate = (mapped_entities / total_entities * 100) if total_entities > 0 else 0

        return {
            "total_entities": total_entities,
            "mapped": mapped_entities,
            "unmapped": unmapped,
            "success_rate": round(success_rate, 2)
        }


def get_unmapped_coverages(conn: PGConnection, limit: int = 20) -> list:
    """Get top unmapped coverage names."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                entity_value->>'coverage_name' as coverage_name,
                COUNT(*) as occurrence_count
            FROM chunk_entity
            WHERE coverage_code IS NULL
              AND entity_value->>'coverage_name' IS NOT NULL
            GROUP BY entity_value->>'coverage_name'
            ORDER BY COUNT(*) DESC
            LIMIT %s
        """, (limit,))

        return [
            {"coverage_name": row[0], "count": row[1]}
            for row in cur.fetchall()
        ]


def get_amount_context_distribution(conn: PGConnection) -> Dict[str, int]:
    """Get distribution of amount context types."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                context_type,
                COUNT(*) as count
            FROM amount_entity
            GROUP BY context_type
            ORDER BY count DESC
        """)

        return {row[0]: row[1] for row in cur.fetchall()}


def check_coverage_standard_violations(conn: PGConnection) -> Dict[str, Any]:
    """Check for coverage_standard policy violations."""
    violations = {}

    with conn.cursor() as cur:
        # Check 1: chunk_entity with invalid coverage_code
        cur.execute("""
            SELECT COUNT(*)
            FROM chunk_entity ce
            LEFT JOIN coverage_standard cs ON ce.coverage_code = cs.coverage_code
            WHERE ce.coverage_code IS NOT NULL
              AND cs.coverage_code IS NULL
        """)
        violations["chunk_entity_invalid_codes"] = cur.fetchone()[0] or 0

        # Check 2: amount_entity with invalid coverage_code
        cur.execute("""
            SELECT COUNT(*)
            FROM amount_entity ae
            LEFT JOIN coverage_standard cs ON ae.coverage_code = cs.coverage_code
            WHERE ae.coverage_code IS NOT NULL
              AND cs.coverage_code IS NULL
        """)
        violations["amount_entity_invalid_codes"] = cur.fetchone()[0] or 0

        # Check 3: coverage_alias with invalid coverage_id
        cur.execute("""
            SELECT COUNT(*)
            FROM coverage_alias ca
            LEFT JOIN coverage_standard cs ON ca.coverage_id = cs.coverage_id
            WHERE cs.coverage_id IS NULL
        """)
        violations["coverage_alias_invalid_ids"] = cur.fetchone()[0] or 0

    return violations


def check_synthetic_policy_violations(conn: PGConnection) -> Dict[str, int]:
    """Check for synthetic chunk policy violations."""
    violations = {}

    with conn.cursor() as cur:
        # Check 1: Synthetic chunk without source
        cur.execute("""
            SELECT COUNT(*)
            FROM chunk
            WHERE is_synthetic = true
              AND synthetic_source_chunk_id IS NULL
        """)
        violations["synthetic_without_source"] = cur.fetchone()[0] or 0

        # Check 2: Non-synthetic with source (invalid)
        cur.execute("""
            SELECT COUNT(*)
            FROM chunk
            WHERE is_synthetic = false
              AND synthetic_source_chunk_id IS NOT NULL
        """)
        violations["non_synthetic_with_source"] = cur.fetchone()[0] or 0

    return violations


def generate_validation_report(conn: PGConnection, output_dir: Path) -> Path:
    """
    Generate comprehensive validation report.

    Args:
        conn: Database connection
        output_dir: Output directory (artifacts/ingestion/)

    Returns:
        Path to generated report directory
    """
    # Create timestamped report directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = output_dir / timestamp
    report_dir.mkdir(parents=True, exist_ok=True)

    # Collect statistics
    report = {
        "timestamp": timestamp,
        "document_stats": get_document_stats(conn),
        "chunk_stats": get_chunk_stats(conn),
        "alias_stats": get_alias_stats(conn),
        "unmapped_coverages": get_unmapped_coverages(conn),
        "amount_context_distribution": get_amount_context_distribution(conn),
        "coverage_standard_violations": check_coverage_standard_violations(conn),
        "synthetic_policy_violations": check_synthetic_policy_violations(conn)
    }

    # Check for critical violations
    critical_violations = []

    cs_violations = report["coverage_standard_violations"]
    if any(v > 0 for v in cs_violations.values()):
        critical_violations.append("coverage_standard FK violations detected")

    syn_violations = report["synthetic_policy_violations"]
    if any(v > 0 for v in syn_violations.values()):
        critical_violations.append("synthetic policy violations detected")

    report["critical_violations"] = critical_violations
    report["validation_passed"] = len(critical_violations) == 0

    # Save summary JSON
    summary_path = report_dir / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Save unmapped coverages CSV
    if report["unmapped_coverages"]:
        unmapped_path = report_dir / "unmapped_coverages.csv"
        with open(unmapped_path, "w", encoding="utf-8") as f:
            f.write("coverage_name,occurrence_count\n")
            for item in report["unmapped_coverages"]:
                f.write(f'"{item["coverage_name"]}",{item["count"]}\n')

    # Print summary to console
    print("\n" + "=" * 60)
    print("Validation Report Summary")
    print("=" * 60)
    print(f"Timestamp: {timestamp}")
    print(f"\nDocuments: {len(report['document_stats'])} types")
    print(f"Chunks: {report['chunk_stats']['total_chunks']} total")
    print(f"  - Original: {report['chunk_stats']['original_chunks']}")
    print(f"  - Synthetic: {report['chunk_stats']['synthetic_chunks']}")
    print(f"\nMapping Success Rate: {report['alias_stats']['success_rate']}%")
    print(f"  - Mapped: {report['alias_stats']['mapped']}")
    print(f"  - Unmapped: {report['alias_stats']['unmapped']}")

    if critical_violations:
        print(f"\n⚠️  CRITICAL VIOLATIONS:")
        for violation in critical_violations:
            print(f"  - {violation}")
    else:
        print(f"\n✅ No critical violations")

    print(f"\nReport saved to: {report_dir}")
    print("=" * 60)

    return report_dir
