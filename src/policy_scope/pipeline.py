"""
Policy Scope Pipeline v1 (MVP)

Purpose: Process policy documents to populate disease_scope_norm

Flow:
1. Parse policy document (deterministic regex)
2. Create/update disease_code_group (with evidence)
3. Create disease_code_group_member (validate against KCD-7 master)
4. Create coverage_disease_scope (with evidence)
5. Update proposal_coverage_slots.disease_scope_norm (group references)

Constitutional guarantees:
- Evidence required at every step
- KCD-7 codes validated against disease_code_master
- insurer=NULL restricted to medical/KCD classification only
- Insurance concepts (유사암) must be insurer-specific groups
"""
from typing import Dict, List, Optional
from psycopg2.extensions import connection as PGConnection


class PolicyScopePipeline:
    """
    MVP: Process policy documents to populate disease_scope_norm
    """

    def __init__(self, conn: PGConnection):
        """
        Args:
            conn: Database connection (write-enabled for pipeline)
        """
        self.conn = conn

    def create_disease_code_group(
        self,
        group_id: str,
        group_label: str,
        insurer: str,
        version_tag: str,
        basis_doc_id: str,
        basis_page: int,
        basis_span: str
    ) -> None:
        """
        Create disease_code_group with evidence.

        Constitutional requirement:
        - insurer MUST be provided for insurance concepts (유사암, 소액암, etc.)
        - insurer=NULL only for medical/KCD classification (C00-C97 ranges)
        - Evidence required (basis_doc_id, basis_page, basis_span)

        Args:
            group_id: Unique group ID (e.g., 'SIMILAR_CANCER_SAMSUNG_V1')
            group_label: Human-readable label (e.g., '유사암 (삼성)')
            insurer: Insurer code (e.g., 'SAMSUNG') - required for insurance concepts
            version_tag: Version tag (e.g., 'V1')
            basis_doc_id: Policy document ID (evidence)
            basis_page: Page number (evidence)
            basis_span: Text span (evidence)

        Raises:
            ValueError: If insurer is NULL for insurance concept
            psycopg2.IntegrityError: If group_id already exists
        """
        if not insurer and '유사암' in group_label or '소액암' in group_label:
            raise ValueError(
                f"insurer=NULL not allowed for insurance concept: {group_label}. "
                "Constitutional violation: insurer=NULL restricted to medical/KCD classification."
            )

        if not basis_span:
            raise ValueError("Evidence required: basis_span cannot be empty")

        sql = """
        INSERT INTO disease_code_group (
            group_id, group_label, insurer, version_tag,
            basis_doc_id, basis_page, basis_span
        ) VALUES (
            %(group_id)s, %(group_label)s, %(insurer)s, %(version_tag)s,
            %(basis_doc_id)s, %(basis_page)s, %(basis_span)s
        )
        ON CONFLICT (group_id) DO NOTHING
        """

        with self.conn.cursor() as cursor:
            cursor.execute(sql, {
                'group_id': group_id,
                'group_label': group_label,
                'insurer': insurer,
                'version_tag': version_tag,
                'basis_doc_id': basis_doc_id,
                'basis_page': basis_page,
                'basis_span': basis_span
            })

        self.conn.commit()

    def add_disease_code_group_member(
        self,
        group_id: str,
        code: Optional[str] = None,
        code_from: Optional[str] = None,
        code_to: Optional[str] = None
    ) -> None:
        """
        Add member to disease_code_group.

        Constitutional requirement:
        - KCD-7 codes must exist in disease_code_master (FK validation)
        - Either single code OR range (code_from, code_to), not both

        Args:
            group_id: Group ID to add member to
            code: Single KCD-7 code (e.g., 'C73')
            code_from: Range start code (e.g., 'C00')
            code_to: Range end code (e.g., 'C97')

        Raises:
            psycopg2.IntegrityError: If FK validation fails (code not in disease_code_master)
        """
        if code:
            member_type = 'CODE'
            sql = """
            INSERT INTO disease_code_group_member (
                group_id, member_type, code
            ) VALUES (
                %(group_id)s, %(member_type)s::member_type_enum, %(code)s
            )
            """
            params = {'group_id': group_id, 'member_type': member_type, 'code': code}
        elif code_from and code_to:
            member_type = 'RANGE'
            sql = """
            INSERT INTO disease_code_group_member (
                group_id, member_type, code_from, code_to
            ) VALUES (
                %(group_id)s, %(member_type)s::member_type_enum, %(code_from)s, %(code_to)s
            )
            """
            params = {
                'group_id': group_id,
                'member_type': member_type,
                'code_from': code_from,
                'code_to': code_to
            }
        else:
            raise ValueError("Must provide either code OR (code_from, code_to)")

        with self.conn.cursor() as cursor:
            cursor.execute(sql, params)

        self.conn.commit()

    def create_coverage_disease_scope(
        self,
        canonical_coverage_code: str,
        insurer: str,
        proposal_id: str,
        include_group_id: str,
        exclude_group_id: Optional[str],
        source_doc_id: str,
        source_page: int,
        span_text: str,
        extraction_rule_id: str
    ) -> int:
        """
        Create coverage_disease_scope with evidence.

        Constitutional requirement:
        - Evidence required (source_doc_id, source_page, span_text)
        - include_group_id required (cannot be NULL)
        - exclude_group_id optional

        Args:
            canonical_coverage_code: Canonical coverage code
            insurer: Insurer code
            proposal_id: Proposal ID
            include_group_id: Group ID to include (required)
            exclude_group_id: Group ID to exclude (optional)
            source_doc_id: Policy document ID (evidence)
            source_page: Page number (evidence)
            span_text: Text span (evidence)
            extraction_rule_id: Extraction rule ID for reproducibility

        Returns:
            scope_id: Created scope ID

        Raises:
            ValueError: If evidence is missing
        """
        if not span_text:
            raise ValueError("Evidence required: span_text cannot be empty")

        sql = """
        INSERT INTO coverage_disease_scope (
            canonical_coverage_code, insurer, proposal_id,
            include_group_id, exclude_group_id,
            source_doc_id, source_page, span_text, extraction_rule_id
        ) VALUES (
            %(canonical_coverage_code)s, %(insurer)s, %(proposal_id)s,
            %(include_group_id)s, %(exclude_group_id)s,
            %(source_doc_id)s, %(source_page)s, %(span_text)s, %(extraction_rule_id)s
        )
        RETURNING id
        """

        with self.conn.cursor() as cursor:
            cursor.execute(sql, {
                'canonical_coverage_code': canonical_coverage_code,
                'insurer': insurer,
                'proposal_id': proposal_id,
                'include_group_id': include_group_id,
                'exclude_group_id': exclude_group_id,
                'source_doc_id': source_doc_id,
                'source_page': source_page,
                'span_text': span_text,
                'extraction_rule_id': extraction_rule_id
            })
            scope_id = cursor.fetchone()[0]

        self.conn.commit()
        return scope_id

    def update_proposal_slots_disease_scope_norm(
        self,
        mapped_id: int,
        include_group_id: str,
        exclude_group_id: Optional[str]
    ) -> None:
        """
        Update proposal_coverage_slots.disease_scope_norm with group references.

        Constitutional requirement:
        - disease_scope_norm must be group references (JSONB)
        - Format: {"include_group_id": "...", "exclude_group_id": "..."}
        - NOT raw code arrays

        Args:
            mapped_id: proposal_coverage_mapped.id
            include_group_id: Group ID to include
            exclude_group_id: Group ID to exclude (optional)
        """
        disease_scope_norm = {
            "include_group_id": include_group_id
        }
        if exclude_group_id:
            disease_scope_norm["exclude_group_id"] = exclude_group_id

        sql = """
        UPDATE proposal_coverage_slots
        SET disease_scope_norm = %(disease_scope_norm)s::jsonb
        WHERE mapped_id = %(mapped_id)s
        """

        with self.conn.cursor() as cursor:
            cursor.execute(sql, {
                'mapped_id': mapped_id,
                'disease_scope_norm': disease_scope_norm
            })

        self.conn.commit()
