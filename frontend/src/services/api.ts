import type { LegalResponse } from "../types/legal";

const API_BASE_URL = "http://127.0.0.1:8000";

export async function analyzeLegalQuery(
  query: string
): Promise<LegalResponse> {
  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query,
    }),
  });

  if (!response.ok) {
    throw new Error("Unable to process your legal query.");
  }

  return response.json();
}