import type { AnalysisRequest, AnalysisResponse } from "../types/analysis";

/**
 * Backend origin, e.g. https://nyayalay-api.onrender.com
 * Both variable names are accepted; a trailing "/" or "/api" is tolerated.
 */
const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000"
)
  .trim()
  .replace(/\/+$/, "")
  .replace(/\/api$/, "");

// Render's free tier sleeps when idle and can take ~1 minute to wake up,
// and the analysis itself makes several LLM calls.
const REQUEST_TIMEOUT_MS = 120_000;

/** Fire-and-forget request that wakes a sleeping backend before the user submits. */
export function wakeBackend(): void {
  fetch(`${API_BASE_URL}/api/health`).catch(() => undefined);
}

export async function analyzeIncident(
  incident: string
): Promise<AnalysisResponse> {
  const request: AnalysisRequest = { incident };
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/analysis`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
      signal: controller.signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error(
        "The server took too long to respond. It may be starting up — please try again in a moment."
      );
    }
    throw new Error(
      "Could not reach the Nyayalay server. Please check your connection or try again shortly."
    );
  } finally {
    window.clearTimeout(timer);
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    const detail = errorData?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail) && detail[0]?.msg
          ? detail[0].msg
          : `Server error: ${response.status}`;
    throw new Error(message);
  }

  return response.json();
}
