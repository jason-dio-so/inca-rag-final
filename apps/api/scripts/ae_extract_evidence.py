#!/usr/bin/env python3
"""
STEP NEXT-AE-FIX: Coverage Evidence Extraction (Document-Based, Deterministic)

Constitutional Principles (STEP NEXT-AE-FIX):
- PDF = Layout Document (not text)
- Structure-First: 목차/헤더/섹션 파악 → Evidence 추출
- Deterministic only (no LLM inference)
- Evidence = excerpt + page + source_doc_type
- **Evidence 출처 제한**: 약관 / 사업방법서 / 상품요약서만 허용
- **가입설계서는 Evidence 출처가 될 수 없음** (Comparison Layer 전용)

Evidence Definition (Constitutional):
1. ✅ PDF 문서 기반
2. ✅ Deterministic 추출 (Structure / Rule 기반)
3. ✅ 출처: policy / business_rules / product_summary
4. ✅ 메타데이터 필수: source_doc_type, source_page, excerpt

Extraction Process:
1. Load MAPPED coverages from v2.coverage_mapping
2. Locate policy/business_rules/product_summary PDFs for product
3. Find sections: 정의, 지급사유, 면책(또는 감액)
4. Extract excerpts + page references
5. Store to v2.coverage_evidence

Evidence Types:
- definition: Coverage 정의 (예: "일반암이라 함은...")
- payment_condition: 보험금 지급 조건 (예: "피보험자가 보험기간 중...")
- exclusion: 면책 사항 (예: "다음의 경우에는 보험금을 지급하지 않습니다...")
- partial_payment: 감액 규칙 (선택적)

Allowed source_doc_type (Hard Rule):
- 'policy' (약관)
- 'business_rules' (사업방법서)
- 'product_summary' (상품요약서)

금지 사항:
- ❌ 가입설계서를 Evidence 출처로 사용
- ❌ LLM 기반 추론/매핑
- ❌ Vector/Embedding 기반 검색
- ❌ 임의 sample evidence INSERT
- ❌ coverage_code 추론
- ❌ page / source_doc_type 없는 Evidence
"""

