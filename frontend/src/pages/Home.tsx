import { useState } from "react";
import { analyzeLegalQuery } from "../services/api";
import type { LegalResponse } from "../types/legal";

export default function Home() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<LegalResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();

    if (!query.trim()) {
      setError("Please describe your legal situation first.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      setResult(null);

      const response = await analyzeLegalQuery(query);
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
          Describe your situation in simple language. Nyayalay helps identify
          relevant legal information and provides an AI-assisted explanation.
        </p>

        <form className="query-form" onSubmit={handleSubmit}>
          <textarea
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Example: Someone took my money but is refusing to return it. What legal options do I have?"
            rows={6}
          />

          <button type="submit" disabled={loading}>
            {loading ? "Analyzing your case..." : "Analyze My Situation"}
          </button>
        </form>

        {error && <p className="error-message">{error}</p>}
      </section>

      {result && (
        <section className="result-section">
          <div className="result-card">
            <div className="result-header">
              <span className="result-label">Legal Analysis</span>

              {result.category && (
                <span className="category-badge">{result.category}</span>
              )}
            </div>

            {result.summary && (
              <>
                <h2>Summary</h2>
                <p>{result.summary}</p>
              </>
            )}

            <h2>What Nyayalay Found</h2>
            <p>{result.answer}</p>

            {result.sources && result.sources.length > 0 && (
              <div className="sources-section">
                <h2>Relevant Legal Sources</h2>

                {result.sources.map((source, index) => (
                  <article className="source-card" key={index}>
                    <h3>{source.title}</h3>

                    {source.content && <p>{source.content}</p>}

                    {source.source && (
                      <small>Source: {source.source}</small>
                    )}
                  </article>
                ))}
              </div>
            )}

            <div className="disclaimer">
              <strong>Important:</strong>{" "}
              {result.disclaimer ||
                "Nyayalay provides legal information and does not replace professional legal advice."}
            </div>
          </div>
        </section>
      )}
    </main>
  );
}