"""
Ingestion pipeline for inca-RAG-final.

STEP 3-Validate scope:
- Discover: File scanning + hash calculation
- Register: DB upsert (insurer/product/document only)

NOT included in this validation:
- PDF parsing
- Chunk/Embed/Extract/Normalize/Synthetic
"""

__version__ = "0.1.0"
