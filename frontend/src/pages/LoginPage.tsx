import { FormEvent, useState } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function LoginPage() {
  const { user, loading, login } = useAuth();
  const [email, setEmail] = useState("manager@smarttender.kz");
  const [password, setPassword] = useState("manager123");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (!loading && user) return <Navigate to="/" replace />;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Кіру сәтсіз");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="login-page">
      <div className="card login-card">
        <h1>SmartTender</h1>
        <p style={{ color: "var(--muted)" }}>Корпоративтік тендерлер платформасы</p>
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
          <div>
            <label className="label">Пароль</label>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          {error && <p className="error-msg">{error}</p>}
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? "Кіру..." : "Кіру"}
          </button>
        </form>
        <div className="demo-hint">
          <strong>Демо аккаунттар:</strong>
          <br />
          <code>manager@smarttender.kz</code> / manager123
          <br />
          <code>employee@smarttender.kz</code> / employee123
          <br />
          <code>supplier@smarttender.kz</code> / supplier123
        </div>
      </div>
    </div>
  );
}