import hashlib
import json
import logging
import re
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import pdfplumber
import psycopg2
from psycopg2.extensions import connection as PGConnection

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.db import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PolicyEvidenceExtractor:
    """
    Structure-First Policy Evidence Extractor

    Principles:
    1. PDF = Layout Document
    2. Section/Header structure first
    3. Evidence = excerpt + page reference
    4. Deterministic only
    """

    def __init__(self, pdf_path: Path, doc_type: str = "policy"):
        self.pdf_path = pdf_path
        self.doc_type = doc_type  # policy, business_rules
        self.pdf = pdfplumber.open(str(pdf_path))
        logger.info(f"Opened {doc_type} PDF: {pdf_path.name}, pages={len(self.pdf.pages)}")

    def close(self):
        """Close PDF"""
        if self.pdf:
            self.pdf.close()

    def extract_evidence_for_coverage(
        self,
        canonical_coverage_code: str,
        coverage_keywords: List[str]
    ) -> List[Dict]:
        """
        Extract evidence for a single canonical coverage code.

        Args:
            canonical_coverage_code: 신정원 통일 코드 (e.g., CA_DIAG_GENERAL)
            coverage_keywords: 담보명 키워드 목록 (e.g., ["일반암", "암진단"])

        Returns:
            List of {
                evidence_type: str,
                excerpt: str,
                source_page: int,
                extraction_method: str,
                extraction_confidence: str
            }
        """
        evidences = []

        # Strategy: 키워드 기반 섹션 탐지 (Structure-First)
        # 1. "정의" 섹션 찾기 → definition evidence
        # 2. "보험금 지급" 섹션 찾기 → payment_condition evidence
        # 3. "면책" 또는 "지급하지 않는 경우" 섹션 찾기 → exclusion evidence

        definition_evidence = self._find_definition_evidence(coverage_keywords)
        if definition_evidence:
            evidences.append(definition_evidence)

        payment_evidence = self._find_payment_condition_evidence(coverage_keywords)
        if payment_evidence:
            evidences.append(payment_evidence)

        exclusion_evidence = self._find_exclusion_evidence(coverage_keywords)
        if exclusion_evidence:
            evidences.append(exclusion_evidence)

        logger.info(
            f"Coverage {canonical_coverage_code}: extracted {len(evidences)} evidence(s)"
        )
        return evidences

    def _find_definition_evidence(self, keywords: List[str]) -> Optional[Dict]:
        """
        Find definition section for coverage.

        Strategy:
        - 키워드 + "이라 함은" / "정의" / "의의" 패턴 탐지
        - "제2조 (용어의 정의)" 섹션에서 키워드 탐색
        - 해당 문단 전체를 excerpt로 추출
        """
        for page_num in range(min(100, len(self.pdf.pages))):  # 앞 100페이지 탐색
            page = self.pdf.pages[page_num]
            text = page.extract_text() or ""

            # 정의 패턴 탐지
            for keyword in keywords:
                # 예: "일반암이라 함은" 또는 "일반암의 정의" 또는 "'일반암'이라 함은"
                pattern = rf"['\"]?{keyword}['\"]?(이라\s*함은|의\s*정의|이란|\s*함은)"
                match = re.search(pattern, text)
                if match:
                    # 해당 문단 추출 (간단 구현: match 이후 300자)
                    start_pos = match.start()
                    excerpt = text[start_pos:start_pos + 300].strip()

                    # 첫 문장만 또는 첫 단락만 (간단 구현)
                    # 실제로는 더 정교한 문단 파싱 필요
                    # 여기서는 첫 마침표까지만
                    end_period = excerpt.find('.')
                    if end_period != -1 and end_period < 250:
                        excerpt = excerpt[:end_period + 1]

                    logger.info(
                        f"Found definition evidence on page {page_num + 1}: {excerpt[:60]}..."
                    )

                    return {
                        "evidence_type": "definition",
                        "excerpt": excerpt,
                        "source_page": page_num + 1,
                        "extraction_method": "deterministic_keyword_v1",
                        "extraction_confidence": "high"
                    }

        # Fallback: "제2조 (용어의 정의)" 섹션 전체 탐색
        for page_num in range(min(100, len(self.pdf.pages))):
            page = self.pdf.pages[page_num]
            text = page.extract_text() or ""

            # "제2조 (용어의 정의)" 섹션 찾기
            if "용어의 정의" in text or "용어의 뜻" in text:
                # 키워드가 이 페이지에 있는지 확인
                for keyword in keywords:
                    if keyword in text:
                        # 키워드 주변 300자 추출
                        idx = text.find(keyword)
                        excerpt = text[idx:idx + 300].strip()
                        end_period = excerpt.find('.')
                        if end_period != -1 and end_period < 250:
                            excerpt = excerpt[:end_period + 1]

                        logger.info(
                            f"Found definition evidence (fallback) on page {page_num + 1}: "
                            f"{excerpt[:60]}..."
                        )

                        return {
                            "evidence_type": "definition",
                            "excerpt": excerpt,
                            "source_page": page_num + 1,
                            "extraction_method": "deterministic_keyword_v1_fallback",
                            "extraction_confidence": "medium"
                        }

        logger.warning(f"Definition evidence not found for keywords: {keywords}")
        return None

    def _find_payment_condition_evidence(self, keywords: List[str]) -> Optional[Dict]:
        """
        Find payment condition section.

        Strategy:
        - 키워드 + "보험금 지급" / "지급사유" 패턴 탐지
        """
        for page_num in range(min(30, len(self.pdf.pages))):
            page = self.pdf.pages[page_num]
            text = page.extract_text() or ""

            for keyword in keywords:
                # 예: "일반암 진단 시 보험금" 또는 "일반암보험금 지급"
                pattern = rf"{keyword}.*?(보험금\s*지급|지급\s*사유|진단.*?보험금)"
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    start_pos = match.start()
                    excerpt = text[start_pos:start_pos + 300].strip()

                    # 첫 문장 또는 첫 문단
                    end_period = excerpt.find('.')
                    if end_period != -1 and end_period < 250:
                        excerpt = excerpt[:end_period + 1]

                    logger.info(
                        f"Found payment_condition evidence on page {page_num + 1}: "
                        f"{excerpt[:60]}..."
                    )

                    return {
                        "evidence_type": "payment_condition",
                        "excerpt": excerpt,
                        "source_page": page_num + 1,
                        "extraction_method": "deterministic_keyword_v1",
                        "extraction_confidence": "medium"
                    }

        logger.warning(f"Payment condition evidence not found for keywords: {keywords}")
        return None

    def _find_exclusion_evidence(self, keywords: List[str]) -> Optional[Dict]:
        """
        Find exclusion section.

        Strategy:
        - 키워드 + "면책" / "지급하지 않" / "제외" 패턴 탐지
        """
        for page_num in range(min(30, len(self.pdf.pages))):
            page = self.pdf.pages[page_num]
            text = page.extract_text() or ""

            # 면책 패턴 (키워드 독립적으로도 탐지 가능)
            # 예: "다음의 경우에는 보험금을 지급하지 않습니다"
            pattern = r"(면책|지급하지\s*않|보험금.*?제외|다음.*?경우.*?지급하지)"
            match = re.search(pattern, text)
            if match:
                start_pos = match.start()
                # 면책 조항은 보통 리스트 형태 → 더 긴 excerpt 필요
                excerpt = text[start_pos:start_pos + 400].strip()

                # 첫 3개 항목 정도만 (간단 구현)
                lines = excerpt.split('\n')[:5]
                excerpt = '\n'.join(lines)

                logger.info(
                    f"Found exclusion evidence on page {page_num + 1}: {excerpt[:60]}..."
                )

                return {
                    "evidence_type": "exclusion",
                    "excerpt": excerpt,
                    "source_page": page_num + 1,
                    "extraction_method": "deterministic_keyword_v1",
                    "extraction_confidence": "medium"
                }

        logger.warning(f"Exclusion evidence not found for keywords: {keywords}")
        return None


