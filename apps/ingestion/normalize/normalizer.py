"""
Coverage normalization to coverage_standard.

Critical principle:
- ❌ NEVER auto-INSERT into coverage_standard
- ✅ Map via coverage_alias table
- ✅ Generate UNMAPPED report for unknown coverages
- ✅ Use FK enforcement to prevent invalid references
"""
import json
from typing import List, Dict, Set, Optional

from psycopg2.extensions import connection as PGConnection


def fetch_coverage_standard_map(conn: PGConnection) -> Dict[str, int]:
    """
    Fetch coverage_standard mapping (coverage_code -> coverage_id).

    Args:
        conn: Database connection

    Returns:
        Dict mapping coverage_code to coverage_id
    """
    with conn.cursor() as cur:
        cur.execute("""
            SELECT coverage_code, coverage_id
            FROM coverage_standard
        """)
        return {row[0]: row[1] for row in cur.fetchall()}


def fetch_existing_aliases(conn: PGConnection, insurer_id: int) -> Dict[str, int]:
    """
    Fetch existing coverage_alias mappings for an insurer.

    Args:
        conn: Database connection
        insurer_id: Insurer ID

    Returns:
        Dict mapping insurer_coverage_name to coverage_id
    """
    with conn.cursor() as cur:
        cur.execute("""
            SELECT insurer_coverage_name, coverage_id
            FROM coverage_alias
            WHERE insurer_id = %s
        """, (insurer_id,))
        return {row[0]: row[1] for row in cur.fetchall()}


def simple_coverage_matcher(coverage_name: str, standard_codes: Dict[str, int]) -> Optional[str]:
    """
    Simple rule-based coverage matcher.

    Args:
        coverage_name: Input coverage name (e.g., "암진단금")
        standard_codes: Dict of coverage_code -> coverage_id

    Returns:
        Matched coverage_code or None

    Note:
        This is a simple heuristic matcher. In production, use LLM or manual mapping.
    """
    # Normalize
    name_normalized = coverage_name.strip().lower()

    # Direct match attempts
    for code in standard_codes.keys():
        code_parts = code.lower().split("_")

        # Simple keyword matching
        if "암" in name_normalized and "ca_diag" in code.lower():
            if "일반암" in name_normalized and "general" in code.lower():
                return code
            elif "제자리암" in name_normalized and "carcinoma_in_situ" in code.lower():
                return code
            elif "유사암" in name_normalized and "quasi" in code.lower():
                return code

        if "뇌졸중" in name_normalized and "stroke" in code.lower():
            return code

        if "심근경색" in name_normalized and "mi_" in code.lower():
            return code

    return None


def create_or_update_alias(conn: PGConnection, insurer_id: int,
                           coverage_name: str, coverage_id: int,
                           confidence: str = "high") -> None:
    """
    Create or update coverage_alias.

    Args:
        conn: Database connection
        insurer_id: Insurer ID
        coverage_name: Insurer's coverage name
        coverage_id: coverage_standard.coverage_id (FK enforced!)
        confidence: Confidence level

    Raises:
        psycopg2.IntegrityError: If coverage_id doesn't exist in coverage_standard
    """
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO coverage_alias (insurer_id, coverage_id, insurer_coverage_name,
                                       confidence, mapping_method)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (insurer_id, insurer_coverage_name)
            DO UPDATE SET
                coverage_id = EXCLUDED.coverage_id,
                confidence = EXCLUDED.confidence,
                mapping_method = EXCLUDED.mapping_method
        """, (insurer_id, coverage_id, coverage_name, confidence, "auto_heuristic_v1"))


def update_chunk_entity_coverage_code(conn: PGConnection, entity_id: int,
                                     coverage_code: str) -> None:
    """
    Update chunk_entity with coverage_code.

    Args:
        conn: Database connection
        entity_id: chunk_entity.entity_id
        coverage_code: coverage_standard.coverage_code (FK enforced!)
    """
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE chunk_entity
            SET coverage_code = %s
            WHERE entity_id = %s
        """, (coverage_code, entity_id))


