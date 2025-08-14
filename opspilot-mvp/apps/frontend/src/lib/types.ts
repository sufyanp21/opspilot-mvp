export interface FileUploadResponse {
  file_id: string;
  columns: string[];
}

export interface FileInfo {
  id: string;
  kind: 'internal' | 'cleared' | 'span';
  original_name: string;
  uploaded_at: string;
  processing_status: string;
  columns?: string[];
}

export interface ColumnMapping {
  internal: Record<string, string>;
  cleared: Record<string, string>;
}

export interface ToleranceConfig {
  price_ticks: number;
  qty: number;
}

export interface ReconcileRequest {
  internal_file_id: string;
  cleared_file_id: string;
  column_map: ColumnMapping;
  match_keys: string[];
  tolerances: ToleranceConfig;
}

export interface ExceptionInfo {
  id: string;
  keys: Record<string, any>;
  internal?: Record<string, any>;
  cleared?: Record<string, any>;
  diff?: Record<string, any>;
  status: 'OPEN' | 'RESOLVED';
}

export interface ReconcileSummary {
  total: number;
  matched: number;
  mismatched: number;
  pct_matched: number;
}

export interface ReconcileResponse {
  run_id: string;
  summary: ReconcileSummary;
  exceptions: ExceptionInfo[];
}

export interface ReconRunInfo {
  id: string;
  status: string;
  started_at: string;
  finished_at?: string;
  internal_file_id: string;
  cleared_file_id: string;
  summary?: ReconcileSummary;
}

export interface SpanUploadResponse {
  file_id: string;
  asof: string;
  rows_ingested: number;
}

export interface SpanDeltaInfo {
  product: string;
  account: string;
  scan_before?: number;
  scan_after: number;
  delta: number;
}
