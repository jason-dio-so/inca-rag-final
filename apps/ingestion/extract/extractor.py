"""
Entity and amount extraction using LLM.

Strategy:
- Use GPT-4o for extraction
- Extract coverage names and amounts from chunks
- Store in chunk_entity and amount_entity tables
- Do NOT auto-generate coverage_standard entries (violation check)
- Coverage codes will be mapped in Normalize stage
"""
import json
import os
import re
from typing import List, Dict, Any, Optional

from psycopg2.extensions import connection as PGConnection

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


EXTRACTION_PROMPT = """다음 보험 약관 텍스트에서 담보명과 금액 정보를 추출하세요.

텍스트:
{text}

응답 형식 (JSON):
{{
  "coverages": [
    {{
      "coverage_name": "암진단금",
      "confidence": "high"
    }}
  ],
  "amounts": [
    {{
      "coverage_name": "암진단금",
      "context_type": "payment",
      "amount_value": 50000000,
      "amount_text": "5천만원",
      "amount_unit": "원",
      "confidence": "high"
    }}
  ]
}}

규칙:
- coverage_name: 정확한 담보명 (예: "암진단금", "뇌졸중진단금")
- context_type: "payment" (지급금), "count" (횟수), "limit" (한도)
- amount_value: 숫자로 변환된 금액 (천만원 -> 10000000)
- confidence: "high", "medium", "low"

JSON만 응답하세요."""


def get_openai_client():
    """Get OpenAI client."""
    if not OPENAI_AVAILABLE:
        raise ImportError("openai package required")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")

    return openai.OpenAI(api_key=api_key)