def load_mapped_coverages(conn: PGConnection) -> List[Dict]:
    """
    Load MAPPED coverages from v2.coverage_mapping.

    Returns:
        List of {
            canonical_coverage_code: str,
            product_id: str,
            insurer_code: str,
            coverage_name_raw: str  # from proposal_coverage (insurer_coverage_name)
        }
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT
            m.canonical_coverage_code,
            p.product_id,
            p.insurer_code,
            pc.insurer_coverage_name as coverage_name_raw
        FROM v2.coverage_mapping m
        JOIN v2.template t ON m.template_id = t.template_id
        JOIN v2.product p ON t.product_id = p.product_id
        JOIN v2.proposal_coverage pc ON pc.coverage_id = m.coverage_id
        WHERE m.mapping_status = 'MAPPED'
        ORDER BY m.canonical_coverage_code;
    """)
    rows = cur.fetchall()
    cur.close()

    coverages = []
    for row in rows:
        coverages.append({
            "canonical_coverage_code": row[0],
            "product_id": row[1],
            "insurer_code": row[2],
            "coverage_name_raw": row[3]
        })

    logger.info(f"Loaded {len(coverages)} MAPPED coverages")
    return coverages


def get_policy_pdf_path(insurer_code: str, doc_type: str = "policy") -> Optional[Path]:
    """
    Get policy/business_rules PDF path for insurer.

    Args:
        insurer_code: SAMSUNG, MERITZ, etc.
        doc_type: "policy" or "business_rules"

    Returns:
        Path to PDF or None
    """
    # Mapping: insurer_code → directory name
    insurer_dir_map = {
        "SAMSUNG": "samsung",
        "MERITZ": "meritz",
        # ... 다른 보험사 추가
    }

    doc_type_dir_map = {
        "policy": "약관",
        "business_rules": "사업방법서"
    }

    insurer_dir = insurer_dir_map.get(insurer_code)
    doc_dir = doc_type_dir_map.get(doc_type)

    if not insurer_dir or not doc_dir:
        return None

    # data/{insurer_dir}/{doc_dir} 디렉토리에서 첫 번째 PDF 찾기
    data_root = Path(__file__).parent.parent.parent.parent / "data"
    search_dir = data_root / insurer_dir / doc_dir

    if not search_dir.exists():
        logger.warning(f"Directory not found: {search_dir}")
        return None

    pdf_files = list(search_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF found in {search_dir}")
        return None

    return pdf_files[0]


def extract_keywords_from_coverage_name(coverage_name_raw: str) -> List[str]:
    """
    Extract keywords from coverage_name_raw for evidence search.

    Example:
        "일반암진단비" → ["일반암", "암진단"]
        "유사암진단비(갑상선암,경계성종양,제자리암,기타피부암,전립선암)" → ["유사암", "암진단"]
    """
    # 간단 구현: 괄호 제거 + "진단비" 제거
    cleaned = re.sub(r'\(.*?\)', '', coverage_name_raw)
    cleaned = cleaned.replace("진단비", "")

    # 키워드 후보: 2글자 이상 토큰
    tokens = re.findall(r'\w{2,}', cleaned)

    # 중복 제거
    keywords = list(set(tokens))

    logger.info(f"Extracted keywords from '{coverage_name_raw}': {keywords}")
    return keywords


def insert_evidence(
    conn: PGConnection,
    canonical_coverage_code: str,
    product_id: str,
    insurer_code: str,
    evidence_type: str,
    excerpt: str,
    source_doc_type: str,
    source_doc_id: str,
    source_page: int,
    extraction_method: str,
    extraction_confidence: str
) -> None:
    """
    Insert evidence into v2.coverage_evidence (idempotent).

    Constitutional Validation (STEP NEXT-AE-FIX):
    - source_doc_type must be: policy, business_rules, or product_summary
    - Proposal documents are NOT allowed as evidence source

    Idempotency:
    - excerpt_hash로 중복 방지
    """
    # Constitutional validation: source_doc_type
    ALLOWED_SOURCE_DOC_TYPES = ['policy', 'business_rules', 'product_summary']
    if source_doc_type not in ALLOWED_SOURCE_DOC_TYPES:
        raise ValueError(
            f"Invalid source_doc_type: '{source_doc_type}'. "
            f"Allowed values: {ALLOWED_SOURCE_DOC_TYPES}. "
            f"Proposal documents cannot be used as evidence source."
        )

    # excerpt_hash 생성
    excerpt_hash = hashlib.sha256(excerpt.encode('utf-8')).hexdigest()[:16]

    cur = conn.cursor()

    # Upsert (ON CONFLICT DO NOTHING)
    cur.execute("""
        INSERT INTO v2.coverage_evidence (
            canonical_coverage_code,
            product_id,
            insurer_code,
            evidence_type,
            excerpt,
            source_doc_type,
            source_doc_id,
            source_page,
            extraction_method,
            extraction_confidence,
            notes
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING;
    """, (
        canonical_coverage_code,
        product_id,
        insurer_code,
        evidence_type,
        excerpt,
        source_doc_type,
        source_doc_id,
        source_page,
        extraction_method,
        extraction_confidence,
        f"excerpt_hash={excerpt_hash}"
    ))

    if cur.rowcount > 0:
        logger.info(f"Inserted {evidence_type} evidence for {canonical_coverage_code}")
    else:
        logger.info(f"Duplicate {evidence_type} evidence for {canonical_coverage_code} (skipped)")

    cur.close()


def main():
    """
    Main pipeline: Extract evidence for all MAPPED coverages.
    """
    logger.info("=" * 60)
    logger.info("STEP NEXT-AE: Evidence Extraction (Document-Based)")
    logger.info("=" * 60)

    # 1. DB 연결 (WRITE mode required)
    conn = get_db_connection(readonly=False)
    logger.info("Connected to DB (write mode)")

    # 2. MAPPED coverages 로드
    coverages = load_mapped_coverages(conn)
    if not coverages:
        logger.error("No MAPPED coverages found. Exiting.")
        conn.close()
        return

    # 3. Insurer별로 PDF 1회 열기 (효율)
    insurer_extractors = {}

    for cov in coverages:
        insurer_code = cov["insurer_code"]
        canonical_coverage_code = cov["canonical_coverage_code"]
        product_id = cov["product_id"]
        coverage_name_raw = cov["coverage_name_raw"]

        # PDF 경로 확인
        if insurer_code not in insurer_extractors:
            policy_pdf_path = get_policy_pdf_path(insurer_code, "policy")
            if not policy_pdf_path:
                logger.warning(f"Policy PDF not found for {insurer_code}, skipping")
                insurer_extractors[insurer_code] = None
                continue

            extractor = PolicyEvidenceExtractor(policy_pdf_path, "policy")
            insurer_extractors[insurer_code] = extractor
            logger.info(f"Loaded policy PDF for {insurer_code}: {policy_pdf_path.name}")

        extractor = insurer_extractors.get(insurer_code)
        if not extractor:
            continue

        # 4. 키워드 추출
        keywords = extract_keywords_from_coverage_name(coverage_name_raw)

        # 5. Evidence 추출
        evidences = extractor.extract_evidence_for_coverage(
            canonical_coverage_code, keywords
        )

        # 6. DB 저장
        for ev in evidences:
            insert_evidence(
                conn,
                canonical_coverage_code=canonical_coverage_code,
                product_id=product_id,
                insurer_code=insurer_code,
                evidence_type=ev["evidence_type"],
                excerpt=ev["excerpt"],
                source_doc_type="policy",
                source_doc_id=str(extractor.pdf_path),
                source_page=ev["source_page"],
                extraction_method=ev["extraction_method"],
                extraction_confidence=ev["extraction_confidence"]
            )

    # 7. Cleanup
    for extractor in insurer_extractors.values():
        if extractor:
            extractor.close()

    conn.commit()
    conn.close()

    logger.info("=" * 60)
    logger.info("Evidence extraction complete")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
