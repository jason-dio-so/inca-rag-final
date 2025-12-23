"""
Parse stage: PDF → text extraction.
"""

from .parser import parse_document, parse_all_documents

__all__ = ["parse_document", "parse_all_documents"]