def extract_with_llm(client, text: str, model: str = "gpt-4o") -> Dict[str, Any]:
    """
    Extract entities using LLM.

    Args:
        client: OpenAI client
        text: Input text
        model: Model name

    Returns:
        Extracted data dict with coverages and amounts
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "당신은 보험 약관 분석 전문가입니다."},
                {"role": "user", "content": EXTRACTION_PROMPT.format(text=text)}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        return result

    except Exception as e:
        print(f"⚠️  LLM extraction failed: {e}")
        return {"coverages": [], "amounts": []}


def insert_chunk_entity(conn: PGConnection, chunk_id: int, entity_data: Dict) -> None:
    """
    Insert chunk_entity record.

    Args:
        conn: Database connection
        chunk_id: Chunk ID
        entity_data: Entity data dict

    Note:
        coverage_code is NULL here - will be filled in Normalize stage
    """
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO chunk_entity (chunk_id, entity_type, coverage_code, entity_value,
                                     extraction_method, confidence)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (
            chunk_id,
            "coverage",
            None,  # coverage_code NULL - to be filled in Normalize
            json.dumps(entity_data),
            "llm_gpt4o",
            entity_data.get("confidence", "medium")
        ))


def insert_amount_entity(conn: PGConnection, chunk_id: int, amount_data: Dict) -> None:
    """
    Insert amount_entity record.

    Args:
        conn: Database connection
        chunk_id: Chunk ID
        amount_data: Amount data dict

    Note:
        coverage_code is NULL here - will be filled in Normalize stage
    """
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO amount_entity (chunk_id, coverage_code, context_type,
                                      amount_value, amount_text, amount_unit, confidence)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (
            chunk_id,
            None,  # coverage_code NULL - to be filled in Normalize
            amount_data.get("context_type", "payment"),
            amount_data.get("amount_value"),
            amount_data.get("amount_text"),
            amount_data.get("amount_unit", "원"),
            amount_data.get("confidence", "medium")
        ))


def extract_entities_from_chunk(conn: PGConnection, chunk_id: int, content: str,
                                model: str = "gpt-4o") -> Dict[str, int]:
    """
    Extract entities from a single chunk.

    Args:
        conn: Database connection
        chunk_id: Chunk ID
        content: Chunk content
        model: LLM model name

    Returns:
        Statistics dict
    """
    try:
        client = get_openai_client()
    except (ImportError, ValueError) as e:
        print(f"⚠️  Extraction skipped: {e}")
        return {"entities_extracted": 0, "amounts_extracted": 0}

    # Extract using LLM
    extracted = extract_with_llm(client, content, model)

    stats = {"entities_extracted": 0, "amounts_extracted": 0}

    # Insert chunk_entity records
    for coverage in extracted.get("coverages", []):
        insert_chunk_entity(conn, chunk_id, coverage)
        stats["entities_extracted"] += 1

    # Insert amount_entity records
    for amount in extracted.get("amounts", []):
        insert_amount_entity(conn, chunk_id, amount)
        stats["amounts_extracted"] += 1

    return stats


def fetch_chunks_for_extraction(conn: PGConnection, limit: Optional[int] = None,
                                insurer_code: Optional[str] = None) -> List[Dict]:
    """
    Fetch chunks that need entity extraction.

    Args:
        conn: Database connection
        limit: Maximum chunks to fetch
        insurer_code: Optional insurer filter

    Returns:
        List of chunk dicts
    """
    query = """
        SELECT c.chunk_id, c.content
        FROM chunk c
        JOIN document d ON c.document_id = d.document_id
        JOIN product p ON d.product_id = p.product_id
        JOIN insurer i ON p.insurer_id = i.insurer_id
        WHERE c.chunk_id NOT IN (
            SELECT DISTINCT chunk_id FROM chunk_entity
        )
        AND c.is_synthetic = false
    """

    if insurer_code:
        query += " AND i.insurer_code = %s"

    query += " ORDER BY c.chunk_id"

    if limit:
        query += f" LIMIT {limit}"

    with conn.cursor() as cur:
        if insurer_code:
            cur.execute(query, (insurer_code,))
        else:
            cur.execute(query)

        return [{"chunk_id": row[0], "content": row[1]} for row in cur.fetchall()]


def extract_entities(conn: PGConnection, chunk_ids: List[int],
                    model: str = "gpt-4o") -> Dict[str, int]:
    """
    Extract entities from specific chunks.

    Args:
        conn: Database connection
        chunk_ids: List of chunk IDs
        model: LLM model name

    Returns:
        Statistics dict
    """
    if not chunk_ids:
        return {"chunks_processed": 0, "entities_extracted": 0, "amounts_extracted": 0}

    # Fetch chunks
    with conn.cursor() as cur:
        cur.execute("""
            SELECT chunk_id, content
            FROM chunk
            WHERE chunk_id = ANY(%s)
        """, (chunk_ids,))
        chunks = [{"chunk_id": row[0], "content": row[1]} for row in cur.fetchall()]

    stats = {"chunks_processed": 0, "entities_extracted": 0, "amounts_extracted": 0}

    for chunk in chunks:
        chunk_stats = extract_entities_from_chunk(
            conn, chunk["chunk_id"], chunk["content"], model
        )
        stats["chunks_processed"] += 1
        stats["entities_extracted"] += chunk_stats["entities_extracted"]
        stats["amounts_extracted"] += chunk_stats["amounts_extracted"]

    return stats


def extract_all_entities(conn: PGConnection, model: str = "gpt-4o",
                        insurer_code: Optional[str] = None,
                        limit: Optional[int] = None) -> Dict[str, int]:
    """
    Extract entities from all chunks without entities.

    Args:
        conn: Database connection
        model: LLM model name
        insurer_code: Optional insurer filter
        limit: Maximum chunks to process

    Returns:
        Statistics dict
    """
    chunks = fetch_chunks_for_extraction(conn, limit, insurer_code)

    if not chunks:
        return {"chunks_processed": 0, "entities_extracted": 0, "amounts_extracted": 0}

    chunk_ids = [c["chunk_id"] for c in chunks]
    return extract_entities(conn, chunk_ids, model)