def update_amount_entity_coverage_code(conn: PGConnection, amount_id: int,
                                      coverage_code: str) -> None:
    """
    Update amount_entity with coverage_code.

    Args:
        conn: Database connection
        amount_id: amount_entity.amount_id
        coverage_code: coverage_standard.coverage_code (FK enforced!)
    """
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE amount_entity
            SET coverage_code = %s
            WHERE amount_id = %s
        """, (coverage_code, amount_id))


def normalize_coverage_aliases(conn: PGConnection, insurer_id: int) -> Dict[str, Any]:
    """
    Normalize coverage names for a specific insurer.

    Process:
    1. Fetch coverage_standard mapping
    2. Fetch existing aliases for insurer
    3. Fetch unmapped chunk_entity/amount_entity records
    4. Attempt to match using heuristics
    5. Create coverage_alias for successful matches
    6. Update chunk_entity/amount_entity with coverage_code
    7. Generate UNMAPPED report for failures

    Args:
        conn: Database connection
        insurer_id: Insurer ID

    Returns:
        Statistics dict with matched/unmapped counts
    """
    stats = {
        "total_entities": 0,
        "matched": 0,
        "unmapped": 0,
        "unmapped_names": []
    }

    # Fetch coverage_standard
    standard_map = fetch_coverage_standard_map(conn)

    if not standard_map:
        print("⚠️  No coverage_standard records found. Cannot normalize.")
        print("⚠️  This is expected if coverage_standard hasn't been seeded yet.")
        return stats

    # Fetch existing aliases
    aliases = fetch_existing_aliases(conn, insurer_id)

    # Fetch unmapped chunk_entity records
    with conn.cursor() as cur:
        cur.execute("""
            SELECT ce.entity_id, ce.entity_value
            FROM chunk_entity ce
            JOIN chunk c ON ce.chunk_id = c.chunk_id
            JOIN document d ON c.document_id = d.document_id
            JOIN product p ON d.product_id = p.product_id
            WHERE p.insurer_id = %s
              AND ce.coverage_code IS NULL
        """, (insurer_id,))

        entities = cur.fetchall()

    stats["total_entities"] = len(entities)

    for entity_id, entity_value_json in entities:
        try:
            entity_value = json.loads(entity_value_json) if isinstance(entity_value_json, str) else entity_value_json
            coverage_name = entity_value.get("coverage_name", "")

            if not coverage_name:
                continue

            # Check if alias already exists
            if coverage_name in aliases:
                coverage_id = aliases[coverage_name]
                # Get coverage_code from coverage_id
                coverage_code = next((code for code, cid in standard_map.items() if cid == coverage_id), None)

                if coverage_code:
                    update_chunk_entity_coverage_code(conn, entity_id, coverage_code)
                    stats["matched"] += 1
                    continue

            # Attempt to match
            matched_code = simple_coverage_matcher(coverage_name, standard_map)

            if matched_code:
                coverage_id = standard_map[matched_code]

                # Create alias
                create_or_update_alias(conn, insurer_id, coverage_name, coverage_id, "medium")

                # Update entity
                update_chunk_entity_coverage_code(conn, entity_id, matched_code)

                stats["matched"] += 1
                aliases[coverage_name] = coverage_id  # Cache
            else:
                stats["unmapped"] += 1
                if coverage_name not in stats["unmapped_names"]:
                    stats["unmapped_names"].append(coverage_name)

        except Exception as e:
            print(f"⚠️  Failed to normalize entity {entity_id}: {e}")
            stats["unmapped"] += 1

    return stats


def normalize_all_coverages(conn: PGConnection) -> Dict[str, Any]:
    """
    Normalize coverages for all insurers.

    Args:
        conn: Database connection

    Returns:
        Aggregated statistics
    """
    # Fetch all insurers
    with conn.cursor() as cur:
        cur.execute("SELECT insurer_id, insurer_code FROM insurer")
        insurers = cur.fetchall()

    aggregated_stats = {
        "insurers_processed": 0,
        "total_matched": 0,
        "total_unmapped": 0,
        "unmapped_by_insurer": {}
    }

    for insurer_id, insurer_code in insurers:
        print(f"Normalizing coverages for {insurer_code}...")

        stats = normalize_coverage_aliases(conn, insurer_id)

        aggregated_stats["insurers_processed"] += 1
        aggregated_stats["total_matched"] += stats["matched"]
        aggregated_stats["total_unmapped"] += stats["unmapped"]

        if stats["unmapped_names"]:
            aggregated_stats["unmapped_by_insurer"][insurer_code] = stats["unmapped_names"]

    return aggregated_stats
