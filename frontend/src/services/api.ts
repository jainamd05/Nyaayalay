import type {
    AnalysisRequest,
    AnalysisResponse,
  } from "../types/analysis";
  
  const API_BASE_URL = "http://127.0.0.1:8000/api";
  
  export async function analyzeIncident(
    incident: string
  ): Promise<AnalysisResponse> {
    const request: AnalysisRequest = {
      incident,
    };
  
    const response = await fetch(`${API_BASE_URL}/analysis`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });
  
    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
  
      throw new Error(
        errorData?.detail ||
          `Server error: ${response.status}`
      );
    }
  
    return response.json();
  }