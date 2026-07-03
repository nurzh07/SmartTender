import { FormEvent, useState } from "react";
import { Navigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function LoginPage() {
  const { user, loading, login } = useAuth();
  const [email, setEmail] = useState("employee@smarttender.kz");
  const [password, setPassword] = useState("employee123");
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
      <div className="card login-card" style={{
        background: "linear-gradient(135deg, var(--surface) 0%, var(--surface2) 100%)",
        border: "1px solid var(--border)",
        boxShadow: "var(--shadow-lg)"
      }}>
        <div style={{ textAlign: "center", marginBottom: "1.5rem" }}>
          <h1 style={{ 
            fontSize: "2rem", 
            fontWeight: 800, 
            marginBottom: "0.5rem",
            letterSpacing: "-0.02em"
          }}>
            Smart<span style={{ color: "var(--accent)" }}>Tender</span>
          </h1>
          <p style={{ 
            color: "var(--text-secondary)", 
            fontSize: "0.95rem",
            marginTop: "0.5rem"
          }}>
            🏛️ Корпоративтік тендерлер платформасы
          </p>
        </div>
        <form className="form-stack" onSubmit={handleSubmit}>
          <div>
            <label className="label" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              📧 Email
            </label>
            <input
              className="input"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="email@example.com"
            />
          </div>
          <div>
            <label className="label" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              🔒 Пароль
            </label>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="••••••••"
            />
          </div>
          {error && (
            <div style={{
              background: "var(--danger-light)",
              border: "1px solid var(--danger)",
              borderRadius: "var(--radius)",
              padding: "0.75rem",
              color: "var(--danger)",
              fontSize: "0.9rem"
            }}>
              ⚠️ {error}
            </div>
          )}
          <button 
            type="submit" 
            className="btn btn-primary btn-lg" 
            disabled={submitting}
            style={{ width: "100%" }}
          >
            {submitting ? "⏳ Кіру..." : "🚀 Кіру"}
          </button>
        </form>
        <div className="auth-link-row" style={{ marginTop: "1.5rem" }}>
          <Link to="/register" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            📝 Тіркелу (BUYER / SUPPLIER)
          </Link>
          <Link to="/forgot-password" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            🔑 Құпия сөзді ұмыттым
          </Link>
        </div>
        <div className="demo-hint" style={{
          background: "var(--surface2)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius)",
          padding: "1rem",
          marginTop: "1.5rem"
        }}>
          <strong style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            👤 Демо аккаунттар (5):
          </strong>
          <div style={{ marginTop: "0.75rem", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.85rem" }}>
              <code style={{ 
                background: "var(--accent-light)", 
                padding: "0.25rem 0.5rem", 
                borderRadius: "4px",
                color: "var(--accent)"
              }}>
                employee@smarttender.kz / employee123
              </code>
              <span style={{ color: "var(--muted)" }}>— өтінім жасайды</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.85rem" }}>
              <code style={{ 
                background: "var(--accent-light)", 
                padding: "0.25rem 0.5rem", 
                borderRadius: "4px",
                color: "var(--accent)"
              }}>
                head@smarttender.kz / head123
              </code>
              <span style={{ color: "var(--muted)" }}>— бөлім бекітеді</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.85rem" }}>
              <code style={{ 
                background: "var(--accent-light)", 
                padding: "0.25rem 0.5rem", 
                borderRadius: "4px",
                color: "var(--accent)"
              }}>
                manager@smarttender.kz / manager123
              </code>
              <span style={{ color: "var(--muted)" }}>— buyer, жариялайды</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.85rem" }}>
              <code style={{ 
                background: "var(--accent-light)", 
                padding: "0.25rem 0.5rem", 
                borderRadius: "4px",
                color: "var(--accent)"
              }}>
                supplier@smarttender.kz / supplier123
              </code>
              <span style={{ color: "var(--muted)" }}>— ұсыныс жібереді</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.85rem" }}>
              <code style={{ 
                background: "var(--accent-light)", 
                padding: "0.25rem 0.5rem", 
                borderRadius: "4px",
                color: "var(--accent)"
              }}>
                admin@smarttender.kz / admin123
              </code>
              <span style={{ color: "var(--muted)" }}>— толық құқық</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
