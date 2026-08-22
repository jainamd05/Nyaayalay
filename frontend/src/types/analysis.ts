export interface AnalysisResponse {
  status: string;
  message?: string | null;
  route?: Record<string, unknown> | null;
  facts?: Record<string, unknown> | null;
  candidates?: Record<string, unknown>[] | null;
  classification?: Record<string, unknown> | null;
  verification?: Record<string, unknown> | null;
  result?: {
    act: string;
    section: string;
    title: string;
    text: string;
  } | null;
}
