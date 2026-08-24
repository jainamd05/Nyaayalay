import type {
    AnalysisRequest,
    AnalysisResponse,
  } from "../types/analysis";
  
  // const API_BASE_URL = "http://127.0.0.1:8000/api";
  // const API_BASE_URL = `${import.meta.env.VITE_API_URL}/api`;
  const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export async function analyzeIncident(incident: string) {
  const response = await fetch(`${API_BASE_URL}/api/analysis`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      incident,
    }),
  });

  if (!response.ok) {
    throw new Error(`Analysis request failed: ${response.status}`);
  }

  return response.json();
}