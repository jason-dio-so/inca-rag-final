/**
 * ViewModel TypeScript types (contract-driven, schema-compliant)
 * Based on: docs/ui/compare_view_model.schema.json
 *
 * Constitution: Fact-only, No Recommendation, Presentation Only
 */

export type InsurerCode =
  | "SAMSUNG"
  | "HANWHA"
  | "LOTTE"
  | "MERITZ"
  | "KB"
  | "HYUNDAI"
  | "HEUNGKUK"
  | "DB";

export type StatusCode =
  | "OK"
  | "MISSING_EVIDENCE"
  | "UNMAPPED"
  | "AMBIGUOUS"
  | "OUT_OF_UNIVERSE";

export type DocType =
  | "가입설계서"
  | "약관"
  | "상품요약서"
  | "사업방법서";

export type SlotKey =
  | "waiting_period"
  | "payment_frequency"
  | "diagnosis_definition"
  | "method_condition"
  | "exclusion_scope"
  | "payout_limit"
  | "disease_scope";

export interface AmountDisplay {
  amount_value: number;
  amount_unit: "만원";
  display_text: string;
  evidence_ref_id?: string;
}

export interface Header {
  user_query: string;
  normalized_query?: string;
}

export interface InsurerSnapshot {
  insurer: InsurerCode;
  headline_amount: AmountDisplay | null;
  status: StatusCode;
}

export interface Snapshot {
  comparison_basis: string;
  insurers: InsurerSnapshot[];
}

export interface PayoutCondition {
  slot_key: SlotKey;
  value_text: string;
  evidence_ref_id?: string;
}

export interface FactTableRow {
  insurer: InsurerCode;
  coverage_title_normalized: string;
  benefit_amount: AmountDisplay | null;
  payout_conditions: PayoutCondition[];
  term_text: string | null;
  note_text: string | null;
  row_status: StatusCode;
}

export interface FactTable {
  columns: readonly [
    "보험사",
    "담보명(정규화)",
    "보장금액",
    "지급 조건 요약",
    "보험기간",
    "비고"
  ];
  rows: FactTableRow[];
}

export interface BBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface SourceMeta {
  filename?: string;
  file_hash?: string;
}

export interface EvidencePanel {
  id: string;
  insurer: InsurerCode;
  doc_type: DocType;
  doc_title?: string;
  page: string | number;
  excerpt: string;
  bbox?: BBox | null;
  source_meta?: SourceMeta | null;
}

export interface DebugInfo {
  resolved_coverage_codes?: string[] | null;
  retrieval?: {
    topk?: number | null;
    strategy?: string | null;
    doc_priority?: string[] | null;
  } | null;
  warnings?: string[] | null;
  execution_time_ms?: number | null;
}

export interface CompareViewModel {
  schema_version: string;
  generated_at: string;
  header: Header;
  snapshot: Snapshot;
  fact_table: FactTable;
  evidence_panels: EvidencePanel[];
  debug?: DebugInfo;
}
