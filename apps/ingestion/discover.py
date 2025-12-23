"""
Discover stage: File scanning + hash calculation.
"""
import csv
import hashlib
from pathlib import Path
from typing import List

from .models import ManifestRow


def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA-256 hash of a file.

    Args:
        file_path: Path to the file

    Returns:
        Hex-encoded SHA-256 hash
    """
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()


def load_manifest(manifest_path: Path) -> List[ManifestRow]:
    """
    Load and validate manifest CSV file.

    Args:
        manifest_path: Path to docs_manifest.csv

    Returns:
        List of ManifestRow objects

    Raises:
        FileNotFoundError: If manifest file doesn't exist
        ValueError: If required columns are missing
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    rows = []
    with open(manifest_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Validate required columns
        required_cols = {"insurer_code", "product_code", "product_name",
                        "document_type", "file_path"}
        if not required_cols.issubset(set(reader.fieldnames or [])):
            raise ValueError(f"Missing required columns: {required_cols - set(reader.fieldnames or [])}")

        for row in reader:
            manifest_row = ManifestRow(
                insurer_code=row["insurer_code"],
                product_code=row["product_code"],
                product_name=row["product_name"],
                document_type=row["document_type"],
                file_path=row["file_path"],
                file_hash=row.get("file_hash")  # May be empty
            )
            rows.append(manifest_row)

    return rows


def discover(manifest_path: Path, base_path: Path) -> List[ManifestRow]:
    """
    Discover stage: Load manifest, verify files exist, calculate hashes.

    Args:
        manifest_path: Path to docs_manifest.csv
        base_path: Base directory for resolving relative file paths

    Returns:
        List of ManifestRow objects with file_hash populated

    Raises:
        FileNotFoundError: If any file in manifest doesn't exist
    """
    rows = load_manifest(manifest_path)

    for row in rows:
        # Resolve file path
        file_path = Path(row.file_path)
        if not file_path.is_absolute():
            file_path = base_path / file_path

        # Check file exists
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Calculate hash if not already present
        if not row.file_hash:
            row.file_hash = calculate_file_hash(file_path)

    return rows
