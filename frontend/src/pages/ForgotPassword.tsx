import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { forgotPassword } from "../api/auth";

export function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [resetToken, setResetToken] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setMessage("");
    setResetToken(null);
    setLoading(true);
    try {
      const res = await forgotPassword(email.trim());
      setMessage(res.message);
      setResetToken(res.reset_token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to request reset token");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-header">
          <span className="auth-logo">◈</span>
          <h1>Reset Password</h1>
          <p>Generate a reset token for your account.</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {error && <div className="form-error">{error}</div>}
          {message && <div className="save-status saved">{message}</div>}

          <div className="field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              autoComplete="email"
              required
            />
          </div>

          <button type="submit" className="btn-primary" disabled={loading || !email.trim()}>
            {loading ? "Generating..." : "Generate reset token"}
          </button>
        </form>

        {resetToken && (
          <div className="inline-confirm" style={{ marginTop: 14, display: "block" }}>
            <p style={{ marginBottom: 6 }}>Use this token on the reset page:</p>
            <code style={{ wordBreak: "break-all" }}>{resetToken}</code>
          </div>
        )}

        <p className="auth-footer">
          Back to <Link to="/login">Sign in</Link> · Continue to <Link to="/reset-password">Reset page</Link>
        </p>
      </div>
    </div>
  );
}

