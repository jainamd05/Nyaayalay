import { useState } from "react";
import { Search, ShieldCheck, Scale, BookOpen, AlertTriangle } from "lucide-react";
import { analyzeIncident } from "./services/api";
import type { AnalysisResponse } from "./types/analysis";
import "./styles/app.css";

export default function App() {
  const [incident, setIncident] = useState("");
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleAnalyze() {
    if (incident.trim().length < 10) return;

    setLoading(true);
    try {
      setResult(await analyzeIncident(incident));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="shell">
      <nav className="navbar">
        <div className="brand">
          <div className="brand-mark"><Scale size={22} /></div>
          <span>Nyayalay</span>
        </div>
        <span className="badge"><ShieldCheck size={15} /> Grounded Legal AI</span>
      </nav>

      <section className="hero">
        <p className="eyebrow">LEGAL INFORMATION ASSISTANT</p>
        <h1>Understand your legal situation.</h1>
        <p className="subtitle">
          Describe what happened in plain language. Nyayalay extracts the facts,
          searches its legal corpus, and verifies the suggested provisions.
        </p>

        <div className="input-card">
          <textarea
            value={incident}
            onChange={(e) => setIncident(e.target.value)}
            placeholder="Describe what happened..."
            rows={7}
          />
          <button onClick={handleAnalyze} disabled={loading || incident.trim().length < 10}>
            <Search size={18} />
            {loading ? "Analyzing..." : "Analyze incident"}
          </button>
        </div>
      </section>

      {result && (
        <section className="result">
          <div className="result-header">
            <div>
              <p className="eyebrow">ANALYSIS RESULT</p>
              <h2>{result.message || "Analysis complete"}</h2>
            </div>
            <span className={`status ${result.status}`}>{result.status}</span>
          </div>

          {result.result && (
            <article className="provision-card">
              <div className="icon"><BookOpen size={20} /></div>
              <div>
                <p className="label">{result.result.act}</p>
                <h3>Section {result.result.section}</h3>
                <p>{result.result.title}</p>
                <blockquote>{result.result.text}</blockquote>
              </div>
            </article>
          )}

          <div className="disclaimer">
            <AlertTriangle size={17} />
            Nyayalay provides legal information, not legal advice. Verify important
            matters with an official legal source or qualified legal professional.
          </div>
        </section>
      )}
    </main>
  );
}
