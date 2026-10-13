import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createApplication } from "../api/client";

const empty = {
  applicant_name: "",
  applicant_age: 35,
  occupation: "",
  product_line: "auto",
  coverage_amount: 50000,
  annual_income: 80000,
  credit_score: 700,
  prior_claims: 0,
  risk_factors: "",
  property_zip: "",
};

export default function NewApplication() {
  const [form, setForm] = useState(empty);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  function set(key, value) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const payload = {
        ...form,
        applicant_age: Number(form.applicant_age),
        coverage_amount: Number(form.coverage_amount),
        annual_income: Number(form.annual_income),
        credit_score: Number(form.credit_score),
        prior_claims: Number(form.prior_claims),
      };
      const created = await createApplication(payload);
      navigate(`/applications/${created.id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>New policy application</h1>
          <p className="muted">Capture intake data — AI scores risk on submit.</p>
        </div>
      </header>
      {error && <div className="alert">{error}</div>}
      <form className="card form-grid" onSubmit={submit}>
        <label>Applicant name<input required value={form.applicant_name} onChange={(e) => set("applicant_name", e.target.value)} /></label>
        <label>Age<input type="number" min="18" max="100" required value={form.applicant_age} onChange={(e) => set("applicant_age", e.target.value)} /></label>
        <label>Occupation<input required value={form.occupation} onChange={(e) => set("occupation", e.target.value)} /></label>
        <label>Product line
          <select value={form.product_line} onChange={(e) => set("product_line", e.target.value)}>
            <option value="auto">Auto</option>
            <option value="home">Home</option>
            <option value="life">Life</option>
            <option value="commercial">Commercial</option>
          </select>
        </label>
        <label>Coverage amount<input type="number" min="1" required value={form.coverage_amount} onChange={(e) => set("coverage_amount", e.target.value)} /></label>
        <label>Annual income<input type="number" min="0" required value={form.annual_income} onChange={(e) => set("annual_income", e.target.value)} /></label>
        <label>Credit score<input type="number" min="300" max="850" required value={form.credit_score} onChange={(e) => set("credit_score", e.target.value)} /></label>
        <label>Prior claims<input type="number" min="0" required value={form.prior_claims} onChange={(e) => set("prior_claims", e.target.value)} /></label>
        <label>Property ZIP<input value={form.property_zip} onChange={(e) => set("property_zip", e.target.value)} /></label>
        <label className="full">Risk factors (comma-separated)
          <input placeholder="e.g. smoking, flood zone, DUI" value={form.risk_factors} onChange={(e) => set("risk_factors", e.target.value)} />
        </label>
        <div className="full btn-row">
          <button className="btn primary" disabled={busy}>{busy ? "Scoring…" : "Submit & score"}</button>
        </div>
      </form>
    </div>
  );
}
