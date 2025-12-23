"""
Embedding generation.

Strategy:
- Use OpenAI text-embedding-3-small (1536 dimensions)
- Batch processing for efficiency
- Skip chunks that already have embeddings (idempotent)
- Fail gracefully: chunk persists even if embedding fails
"""
import os
from typing import List, Optional, Dict

from psycopg2.extensions import connection as PGConnection

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def get_openai_client():
    """
    Get OpenAI client.

    Returns:
        OpenAI client instance

    Raises:
        ImportError: If openai package not installed
        ValueError: If OPENAI_API_KEY not set
    """
    if not OPENAI_AVAILABLE:
        raise ImportError("openai package required. Install with: pip install openai")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    return openai.OpenAI(api_key=api_key)


def generate_embedding(client, text: str, model: str = "text-embedding-3-small") -> List[float]:
    """
    Generate embedding for text.

    Args:
        client: OpenAI client
        text: Input text
        model: Embedding model name

    Returns:
        Embedding vector (1536 dimensions for text-embedding-3-small)
    """
    response = client.embeddings.create(
        input=text,
        model=model
    )
    return response.data[0].embedding


def generate_embeddings_batch(client, texts: List[str],
                              model: str = "text-embedding-3-small") -> List[List[float]]:
    """
    Generate embeddings for multiple texts in a single API call.

    Args:
        client: OpenAI client
        texts: List of input texts
        model: Embedding model name

    Returns:
        List of embedding vectors
    """
    if not texts:
        return []

    response = client.embeddings.create(
        input=texts,
        model=model
    )

    # Sort by index to ensure correct order
    embeddings = [None] * len(texts)
    for item in response.data:
        embeddings[item.index] = item.embedding

    return embeddings


def fetch_chunks_without_embeddings(conn: PGConnection, limit: Optional[int] = None,
                                   insurer_code: Optional[str] = None) -> List[Dict]:
    """
    Fetch chunks that don't have embeddings yet.

    Args:
        conn: Database connection
        limit: Maximum number of chunks to fetch
        insurer_code: Optional filter by insurer

    Returns:
        List of dicts with chunk_id and content
    """
    query = """
        SELECT c.chunk_id, c.content
        FROM chunk c
        JOIN document d ON c.document_id = d.document_id
        JOIN product p ON d.product_id = p.product_id
        JOIN insurer i ON p.insurer_id = i.insurer_id
        WHERE c.embedding IS NULL
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


def update_chunk_embedding(conn: PGConnection, chunk_id: int, embedding: List[float]) -> None:
    """
    Update chunk with embedding vector.

    Args:
        conn: Database connection
        chunk_id: Chunk ID
        embedding: Embedding vector
    """
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE chunk
            SET embedding = %s::vector
            WHERE chunk_id = %s
        """, (str(embedding), chunk_id))


def embed_chunks(conn: PGConnection, chunk_ids: List[int], model: str = "text-embedding-3-small",
                batch_size: int = 100) -> Dict[str, int]:
    """
    Generate embeddings for specific chunks.

    Args:
        conn: Database connection
        chunk_ids: List of chunk IDs
        model: Embedding model name
        batch_size: Batch size for API calls

    Returns:
        Statistics dictionary
    """
    if not chunk_ids:
        return {"processed": 0, "success": 0, "failed": 0}

    # Fetch chunk content
    with conn.cursor() as cur:
        cur.execute("""
            SELECT chunk_id, content
            FROM chunk
            WHERE chunk_id = ANY(%s)
        """, (chunk_ids,))
        chunks = [{"chunk_id": row[0], "content": row[1]} for row in cur.fetchall()]

    # Get OpenAI client
    try:
        client = get_openai_client()
    except (ImportError, ValueError) as e:
        print(f"⚠️  Embedding skipped: {e}")
        return {"processed": 0, "success": 0, "failed": len(chunks)}

    stats = {"processed": 0, "success": 0, "failed": 0}

    # Process in batches
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]

        try:
            # Generate embeddings
            texts = [chunk["content"] for chunk in batch]
            embeddings = generate_embeddings_batch(client, texts, model)

            # Update database
            for chunk, embedding in zip(batch, embeddings):
                try:
                    update_chunk_embedding(conn, chunk["chunk_id"], embedding)
                    stats["success"] += 1
                except Exception as e:
                    print(f"⚠️  Failed to update embedding for chunk {chunk['chunk_id']}: {e}")
                    stats["failed"] += 1

                stats["processed"] += 1

        except Exception as e:
            print(f"⚠️  Batch embedding failed: {e}")
            stats["failed"] += len(batch)
            stats["processed"] += len(batch)

    return stats


def embed_all_chunks(conn: PGConnection, model: str = "text-embedding-3-small",
                    batch_size: int = 100, insurer_code: Optional[str] = None,
                    limit: Optional[int] = None) -> Dict[str, int]:
    """
    Generate embeddings for all chunks without embeddings.

    Args:
        conn: Database connection
        model: Embedding model name
        batch_size: Batch size for API calls
        insurer_code: Optional filter by insurer
        limit: Maximum number of chunks to process

    Returns:
        Statistics dictionary
    """
    # Fetch chunks without embeddings
    chunks = fetch_chunks_without_embeddings(conn, limit, insurer_code)

    if not chunks:
        return {"processed": 0, "success": 0, "failed": 0}

    # Extract chunk IDs
    chunk_ids = [chunk["chunk_id"] for chunk in chunks]

    # Generate embeddings
    return embed_chunks(conn, chunk_ids, model, batch_size)
