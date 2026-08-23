import { useState } from "react";
import { analyzeIncident } from "../services/api";
import type { AnalysisResponse } from "../types/analysis";

export default function Home() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();

    if (query.trim().length < 10) {
      setError("Please describe your situation in a little more detail.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      setResult(null);

      const response = await analyzeIncident(query);
      setResult(response);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="home-page">
      <section className="hero">
        <div className="badge">AI-Powered Legal Assistance</div>

        <h1>
          Understand your legal situation with
          <span> Nyayalay</span>
        </h1>

        <p className="hero-description">
          Describe your situation in simple language. Nyayalay analyzes the
          information provided and identifies relevant legal provisions.
        </p>

        <form className="query-form" onSubmit={handleSubmit}>
          <textarea
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Example: Someone threatened me and forcefully took away my mobile phone and wallet."
            rows={6}
          />

          <button type="submit" disabled={loading}>
            {loading ? "Analyzing your situation..." : "Analyze My Situation"}
          </button>
        </form>

        {error && <p className="error-message">{error}</p>}
      </section>

      {result && (
        <section className="result-section">
          <div className="result-card">
            <div className="result-header">
              <span className="result-label">Nyayalay Analysis</span>

              {result.route?.domain && (
                <span className="category-badge">
                  {result.route.domain}
                </span>
              )}
            </div>

            <h2>Analysis Status</h2>
            <p>{result.message || result.status}</p>

            {result.facts?.summary && (
              <>
                <h2>Incident Summary</h2>
                <p>{result.facts.summary}</p>
              </>
            )}

            {result.result ? (
              <div className="legal-provision">
                <h2>Relevant Legal Provision</h2>

                <article className="source-card">
                  <h3>
                    {result.result.act} — Section {result.result.section}
                  </h3>

                  <h4>{result.result.title}</h4>

                  <p>{result.result.text}</p>
                </article>
              </div>
            ) : (
              <div className="analysis-warning">
                <h2>No Final Provision Selected</h2>
                <p>
                  Nyayalay could not confidently verify a legal provision based
                  on the currently available evidence.
                </p>
              </div>
            )}

            {result.classification && (
              <div className="classification-section">
                <h2>AI Classification</h2>

                <p>
                  <strong>Proposed Section:</strong>{" "}
                  {result.classification.section || "Not selected"}
                </p>

                <p>
                  <strong>Confidence:</strong>{" "}
                  {Math.round(result.classification.confidence * 100)}%
                </p>

                <p>{result.classification.explanation}</p>
              </div>
            )}

            {result.verification && (
              <div className="verification-section">
                <h2>Verification</h2>

                <p>
                  <strong>Status:</strong>{" "}
                  {result.verification.supported
                    ? "Supported"
                    : "Could not be verified"}
                </p>

                <p>{result.verification.reasoning}</p>
              </div>
            )}

            {result.facts?.missing_or_uncertain_facts &&
              result.facts.missing_or_uncertain_facts.length > 0 && (
                <div className="missing-facts">
                  <h2>Information That May Be Important</h2>

                  <ul>
                    {result.facts.missing_or_uncertain_facts.map(
                      (fact, index) => (
                        <li key={index}>{fact}</li>
                      )
                    )}
                  </ul>
                </div>
              )}

            <div className="disclaimer">
              <strong>Important:</strong> Nyayalay provides legal information
              and AI-assisted analysis. It does not replace advice from a
              qualified legal professional.
            </div>
          </div>
        </section>
      )}
    </main>
  );
}