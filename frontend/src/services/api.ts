import type { AnalysisResponse } from "../types/analysis";

const API_BASE = "http://127.0.0.1:8000/api";

export async function analyzeIncident(incident: string): Promise<AnalysisResponse> {
  const response = await fetch(`${API_BASE}/analysis`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ incident }),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "Analysis request failed.");
  }

  return response.json();
}
