import { useState } from "react";
import { login, me } from "../api/client";

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("underwriter@demo.com");
  const [password, setPassword] = useState("Demo@1234");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const { access_token } = await login(email, password);
      localStorage.setItem("token", access_token);
      onLogin(await me());
    } catch (err) {
      setError(err.message || "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={handleSubmit}>
        <div className="brand-mark lg">UW</div>
        <h1>Insurance Underwriting AI</h1>
        <p className="muted">Rules + Gemini assist. You decide.</p>
        {error && <div className="alert">{error}</div>}
        <label>Work email
          <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
        </label>
        <label>Password
          <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required />
        </label>
        <button className="btn primary" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
        <p className="hint">Demo: underwriter@demo.com / Demo@1234</p>
      </form>
    </div>
  );
}

