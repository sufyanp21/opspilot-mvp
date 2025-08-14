import type { ExceptionInfo } from './types';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export interface FileUploadResponse {
  file_id: string;
  columns: string[];
}

export interface FileInfo {
  id: string;
  kind: string;
  original_name: string;
  uploaded_at: string;
  processing_status: string;
  columns?: string[];
}

export interface ReconcileRequest {
  internal_file_id: string;
  cleared_file_id: string;
  column_map: {
    internal: Record<string, string>;
    cleared: Record<string, string>;
  };
  match_keys: string[];
  tolerances: {
    price_ticks: number;
    qty: number;
  };
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

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`API Error: ${response.status} - ${error}`);
    }

    return response.json();
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    return this.request('/api/v1/health');
  }

  // File operations
  async uploadFile(file: File, kind: string): Promise<FileUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('kind', kind);

    const response = await fetch(`${this.baseUrl}/api/v1/files/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Upload failed: ${response.status} - ${error}`);
    }

    return response.json();
  }

  async listFiles(): Promise<FileInfo[]> {
    return this.request('/api/v1/files');
  }

  async getFile(fileId: string): Promise<FileInfo> {
    return this.request(`/api/v1/files/${fileId}`);
  }

  // Reconciliation operations
  async runReconciliation(request: ReconcileRequest): Promise<ReconcileResponse> {
    return this.request('/api/v1/reconcile', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async listReconciliationRuns(): Promise<any[]> {
    return this.request('/api/v1/reconcile/runs');
  }

  async getRunExceptions(runId: string): Promise<ExceptionInfo[]> {
    return this.request(`/api/v1/reconcile/runs/${runId}/exceptions`);
  }

  // SPAN operations
  async uploadSpanFile(file: File): Promise<SpanUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/api/v1/span/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`SPAN upload failed: ${response.status} - ${error}`);
    }

    return response.json();
  }

  async getSpanChanges(asof: string): Promise<SpanDeltaInfo[]> {
    return this.request(`/api/v1/span/changes?asof=${asof}`);
  }

  async getSpanSnapshots(params?: {
    asof?: string;
    product?: string;
    account?: string;
  }): Promise<any[]> {
    const searchParams = new URLSearchParams();
    if (params?.asof) searchParams.append('asof', params.asof);
    if (params?.product) searchParams.append('product', params.product);
    if (params?.account) searchParams.append('account', params.account);

    const query = searchParams.toString();
    return this.request(`/api/v1/span/snapshots${query ? `?${query}` : ''}`);
  }
}

export const apiClient = new ApiClient();
