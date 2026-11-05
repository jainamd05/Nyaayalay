import type { AnalysisResponse } from "../types/analysis";

const LOCAL_API_BASE_URL = "http://127.0.0.1:8000";

/**
 * Resolve the backend base URL.
 *
 * - `VITE_API_BASE_URL` is the preferred variable; `VITE_API_URL` (used by an
 *   earlier version of this app) is still accepted so an existing Vercel
 *   configuration keeps working.
 * - A trailing "/" or "/api" is stripped, so both "https://x.onrender.com"
 *   and "https://x.onrender.com/api/" work.
 * - Falls back to the local backend only in development; a production build
 *   without the variable reports a clear configuration error instead of
 *   silently calling 127.0.0.1 on the visitor's machine.
 */
function resolveApiBaseUrl(): string | null {
  const configured = (
    import.meta.env.VITE_API_BASE_URL ||
    import.meta.env.VITE_API_URL ||
    ""
  ).trim();

  if (configured) {
    return configured.replace(/\/+$/, "").replace(/\/api$/, "");
  }

  return import.meta.env.DEV ? LOCAL_API_BASE_URL : null;
}

export const API_BASE_URL = resolveApiBaseUrl();

// Render's free tier can take ~a minute to wake up, and the analysis itself
// makes several LLM calls, so allow a generous timeout.
const REQUEST_TIMEOUT_MS = 150_000;

function requireBaseUrl(): string {
  if (!API_BASE_URL) {
    throw new Error(
      "The app is not connected to a backend. Set VITE_API_BASE_URL to the backend URL and redeploy."
    );
  }
  return API_BASE_URL;
}

async function readErrorDetail(response: Response): Promise<string | null> {
  try {
    const body = await response.json();
    const detail = body?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg);
  } catch {
    // Non-JSON error body (e.g. a proxy error page).
  }
  return null;
}

/**
 * Fire-and-forget request that wakes a sleeping backend (Render free tier)
 * while the user is still typing.
 */
export function wakeBackend(): void {
  if (!API_BASE_URL) return;
  fetch(`${API_BASE_URL}/api/health`, { method: "GET" }).catch(() => {
    // Ignored: the real request will report any problem.
  });
}

export async function analyzeIncident(incident: string): Promise<AnalysisResponse> {
  const baseUrl = requireBaseUrl();
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  let response: Response;
  try {
    response = await fetch(`${baseUrl}/api/analysis`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ incident }),
      signal: controller.signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error("The analysis took too long. Please try again.");
    }
    throw new Error(
      "Could not reach the Nyayalay server. If it was idle it may be starting up — please try again in a minute."
    );
  } finally {
    window.clearTimeout(timeout);
  }

  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new Error(detail || `Analysis request failed (HTTP ${response.status}).`);
  }

  return (await response.json()) as AnalysisResponse;
}
