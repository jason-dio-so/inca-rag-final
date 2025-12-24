"""
Proposal Universe Pipeline

E2E orchestration:
1. Parse proposals → universe
2. Map to canonical codes
3. Extract slots
4. Store in DB

Constitution: All principles enforced at each stage
"""

import logging
from pathlib import Path
from typing import List, Dict
import psycopg2
from psycopg2.extras import RealDictCursor
import json

from .parser import ProposalCoverageParser
from .mapper import CoverageMapper
from .extractor import SlotExtractor


logger = logging.getLogger(__name__)


class ProposalUniversePipeline:
    """
    End-to-end pipeline for proposal universe ingestion.

    Steps:
    1. Parse PDF → coverage universe
    2. Map coverage names → canonical codes
    3. Extract slots from proposal text
    4. Insert into database
    """

    def __init__(
        self,
        db_connection,
        excel_path: Path
    ):
        """
        Initialize pipeline.

        Args:
            db_connection: PostgreSQL connection
            excel_path: Path to 담보명mapping자료.xlsx
        """
        self.db = db_connection
        self.mapper = CoverageMapper(excel_path)
        self.extractor = SlotExtractor()

    def ingest_proposal(
        self,
        insurer: str,
        proposal_path: Path
    ) -> Dict:
        """
        Ingest single proposal into universe.

        Args:
            insurer: Insurer name (e.g., "Samsung", "Meritz")
            proposal_path: Path to proposal PDF

        Returns:
            Dict with statistics
        """
        logger.info(f"Ingesting proposal: {insurer} - {proposal_path}")

        # Step 1: Parse PDF
        parser = ProposalCoverageParser(insurer, proposal_path)
        coverages = parser.parse()

        logger.info(f"Parsed {len(coverages)} coverages from {proposal_path}")

        stats = {
            'total_coverages': len(coverages),
            'inserted_universe': 0,
            'inserted_mapped': 0,
            'inserted_slots': 0,
            'mapping_status': {
                'MAPPED': 0,
                'UNMAPPED': 0,
                'AMBIGUOUS': 0,
            }
        }

        # Step 2-4: Process each coverage
        for cov in coverages:
            try:
                # Insert into universe
                universe_id = self._insert_universe(cov)
                stats['inserted_universe'] += 1

                # Map to canonical code
                mapping = self.mapper.map(
                    normalized_name=cov['normalized_name'],
                    insurer_coverage_name=cov['insurer_coverage_name']
                )
                mapped_id = self._insert_mapped(universe_id, mapping)
                stats['inserted_mapped'] += 1
                stats['mapping_status'][mapping['mapping_status']] += 1

                # Extract slots (only if MAPPED)
                if mapping['mapping_status'] == 'MAPPED':
                    slots = self.extractor.extract(
                        coverage_name=cov['insurer_coverage_name'],
                        span_text=cov['span_text'],
                        amount_value=cov['amount_value'],
                        page=cov['source_page'],
                        proposal_id=cov['proposal_id']
                    )
                    self._insert_slots(mapped_id, slots)
                    stats['inserted_slots'] += 1

            except Exception as e:
                logger.error(f"Failed to process coverage {cov['insurer_coverage_name']}: {e}")
                continue

        logger.info(f"Ingestion complete: {stats}")
        return stats

    def _insert_universe(self, coverage: Dict) -> int:
        """Insert into proposal_coverage_universe, return ID."""
        query = """
        INSERT INTO proposal_coverage_universe (
            insurer,
            proposal_id,
            insurer_coverage_name,
            normalized_name,
            currency,
            amount_value,
            payout_amount_unit,
            source_page,
            span_text,
            content_hash
        ) VALUES (
            %(insurer)s,
            %(proposal_id)s,
            %(insurer_coverage_name)s,
            %(normalized_name)s,
            %(currency)s,
            %(amount_value)s,
            %(payout_amount_unit)s,
            %(source_page)s,
            %(span_text)s,
            %(content_hash)s
        )
        ON CONFLICT (content_hash) DO NOTHING
        RETURNING id;
        """

        with self.db.cursor() as cur:
            cur.execute(query, coverage)
            result = cur.fetchone()

            if result is None:
                # Already exists, get existing ID
                cur.execute(
                    "SELECT id FROM proposal_coverage_universe WHERE content_hash = %s",
                    (coverage['content_hash'],)
                )
                result = cur.fetchone()

            self.db.commit()
            return result[0]

    def _insert_mapped(self, universe_id: int, mapping: Dict) -> int:
        """Insert into proposal_coverage_mapped, return ID."""
        query = """
        INSERT INTO proposal_coverage_mapped (
            universe_id,
            canonical_coverage_code,
            mapping_status,
            mapping_evidence
        ) VALUES (
            %s, %s, %s, %s
        )
        ON CONFLICT (universe_id) DO UPDATE
        SET
            canonical_coverage_code = EXCLUDED.canonical_coverage_code,
            mapping_status = EXCLUDED.mapping_status,
            mapping_evidence = EXCLUDED.mapping_evidence
        RETURNING id;
        """

        with self.db.cursor() as cur:
            cur.execute(
                query,
                (
                    universe_id,
                    mapping['canonical_coverage_code'],
                    mapping['mapping_status'],
                    json.dumps(mapping['mapping_evidence']),
                )
            )
            result = cur.fetchone()
            self.db.commit()
            return result[0]

    def _insert_slots(self, mapped_id: int, slots: Dict) -> int:
        """Insert into proposal_coverage_slots, return ID."""
        query = """
        INSERT INTO proposal_coverage_slots (
            mapped_id,
            event_type,
            disease_scope_raw,
            disease_scope_norm,
            waiting_period_days,
            coverage_start_rule,
            reduction_periods,
            payout_limit,
            treatment_method,
            hospitalization_exclusions,
            renewal_flag,
            renewal_period_years,
            renewal_max_age,
            source_confidence,
            qualification_suffix,
            evidence
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (mapped_id) DO UPDATE
        SET
            event_type = EXCLUDED.event_type,
            disease_scope_raw = EXCLUDED.disease_scope_raw,
            waiting_period_days = EXCLUDED.waiting_period_days,
            reduction_periods = EXCLUDED.reduction_periods,
            payout_limit = EXCLUDED.payout_limit,
            treatment_method = EXCLUDED.treatment_method,
            renewal_flag = EXCLUDED.renewal_flag,
            renewal_period_years = EXCLUDED.renewal_period_years,
            source_confidence = EXCLUDED.source_confidence,
            qualification_suffix = EXCLUDED.qualification_suffix,
            evidence = EXCLUDED.evidence
        RETURNING id;
        """

        with self.db.cursor() as cur:
            cur.execute(
                query,
                (
                    mapped_id,
                    slots['event_type'],
                    slots['disease_scope_raw'],
                    json.dumps(slots['disease_scope_norm']) if slots['disease_scope_norm'] else None,
                    slots['waiting_period_days'],
                    slots['coverage_start_rule'],
                    json.dumps(slots['reduction_periods']) if slots['reduction_periods'] else None,
                    json.dumps(slots['payout_limit']) if slots['payout_limit'] else None,
                    slots['treatment_method'],
                    json.dumps(slots['hospitalization_exclusions']) if slots['hospitalization_exclusions'] else None,
                    slots['renewal_flag'],
                    slots['renewal_period_years'],
                    slots['renewal_max_age'],
                    slots['source_confidence'],
                    slots['qualification_suffix'],
                    json.dumps(slots['evidence']),
                )
            )
            result = cur.fetchone()
            self.db.commit()
            return result[0]
