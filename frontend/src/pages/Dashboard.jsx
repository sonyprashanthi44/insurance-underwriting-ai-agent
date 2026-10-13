import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getStats, listApplications } from "../api/client";

const badge = (v) => `badge ${String(v || "").toLowerCase()}`;

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [rows, setRows] = useState([]);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  async function load(s = status) {
    try {
      const params = s ? { status: s } : {};
      const [st, list] = await Promise.all([getStats(), listApplications(params)]);
      setStats(st);
      setRows(list);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => { load(); }, []);

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Underwriting queue</h1>
          <p className="muted">Review AI risk scores, explanations, and record final decisions.</p>
        </div>
        <Link className="btn primary" to="/applications/new">+ New application</Link>
      </header>

      {error && <div className="alert">{error}</div>}

      {stats && (
        <div className="stat-grid">
          <div className="stat"><span>Total</span><strong>{stats.total}</strong></div>
          <div className="stat"><span>Pending</span><strong>{stats.pending}</strong></div>
          <div className="stat"><span>Approved</span><strong>{stats.approved}</strong></div>
          <div className="stat"><span>Referred</span><strong>{stats.referred}</strong></div>
          <div className="stat"><span>Declined</span><strong>{stats.declined}</strong></div>
          <div className="stat"><span>Avg risk</span><strong>{stats.avg_risk_score}</strong></div>
        </div>
      )}

      <div className="toolbar">
        <select value={status} onChange={(e) => { setStatus(e.target.value); load(e.target.value); }}>
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="referred">Referred</option>
          <option value="declined">Declined</option>
        </select>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Application</th>
              <th>Applicant</th>
              <th>Product</th>
              <th>Coverage</th>
              <th>AI rec</th>
              <th>Risk</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td><Link to={`/applications/${r.id}`}>{r.application_number}</Link></td>
                <td>{r.applicant_name}</td>
                <td className="cap">{r.product_line}</td>
                <td>${Number(r.coverage_amount).toLocaleString()}</td>
                <td><span className={badge(r.ai_recommendation)}>{r.ai_recommendation}</span></td>
                <td><span className="mono">{r.ai_risk_score}</span></td>
                <td><span className={badge(r.status)}>{r.status}</span></td>
              </tr>
            ))}
            {!rows.length && <tr><td colSpan="7" className="muted">No applications in this view.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
