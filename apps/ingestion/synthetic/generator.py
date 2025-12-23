"""
Synthetic chunk generation for Amount Bridge.

Critical principles:
- ✅ Only for chunks with 2+ coverages
- ✅ is_synthetic=true, synthetic_source_chunk_id=<original>
- ✅ meta.synthetic_type="split", meta.synthetic_method="v1_6_3_beta_2_split"
- ❌ Never use in Compare/Retrieval axis
- ✅ Only for Amount Bridge (amount evidence)
"""
import json
import os
from typing import List, Dict, Optional

from psycopg2.extensions import connection as PGConnection

try:
    import openai
    OPENAI_AVAILABLE = True
except Import

Error:
    OPENAI_AVAILABLE = False


SPLIT_PROMPT = """다음 보험 약관 텍스트에는 여러 담보가 혼합되어 있습니다.
각 담보별로 텍스트를 분리하세요.

원본 텍스트:
{text}

감지된 담보:
{coverages}

응답 형식 (JSON):
{{
  "split_chunks": [
    {{
      "coverage_code": "CA_DIAG_GENERAL",
      "content": "일반암 진단 시 5천만원을 지급합니다.",
      "amount_value": 50000000,
      "amount_text": "5천만원"
    }}
  ]
}}

규칙:
- 각 담보별로 content 분리
- amount 정보 포함
- JSON만 응답"""


def get_openai_client():
    """Get OpenAI client."""
    if not OPENAI_AVAILABLE:
        raise ImportError("openai package required")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")

    return openai.OpenAI(api_key=api_key)


def split_chunk_with_llm(client, text: str, coverages: List[str],
                        model: str = "gpt-4o") -> List[Dict]:
    """
    Split mixed chunk using LLM.

    Args:
        client: OpenAI client
        text: Original chunk text
        coverages: List of coverage codes detected
        model: Model name

    Returns:
        List of split chunk dicts
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "보험 약관 텍스트 분리 전문가"},
                {"role": "user", "content": SPLIT_PROMPT.format(
                    text=text,
                    coverages=", ".join(coverages)
                )}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        return result.get("split_chunks", [])

    except Exception as e:
        print(f"⚠️  Chunk splitting failed: {e}")
        return []


def find_mixed_coverage_chunks(conn: PGConnection, limit: Optional[int] = None) -> List[Dict]:
    """
    Find chunks with 2+ distinct coverage codes (candidates for splitting).

    Args:
        conn: Database connection
        limit: Maximum chunks to return

    Returns:
        List of chunk dicts with chunk_id, content, and coverage_codes
    """
    query = """
        SELECT c.chunk_id, c.content, ARRAY_AGG(DISTINCT ce.coverage_code) as coverage_codes
        FROM chunk c
        JOIN chunk_entity ce ON c.chunk_id = ce.chunk_id
        WHERE c.is_synthetic = false
          AND ce.coverage_code IS NOT NULL
        GROUP BY c.chunk_id, c.content
        HAVING COUNT(DISTINCT ce.coverage_code) >= 2
        ORDER BY c.chunk_id
    """

    if limit:
        query += f" LIMIT {limit}"

    with conn.cursor() as cur:
        cur.execute(query)
        return [
            {"chunk_id": row[0], "content": row[1], "coverage_codes": row[2]}
            for row in cur.fetchall()
        ]


def insert_synthetic_chunk(conn: PGConnection, source_chunk_id: int,
                          document_id: int, page_number: int,
                          content: str, coverage_code: str,
                          amount_value: Optional[float] = None,
                          amount_text: Optional[str] = None) -> int:
    """
    Insert synthetic chunk.

    Args:
        conn: Database connection
        source_chunk_id: Original chunk ID
        document_id: Document ID
        page_number: Page number
        content: Split content
        coverage_code: Coverage code for this split
        amount_value: Optional amount value
        amount_text: Optional amount text

    Returns:
        Synthetic chunk_id
    """
    meta = {
        "synthetic_type": "split",
        "synthetic_method": "v1_6_3_beta_2_split",
        "entities": {
            "coverage_code": coverage_code
        }
    }

    if amount_value is not None:
        meta["entities"]["amount"] = {
            "amount_value": amount_value,
            "amount_text": amount_text,
            "method": "v1_6_3_beta_2_split",
            "confidence": "high"
        }

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO chunk (document_id, page_number, content, is_synthetic,
                             synthetic_source_chunk_id, meta)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING chunk_id
        """, (document_id, page_number, content, True, source_chunk_id, json.dumps(meta)))

        return cur.fetchone()[0]


