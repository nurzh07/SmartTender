import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { forgotPassword } from "../api";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [resetLink, setResetLink] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!resetLink) return;
    await navigator.clipboard.writeText(resetLink);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setSubmitting(true);

    try {
      const res = await forgotPassword(email);
      setResetLink(res.reset_link || "");
      setSuccess(
        res.reset_link
          ? `${res.message}`
          : res.message || "Құпия сөзді қалпына келтіру сілтемесі жіберілді."
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Сілтеме жіберу мүмкін болмады");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="login-page">
      <div className="card login-card">
        <h1>SmartTender</h1>
        {!success ? (
          <>
            <p style={{ color: "var(--muted)" }}>Құпия сөзді қалпына келтіру үшін email-ыңызды енгізіңіз</p>
            <form className="form-stack" onSubmit={handleSubmit}>
              <div>
                <label className="label">Email</label>
                <input
                  className="input"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              {error && <p className="error-msg">{error}</p>}
              <button type="submit" className="btn btn-primary" disabled={submitting}>
                {submitting ? "Сілтеме жіберуде..." : "Сілтемені жіберу"}
              </button>
            </form>
          </>
        ) : (
          <div style={{ textAlign: "left" }}>
            <div
              style={{
                padding: "1rem",
                borderRadius: "12px",
                background: "rgba(34, 197, 94, 0.12)",
                color: "var(--success)",
                border: "1px solid rgba(34, 197, 94, 0.25)",
              }}
            >
              <h2 style={{ margin: "0 0 0.4rem", fontSize: "1.1rem" }}>Поштаңызды тексеріңіз</h2>
              <p style={{ margin: 0, fontWeight: 600 }}>{success}</p>
              <p style={{ margin: "0.45rem 0 0", color: "var(--muted)" }}>
                Егер бұл локальді режим болса, төмендегі сілтемені тікелей пайдалана аласыз.
              </p>
              {resetLink && (
                <>
                  <a
                    href={resetLink}
                    target="_blank"
                    rel="noreferrer"
                    style={{ display: "inline-block", marginTop: "0.6rem", color: "var(--primary)" }}
                  >
                    {resetLink}
                  </a>
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={handleCopy}
                    style={{ marginTop: "0.75rem", padding: "0.55rem 0.9rem" }}
                  >
                    {copied ? "Көшірілді" : "Сілтемені көшіру"}
                  </button>
                </>
              )}
            </div>
          </div>
        )}
        <div style={{ marginTop: "1rem", textAlign: "center" }}>
          <Link to="/login" style={{ color: "var(--primary)", textDecoration: "none" }}>
            Кіруге оралу
          </Link>
        </div>
      </div>
    </div>
  );
}
