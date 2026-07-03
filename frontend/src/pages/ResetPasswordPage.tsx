import { FormEvent, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { resetPassword } from "../api";

function getPasswordStrength(password: string) {
  if (!password) return { label: "", score: 0 };
  const checks = [/.{8,}/, /[A-Z]/, /[a-z]/, /\d/, /[^A-Za-z0-9]/];
  const passed = checks.filter((check) => check.test(password)).length;
  if (passed <= 2) return { label: "Әлсіз", score: 1 };
  if (passed === 3 || passed === 4) return { label: "Орташа", score: 2 };
  return { label: "Күшті", score: 3 };
}

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = useMemo(() => searchParams.get("token") || "", [searchParams]);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const strength = getPasswordStrength(password);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (password.length < 8) {
      setError("Құпия сөз кемінде 8 таңбадан тұруы керек");
      return;
    }
    if (strength.score < 2) {
      setError("Құпия сөзді күштірек жасаңыз: үлкен әріп, сан және арнайы таңба қосыңыз");
      return;
    }
    if (password !== confirmPassword) {
      setError("Құпия сөздер бірдей емес");
      return;
    }

    setSubmitting(true);
    try {
      await resetPassword(token, password);
      setSuccess("Құпия сөз сәтті өзгертілді. Кіру бетіне бағытталасыз...");
      setTimeout(() => navigate("/login"), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Құпия сөзді өзгерту мүмкін болмады");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="login-page">
      <div className="card login-card">
        <h1>SmartTender</h1>
        <p style={{ color: "var(--muted)" }}>Жаңа құпия сөз қойыңыз</p>
        <form className="form-stack" onSubmit={handleSubmit}>
          <div>
            <label className="label">Жаңа құпия сөз</label>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            {password && (
              <div style={{ marginTop: "0.35rem", fontSize: "0.85rem", color: strength.score >= 3 ? "var(--success)" : strength.score === 2 ? "var(--warning)" : "var(--danger)" }}>
                Құпия сөздің беріктігі: {strength.label}
              </div>
            )}
          </div>
          <div>
            <label className="label">Құпия сөзді қайталаңыз</label>
            <input
              className="input"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>
          {error && <p className="error-msg">{error}</p>}
          {success && <p style={{ color: "var(--success)" }}>{success}</p>}
          <button type="submit" className="btn btn-primary" disabled={submitting || !token}>
            {submitting ? "Жаңартылуда..." : "Құпия сөзді сақтау"}
          </button>
        </form>
        <div style={{ marginTop: "1rem", textAlign: "center" }}>
          <Link to="/login" style={{ color: "var(--primary)", textDecoration: "none" }}>
            Кіруге оралу
          </Link>
        </div>
      </div>
    </div>
  );
}