def generate_synthetic_chunks_for_chunk(conn: PGConnection, chunk_id: int,
                                       content: str, coverage_codes: List[str],
                                       model: str = "gpt-4o") -> int:
    """
    Generate synthetic chunks for a single mixed chunk.

    Args:
        conn: Database connection
        chunk_id: Source chunk ID
        content: Chunk content
        coverage_codes: List of coverage codes detected
        model: LLM model

    Returns:
        Number of synthetic chunks created
    """
    # Get document_id and page_number
    with conn.cursor() as cur:
        cur.execute("""
            SELECT document_id, page_number
            FROM chunk
            WHERE chunk_id = %s
        """, (chunk_id,))

        row = cur.fetchone()
        if not row:
            raise ValueError(f"Chunk {chunk_id} not found")

        document_id, page_number = row

    # Split using LLM
    try:
        client = get_openai_client()
    except (ImportError, ValueError) as e:
        print(f"⚠️  Synthetic generation skipped: {e}")
        return 0

    split_chunks = split_chunk_with_llm(client, content, coverage_codes, model)

    count = 0
    for split in split_chunks:
        insert_synthetic_chunk(
            conn,
            source_chunk_id=chunk_id,
            document_id=document_id,
            page_number=page_number,
            content=split.get("content", ""),
            coverage_code=split.get("coverage_code"),
            amount_value=split.get("amount_value"),
            amount_text=split.get("amount_text")
        )
        count += 1

    return count


def generate_synthetic_chunks(conn: PGConnection, chunk_ids: List[int],
                             model: str = "gpt-4o") -> Dict[str, int]:
    """
    Generate synthetic chunks for specific source chunks.

    Args:
        conn: Database connection
        chunk_ids: List of source chunk IDs
        model: LLM model

    Returns:
        Statistics dict
    """
    stats = {"chunks_processed": 0, "synthetic_created": 0}

    for chunk_id in chunk_ids:
        # Fetch chunk and coverage codes
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.content, ARRAY_AGG(DISTINCT ce.coverage_code) as coverage_codes
                FROM chunk c
                JOIN chunk_entity ce ON c.chunk_id = ce.chunk_id
                WHERE c.chunk_id = %s
                  AND ce.coverage_code IS NOT NULL
                GROUP BY c.content
            """, (chunk_id,))

            row = cur.fetchone()
            if not row:
                continue

            content, coverage_codes = row

        # Only generate if 2+ coverages
        if len(coverage_codes) < 2:
            continue

        try:
            count = generate_synthetic_chunks_for_chunk(
                conn, chunk_id, content, coverage_codes, model
            )
            stats["chunks_processed"] += 1
            stats["synthetic_created"] += count
        except Exception as e:
            print(f"⚠️  Failed to generate synthetic chunks for {chunk_id}: {e}")

    return stats


def generate_all_synthetic_chunks(conn: PGConnection, model: str = "gpt-4o",
                                 limit: Optional[int] = None) -> Dict[str, int]:
    """
    Generate synthetic chunks for all mixed coverage chunks.

    Args:
        conn: Database connection
        model: LLM model
        limit: Maximum chunks to process

    Returns:
        Statistics dict
    """
    # Find mixed chunks
    mixed_chunks = find_mixed_coverage_chunks(conn, limit)

    if not mixed_chunks:
        return {"chunks_processed": 0, "synthetic_created": 0}

    chunk_ids = [c["chunk_id"] for c in mixed_chunks]
    return generate_synthetic_chunks(conn, chunk_ids, model)
