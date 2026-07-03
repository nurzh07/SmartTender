import { FormEvent, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function RegisterPage() {
  const { user, loading, register } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState<"buyer" | "supplier">("buyer");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  if (!loading && user) return <Navigate to="/" replace />;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await register(email, password, fullName, role);
      setSuccess(true);
      setTimeout(() => navigate("/login"), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Тіркелу сәтсіз");
    } finally {
      setSubmitting(false);
    }
  };

  if (success) {
    return (
      <div className="login-page">
        <div className="card login-card">
          <h1>SmartTender</h1>
          <p style={{ color: "var(--success)", textAlign: "center" }}>
            Тіркелу сәтті аяқталды!
          </p>
          <p style={{ color: "var(--muted)", textAlign: "center" }}>
            Email-ге растау сілтемесі жіберілді. 3 секундтан кейін кіру бетіне бағытталасыз...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="login-page">
      <div className="card login-card">
        <h1>SmartTender</h1>
        <p style={{ color: "var(--muted)" }}>Тіркелу</p>
        <form className="form-stack" onSubmit={handleSubmit}>
          <div>
            <label className="label">Аты-жөні</label>
            <input
              className="input"
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
            />
          </div>
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
          <div>
            <label className="label">Пароль</label>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
            />
          </div>
          <div>
            <label className="label">Рөл</label>
            <select
              className="input"
              value={role}
              onChange={(e) => setRole(e.target.value as "buyer" | "supplier")}
              required
            >
              <option value="buyer">BUYER (Сатып алушы)</option>
              <option value="supplier">SUPPLIERжеткізуші)</option>
            </select>
          </div>
          {error && <p className="error-msg">{error}</p>}
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? "Тіркелуде..." : "Тіркелу"}
          </button>
        </form>
        <div style={{ marginTop: "1rem", textAlign: "center", fontSize: "0.9rem", color: "var(--muted)" }}>
          Тіркелгеннен кейін email-ге растау сілтемесі жіберіледі.
        </div>
      </div>
    </div>
  );
}
