const API_BASE = "https://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`${path} failed: ${response.status}`);
  }
  return response.json();
}

export interface LabResultRow {
  id: number;
  loinc_code: string | null;
  display_name: string;
  category: string | null;
  value: number | null;
  value_text: string | null;
  unit: string | null;
  reference_range_low: number | null;
  reference_range_high: number | null;
  reference_range_text: string | null;
  collected_at: string | null;
  out_of_range: boolean | null;
}

export interface LabsResponse {
  categories: { category: string; results: LabResultRow[] }[];
}

export interface TrendMetric {
  loinc_code: string | null;
  display_name: string;
  data_points: number;
}

export interface TrendPoint {
  collected_at: string | null;
  value: number | null;
  value_text: string | null;
  reference_range_low: number | null;
  reference_range_high: number | null;
}

export interface TrendResponse {
  display_name: string;
  unit: string | null;
  points: TrendPoint[];
}

export interface ReportRow {
  id: number;
  resource_type: string;
  report_type: string | null;
  title: string;
  narrative_text: string | null;
  source_attachment_url: string | null;
  collected_at: string | null;
}

export const api = {
  authStatus: () => request<{ connected: boolean; access_token_valid: boolean }>("/auth/status"),
  login: () => {
    window.open("https://localhost:8000/auth/login", "_blank");
  },
  sync: () => request<{ lab_results: number; diagnostic_reports: number; documents: number }>("/sync", { method: "POST" }),
  labs: (params?: { category?: string; search?: string }) => {
    const query = new URLSearchParams(params as Record<string, string>).toString();
    return request<LabsResponse>(`/labs${query ? `?${query}` : ""}`);
  },
  trendMetrics: () => request<TrendMetric[]>("/trends/metrics"),
  trend: (loincCode: string) => request<TrendResponse>(`/trends?loinc_code=${encodeURIComponent(loincCode)}`),
  reports: (reportType?: string) =>
    request<ReportRow[]>(`/reports${reportType ? `?report_type=${encodeURIComponent(reportType)}` : ""}`),
  summary: (refresh = false) => request<{ summary: string }>(`/summary${refresh ? "?refresh=true" : ""}`),
  chat: (message: string) => request<{ reply: string }>("/chat", { method: "POST", body: JSON.stringify({ message }) }),
};
