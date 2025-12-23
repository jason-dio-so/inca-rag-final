"""
Chunk stage: Text → chunks (is_synthetic=false only).
"""

from .chunker import chunk_document, chunk_all_documents

__all__ = ["chunk_document", "chunk_all_documents"]
