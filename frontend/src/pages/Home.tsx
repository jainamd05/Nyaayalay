import { useState, useEffect } from "react";
import { analyzeIncident } from "../services/api";
import type { AnalysisResponse } from "../types/analysis";

const LOADING_MESSAGES = [
  "Understanding the incident...",
  "Analyzing the facts...",
  "Searching relevant legal provisions...",
  "Finalizing analysis..."
];

export default function Home() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [error, setError] = useState("");
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    let interval: number;
    if (loading) {
      setLoadingStep(0);
      interval = window.setInterval(() => {
        setLoadingStep((prev) => (prev + 1) % LOADING_MESSAGES.length);
      }, 2500);
    }
    return () => clearInterval(interval);
  }, [loading]);

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
      setIsExpanded(false);

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

  const renderFactTags = () => {
    if (!result?.facts) return null;
    const tags = [];
    if (result.facts.event_type) tags.push(result.facts.event_type);
    if (result.facts.property_or_money) tags.push("Property Involved");
    if (result.facts.violence_or_threat) tags.push("Violence/Threat");
    if (result.facts.deception_or_fraud) tags.push("Deception/Fraud");
    if (result.facts.digital_element) tags.push("Digital Element");
    
    return tags.map((t, i) => (
      <span key={i} className="fact-tag highlight">{t}</span>
    ));
  };

  const getStatusDisplay = () => {
    if (!result) return null;
    switch (result.status) {
      case 'ok':
        return {
          indicator: '',
          badge: 'Analysis Complete',
          title: 'Relevant Legal Provision Identified',
          message: result.message || 'A potentially relevant legal provision has been identified based on your description.',
          isSuccess: true,
          showProvision: true
        };
      case 'low_confidence':
        return {
          indicator: 'warning',
          badge: 'Analysis Requires Review',
          title: 'Analysis Requires Review',
          message: 'More information may be needed before a legal provision can be confidently identified.',
          isSuccess: false,
          showProvision: false
        };
      case 'no_evidence':
        return {
          indicator: 'warning',
          badge: 'No Relevant Provision Found',
          title: 'No Relevant Provision Found',
          message: result.message || 'We could not identify a relevant legal provision based on the provided details.',
          isSuccess: false,
          showProvision: false
        };
      case 'unsupported':
        return {
          indicator: 'warning',
          badge: 'Incident Not Supported',
          title: 'Incident Not Supported',
          message: 'This incident could not currently be safely mapped to a supported legal domain.',
          isSuccess: false,
          showProvision: false
        };
      case 'verification_failed':
        return {
          indicator: 'warning',
          badge: 'Analysis Could Not Be Confirmed',
          title: 'Analysis Could Not Be Confirmed',
          message: 'A potentially relevant provision was found but could not be sufficiently verified from the available information.',
          isSuccess: false,
          showProvision: false
        };
      default:
        return {
          indicator: 'warning',
          badge: 'Analysis Requires Review',
          title: 'Analysis Requires Review',
          message: result.message || 'Please review the analysis.',
          isSuccess: false,
          showProvision: false
        };
    }
  };

  return (
    <>
      <nav className="navbar">
        <a href="/" className="nav-logo">Nyayalay</a>
        <div className="nav-links">
          <a href="#">Home</a>
          <a href="#">How It Works</a>
          <a href="#">About</a>
        </div>
      </nav>

      <main className="home-page">
        <section className="hero">
          <h1>Understand your legal situation, clearly.</h1>
          <p className="hero-description">
            Describe what happened in simple language, and Nyayalay will identify potentially relevant legal provisions from the supported Indian legal corpus.
          </p>

          <form className="query-form" onSubmit={handleSubmit}>
            <textarea
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Describe what happened. Include what occurred, who was involved, and any important details you remember."
              rows={6}
            />

            <button type="submit" disabled={loading}>
              Analyze Incident
            </button>
          </form>

          {error && <p className="error-message">{error}</p>}
        </section>

        {loading && (
          <div className="loading-container">
            <div className="spinner"></div>
            <div className="loading-text">{LOADING_MESSAGES[loadingStep]}</div>
          </div>
        )}

        {result && !loading && (
          <section className="result-section">
            <div className="result-card">
              
              {(() => {
                const statusDisplay = getStatusDisplay();
                return (
                  <>
                    <div className="result-header">
                      <div className="status-badge">
                        <div className={`status-indicator ${statusDisplay?.indicator}`}></div>
                        {statusDisplay?.badge}
                      </div>
                      
                      {result.route?.domain && (
                        <div className="domain-tag">
                          {result.route.domain} Domain
                        </div>
                      )}
                    </div>

                    {!statusDisplay?.isSuccess && (
                      <div className="analysis-warning">
                        <h3>{statusDisplay?.title}</h3>
                        <p>{statusDisplay?.message}</p>
                        {result.status === 'low_confidence' && (
                          <button 
                            onClick={() => {
                              window.scrollTo({ top: 0, behavior: 'smooth' });
                              document.querySelector('textarea')?.focus();
                            }}
                            style={{
                              marginTop: '20px',
                              padding: '12px 24px',
                              background: 'transparent',
                              border: '2px solid var(--color-primary)',
                              color: 'var(--color-primary)',
                              borderRadius: '8px',
                              cursor: 'pointer',
                              fontWeight: '600',
                              fontSize: '0.95rem',
                              transition: 'all 0.2s ease'
                            }}
                            onMouseOver={(e) => {
                              e.currentTarget.style.background = 'var(--color-primary)';
                              e.currentTarget.style.color = '#fff';
                            }}
                            onMouseOut={(e) => {
                              e.currentTarget.style.background = 'transparent';
                              e.currentTarget.style.color = 'var(--color-primary)';
                            }}
                          >
                            Add More Details
                          </button>
                        )}
                      </div>
                    )}

                    {statusDisplay?.isSuccess && (
                      <div className="analysis-success">
                        <h3>{statusDisplay?.title}</h3>
                        <p>{statusDisplay?.message}</p>
                      </div>
                    )}

                    {result.facts?.summary && (
                      <div className="summary-box">
                        <h2 className="section-heading">Incident Summary</h2>
                        <p className="section-text">{result.facts.summary}</p>
                        <div className="facts-container">
                          {renderFactTags()}
                        </div>
                      </div>
                    )}

                    {statusDisplay?.showProvision && result.result && (
                      <div className="legal-provision">
                        <div className="provision-header">
                          <div className="provision-act">{result.result.act} — Section {result.result.section}</div>
                          <div className="provision-title">{result.result.title}</div>
                        </div>
                        
                        <div className={`provision-text ${!isExpanded ? 'collapsed' : ''}`}>
                          {result.result.text}
                        </div>
                        
                        <button 
                          className="expand-btn" 
                          onClick={() => setIsExpanded(!isExpanded)}
                        >
                          {isExpanded ? "Hide Full Text" : "Read Full Provision"}
                        </button>
                      </div>
                    )}

                    {statusDisplay?.showProvision && result.classification && (
                      <div className="verification-box">
                        <h2 className="section-heading">Why was this selected?</h2>
                        <p className="section-text">
                          Based on your description, this situation aligns with <strong>{result.classification.section || "the identified laws"}</strong>. 
                          {result.classification.explanation}
                        </p>
                        <p className="section-text" style={{marginTop: '12px', fontSize: '0.9rem', color: 'var(--color-text-muted)'}}>
                          Analysis Confidence: {Math.round(result.classification.confidence * 100)}%
                        </p>
                      </div>
                    )}

                    {statusDisplay?.showProvision && result.verification && (
                      <div className="verification-box">
                        <h2 className="section-heading">Verification Status</h2>
                        <p className="section-text">
                          <strong>{result.verification.supported ? "Supported by facts:" : "Could not be fully verified:"}</strong> {result.verification.reasoning}
                        </p>
                      </div>
                    )}
                  </>
                );
              })()}

              {result.facts?.missing_or_uncertain_facts && result.facts.missing_or_uncertain_facts.length > 0 && (
                <div className="verification-box">
                  <h2 className="section-heading">Information That May Be Important</h2>
                  <p className="section-text" style={{marginBottom: '16px'}}>
                    Providing additional details about these points may affect which legal provisions are considered relevant:
                  </p>
                  <ul className="checklist">
                    {result.facts.missing_or_uncertain_facts.map((fact, index) => (
                      <li key={index}>{fact}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="disclaimer">
                <strong>Important Notice:</strong> Nyayalay provides legal information and AI-assisted analysis based on the information provided. This does not constitute legal advice and should not replace consultation with a qualified legal professional.
              </div>
            </div>
          </section>
        )}
      </main>
    </>
  );
}