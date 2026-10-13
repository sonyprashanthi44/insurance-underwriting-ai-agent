import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { decideApplication, getApplication, rescoreApplication } from "../api/client";

export default function ApplicationDetail() {
  const { id } = useParams();
  const [app, setApp] = useState(null);
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      const data = await getApplication(id);
      setApp(data);
      setNotes(data.underwriter_notes || "");
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => { load(); }, [id]);

  async function decide(final_decision) {
    setBusy(true);
    setError("");
    try {
      setApp(await decideApplication(id, { final_decision, underwriter_notes: notes }));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function rescore() {
    setBusy(true);
    try {
      setApp(await rescoreApplication(id));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (!app && !error) return <div className="page">Loading application…</div>;
  if (!app) return <div className="page alert">{error}</div>;

  return (
    <div className="page">
      <Link className="back" to="/">← Back to queue</Link>
      <header className="page-header">
        <div>
          <h1>{app.application_number}</h1>
          <p className="muted">{app.applicant_name} · {app.product_line} · status: {app.status}</p>
        </div>
        <button className="btn ghost" disabled={busy} onClick={rescore}>Re-run AI score</button>
      </header>
      {error && <div className="alert">{error}</div>}

      <div className="detail-grid">
        <section className="card">
          <h2>Applicant & risk inputs</h2>
          <dl className="kv">
            <div><dt>Age</dt><dd>{app.applicant_age}</dd></div>
            <div><dt>Occupation</dt><dd>{app.occupation}</dd></div>
            <div><dt>Coverage</dt><dd>${Number(app.coverage_amount).toLocaleString()}</dd></div>
            <div><dt>Income</dt><dd>${Number(app.annual_income).toLocaleString()}</dd></div>
            <div><dt>Credit score</dt><dd>{app.credit_score}</dd></div>
            <div><dt>Prior claims</dt><dd>{app.prior_claims}</dd></div>
            <div><dt>ZIP</dt><dd>{app.property_zip || "—"}</dd></div>
            <div><dt>Risk factors</dt><dd>{app.risk_factors || "None listed"}</dd></div>
          </dl>
        </section>

        <section className="card ai-card">
          <h2>AI recommendation</h2>
          <div className="ai-metrics">
            <div>
              <span className="label">Recommendation</span>
              <div className={`badge lg ${app.ai_recommendation}`}>{app.ai_recommendation}</div>
            </div>
            <div>
              <span className="label">Risk score</span>
              <div className="score">{app.ai_risk_score}<small>/100</small></div>
            </div>
            <div>
              <span className="label">Indicative premium</span>
              <div className="score">${Number(app.ai_suggested_premium).toLocaleString()}</div>
            </div>
          </div>
          <p className="explanation">{app.ai_explanation}</p>
          <p className="hint">Advisory only — final underwriting authority stays with the human reviewer.</p>
        </section>

        <section className="card">
          <h2>Underwriter decision</h2>
          <label>Notes
            <textarea rows={5} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Document rationale, referrals, or conditions…" />
          </label>
          <div className="btn-row">
            <button className="btn success" disabled={busy} onClick={() => decide("approved")}>Approve</button>
            <button className="btn warn" disabled={busy} onClick={() => decide("referred")}>Refer</button>
<button className="btn danger" disabled={busy} onClick={() => decide("declined")}>Decline</button>
          </div>
          {app.final_decision && (
            <p className="muted">Recorded decision: <strong>{app.final_decision}</strong></p>
          )}
        </section>
      </div>
    </div>
  );
}
