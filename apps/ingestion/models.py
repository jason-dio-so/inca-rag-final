"""
Data models for ingestion pipeline.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ManifestRow:
    """Represents a single row in docs_manifest.csv"""
    insurer_code: str
    product_code: str
    product_name: str
    document_type: str
    file_path: str
    file_hash: Optional[str] = None  # Calculated during discover

    def __post_init__(self):
        """Validate required fields"""
        if not self.insurer_code:
            raise ValueError("insurer_code is required")
        if not self.product_code:
            raise ValueError("product_code is required")
        if not self.product_name:
            raise ValueError("product_name is required")
        if not self.document_type:
            raise ValueError("document_type is required")
        if not self.file_path:
            raise ValueError("file_path is required")


@dataclass
class InsurerRecord:
    """Database record for insurer table"""
    insurer_code: str
    insurer_name: str
    is_active: bool = True


@dataclass
class ProductRecord:
    """Database record for product table"""
    insurer_id: int
    product_code: str
    product_name: str
    product_type: str
    is_active: bool = True


@dataclass
class DocumentRecord:
    """Database record for document table"""
    product_id: int
    document_type: str
    file_path: str
    file_hash: str
    doc_type_priority: int
