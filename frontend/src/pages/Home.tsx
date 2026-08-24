import { useState, useEffect } from "react";
import { analyzeIncident } from "../services/api";
import type { AnalysisResponse } from "../types/analysis";

const LOADING_MESSAGES = [
  "Understanding the incident...",
  "Analyzing the facts...",
  "Searching relevant legal provisions...",
  "Finalizing analysis..."
];

/**
 * Split a block of text into bullet-point sentences.
 * Handles period-separated sentences, semicolons, and numbered lists.
 */
function textToBullets(text: string): string[] {
  if (!text || !text.trim()) return [];

  // Split on sentence endings (. or ; followed by space/end), or numbered items
  const parts = text
    .split(/(?<=[.;])\s+|(?=\d+\.\s)/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0);

  // If splitting produced only 1 item, try splitting on commas with conjunctions
  if (parts.length <= 1) {
    const commaParts = text
      .split(/,\s*(?:and|or|also|additionally|furthermore|moreover)\s+/i)
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
    if (commaParts.length > 1) return commaParts;
  }

  return parts.length > 0 ? parts : [text];
}

/** Render a confidence percentage as a visual bar */
function ConfidenceBar({ value, label }: { value: number; label: string }) {
  const pct = Math.round(value * 100);
  const level = pct >= 75 ? "high" : pct >= 45 ? "medium" : "low";

  return (
    <div className="confidence-bar-container">
      <span className="confidence-label">{label}</span>
      <div className="confidence-track">
        <div
          className={`confidence-fill ${level}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="confidence-value">{pct}%</span>
    </div>
  );
}

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

  /** Render the Key Facts grid from extracted facts */
  const renderKeyFacts = () => {
    if (!result?.facts) return null;

    const facts = result.facts;
    const rows: { label: string; value: React.ReactNode }[] = [];

    // Parties
    if (facts.victim) rows.push({ label: "Victim / Complainant", value: facts.victim });
    if (facts.accused) rows.push({ label: "Accused / Other Party", value: facts.accused });
    if (facts.relationship_between_parties) rows.push({ label: "Relationship", value: facts.relationship_between_parties });

    // Context
    if (facts.location) rows.push({ label: "Location", value: facts.location });
    if (facts.time_or_date) rows.push({ label: "Time / Date", value: facts.time_or_date });
    if (facts.intent) rows.push({ label: "Alleged Intent", value: facts.intent });

    // Financial
    if (facts.money_amount) rows.push({ label: "Amount Involved", value: facts.money_amount });

    // Array fields as tag chips
    if (facts.alleged_conduct && facts.alleged_conduct.length > 0) {
      rows.push({
        label: "Alleged Conduct",
        value: (
          <div className="array-tags">
            {facts.alleged_conduct.map((c, i) => (
              <span key={i} className="array-tag">{c}</span>
            ))}
          </div>
        ),
      });
    }

    if (facts.harm && facts.harm.length > 0) {
      rows.push({
        label: "Harm Caused",
        value: (
          <div className="array-tags">
            {facts.harm.map((h, i) => (
              <span key={i} className="array-tag">{h}</span>
            ))}
          </div>
        ),
      });
    }

    if (facts.injuries && facts.injuries.length > 0) {
      rows.push({
        label: "Injuries",
        value: (
          <div className="array-tags">
            {facts.injuries.map((inj, i) => (
              <span key={i} className="array-tag">{inj}</span>
            ))}
          </div>
        ),
      });
    }

    if (facts.weapons_or_tools && facts.weapons_or_tools.length > 0) {
      rows.push({
        label: "Weapons / Tools",
        value: (
          <div className="array-tags">
            {facts.weapons_or_tools.map((w, i) => (
              <span key={i} className="array-tag">{w}</span>
            ))}
          </div>
        ),
      });
    }

    if (facts.property_items && facts.property_items.length > 0) {
      rows.push({
        label: "Property Items",
        value: (
          <div className="array-tags">
            {facts.property_items.map((p, i) => (
              <span key={i} className="array-tag">{p}</span>
            ))}
          </div>
        ),
      });
    }

    if (facts.evidence && facts.evidence.length > 0) {
      rows.push({
        label: "Available Evidence",
        value: (
          <div className="array-tags">
            {facts.evidence.map((e, i) => (
              <span key={i} className="array-tag">{e}</span>
            ))}
          </div>
        ),
      });
    }

    if (rows.length === 0) return null;

    return (
      <>
        <h4 className="sub-section-heading">Key Facts Identified</h4>
        <div className="facts-grid">
          {rows.map((row, i) => (
            <div key={i} className="fact-row">
              <span className="fact-label">{row.label}</span>
              <span className="fact-value">{row.value}</span>
            </div>
          ))}
        </div>
      </>
    );
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
          showProvision: true
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
          showProvision: true
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

                    {/* ── Incident Summary (bulleted) ── */}
                    {result.facts?.summary && (
                      <div className="summary-box">
                        <h2 className="section-heading">Incident Summary</h2>
                        {(() => {
                          const bullets = textToBullets(result.facts.summary);
                          return bullets.length > 1 ? (
                            <ul className="bullet-list">
                              {bullets.map((b, i) => (
                                <li key={i}>{b}</li>
                              ))}
                            </ul>
                          ) : (
                            <p className="section-text">{result.facts.summary}</p>
                          );
                        })()}
                        <div className="facts-container">
                          {renderFactTags()}
                        </div>

                        {/* Key Facts Grid */}
                        {renderKeyFacts()}
                      </div>
                    )}

                    {/* ── Legal Provision ── */}
                    {statusDisplay?.showProvision && result.result && (
                      <div className="legal-provision">
                        <div className="provision-header">
                          <div className="provision-act">{result.result.act} — Section {result.result.section}</div>
                          <div className="provision-title">{result.result.title}</div>
                        </div>
                        
                        <div className={`provision-text ${!isExpanded ? 'collapsed' : ''}`}>
                          {(() => {
                            const rawText = result.result.text;
                            if (!rawText) return null;
                            
                            let text = rawText;
                            const textMatch = rawText.match(/Text:\s*(.*)/is);
                            if (textMatch) {
                              text = textMatch[1];
                            }

                            const introSplit = text.split('—');
                            if (introSplit.length > 1) {
                              const intro = introSplit[0] + '—';
                              const pointsText = introSplit.slice(1).join('—');
                              const points = pointsText.split(/(?=\s*\([a-z0-9]+\)\s)/i).filter(p => p.trim());
                              
                              return (
                                <div className="formatted-provision">
                                  <p className="provision-intro">{intro.trim()}</p>
                                  <ul className="provision-list">
                                    {points.map((point, i) => (
                                      <li key={i}>{point.trim()}</li>
                                    ))}
                                  </ul>
                                </div>
                              );
                            }
                            
                            const points = text.split(/(?=\s*\([a-z0-9]+\)\s)/i).filter(p => p.trim());
                            if (points.length > 1) {
                              return (
                                <div className="formatted-provision">
                                  <p className="provision-intro">{points[0].trim()}</p>
                                  <ul className="provision-list">
                                    {points.slice(1).map((point, i) => (
                                      <li key={i}>{point.trim()}</li>
                                    ))}
                                  </ul>
                                </div>
                              );
                            }

                            return <p>{text}</p>;
                          })()}
                        </div>
                        
                        <button 
                          className="expand-btn" 
                          onClick={() => setIsExpanded(!isExpanded)}
                        >
                          {isExpanded ? "Hide Full Text" : "Read Full Provision"}
                        </button>
                      </div>
                    )}

                    {/* ── Why Was This Selected? (bulleted explanation + missing info) ── */}
                    {statusDisplay?.showProvision && result.classification && (
                      <div className="verification-box">
                        <h2 className="section-heading">Why was this selected?</h2>

                        {/* Explanation as bullet points */}
                        {result.classification.explanation && (() => {
                          const intro = result.classification.section
                            ? `Based on your description, this situation aligns with ${result.classification.section}.`
                            : null;
                          const bullets = textToBullets(result.classification.explanation);

                          return (
                            <>
                              {intro && <p className="section-text" style={{ marginBottom: '12px' }}><strong>{intro}</strong></p>}
                              {bullets.length > 1 ? (
                                <ul className="bullet-list">
                                  {bullets.map((b, i) => (
                                    <li key={i}>{b}</li>
                                  ))}
                                </ul>
                              ) : (
                                <p className="section-text">{result.classification.explanation}</p>
                              )}
                            </>
                          );
                        })()}

                        {/* Confidence bar */}
                        <ConfidenceBar
                          value={result.classification.confidence}
                          label="Analysis Confidence"
                        />

                        {/* Missing information from classification */}
                        {result.classification.missing_information && result.classification.missing_information.length > 0 && (
                          <>
                            <h4 className="sub-section-heading">Additional information that could strengthen this analysis</h4>
                            <ul className="evidence-list">
                              {result.classification.missing_information.map((info, i) => (
                                <li key={i} className="missing-item">{info}</li>
                              ))}
                            </ul>
                          </>
                        )}
                      </div>
                    )}

                    {/* ── Verification Status (structured with evidence/contradictions) ── */}
                    {statusDisplay?.showProvision && result.verification && (
                      <div className="verification-box">
                        <h2 className="section-heading">Verification Status</h2>

                        {/* Reasoning as bullet points */}
                        <p className="section-text" style={{ marginBottom: '8px' }}>
                          <strong>{result.verification.supported ? "Supported by facts:" : "Could not be fully verified:"}</strong>
                        </p>
                        {(() => {
                          const bullets = textToBullets(result.verification.reasoning);
                          return bullets.length > 1 ? (
                            <ul className="bullet-list">
                              {bullets.map((b, i) => (
                                <li key={i}>{b}</li>
                              ))}
                            </ul>
                          ) : (
                            <p className="section-text">{result.verification.reasoning}</p>
                          );
                        })()}

                        {/* Evidence Support */}
                        {result.verification.evidence_support && result.verification.evidence_support.length > 0 && (
                          <>
                            <h4 className="sub-section-heading">Supporting Evidence</h4>
                            <ul className="evidence-list">
                              {result.verification.evidence_support.map((e, i) => (
                                <li key={i} className="evidence-item">{e}</li>
                              ))}
                            </ul>
                          </>
                        )}

                        {/* Contradictions */}
                        {result.verification.contradictions && result.verification.contradictions.length > 0 && (
                          <>
                            <h4 className="sub-section-heading">Points of Concern</h4>
                            <ul className="evidence-list">
                              {result.verification.contradictions.map((c, i) => (
                                <li key={i} className="contradiction-item">{c}</li>
                              ))}
                            </ul>
                          </>
                        )}

                        {/* Missing Facts */}
                        {result.verification.missing_facts && result.verification.missing_facts.length > 0 && (
                          <>
                            <h4 className="sub-section-heading">Facts Not Yet Confirmed</h4>
                            <ul className="evidence-list">
                              {result.verification.missing_facts.map((f, i) => (
                                <li key={i} className="missing-item">{f}</li>
                              ))}
                            </ul>
                          </>
                        )}

                        {/* Verification confidence bar */}
                        <ConfidenceBar
                          value={result.verification.confidence}
                          label="Verification Confidence"
                        />
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