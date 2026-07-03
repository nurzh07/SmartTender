import { FormEvent, useState } from "react";
import { Navigate, useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function RegisterPage() {
  const { user, loading, register } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState<"buyer" | "supplier">("buyer");
  const [bin, setBin] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [useBin, setUseBin] = useState(false);

  if (!loading && user) return <Navigate to="/" replace />;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      if (useBin) {
        await register(email, password, fullName, role, bin);
      } else {
        await register(email, password, fullName, role, undefined, companyName);
      }
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
        <div className="card login-card" style={{ textAlign: "center" }}>
          <div style={{ fontSize: 48, marginBottom: "0.75rem" }}>✅</div>
          <h2 style={{ color: "var(--success)", marginBottom: "0.5rem" }}>Тіркелу сәтті!</h2>
          <p style={{ color: "var(--muted)" }}>
            Email-ге растау сілтемесі жіберілді. 3 секундтан кейін кіру бетіне бағытталасыз...
          </p>
        </div>
      </div>
    );
  }

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
            📝 Тіркелу
          </p>
        </div>

        <form className="form-stack" onSubmit={handleSubmit}>
          <div>
            <label className="label" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              👤 Аты-жөні
            </label>
            <input
              className="input"
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
              placeholder="Иванов Иван"
            />
          </div>
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
              placeholder="you@company.kz"
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
              minLength={6}
              placeholder="Кемінде 6 таңба"
            />
          </div>
          <div>
            <label className="label" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              🎭 Рөл
            </label>
            <select
              className="input"
              value={role}
              onChange={(e) => setRole(e.target.value as "buyer" | "supplier")}
              required
            >
              <option value="buyer">🏢 BUYER — Сатып алушы</option>
              <option value="supplier">🚛 SUPPLIER — Жеткізуші</option>
            </select>
          </div>

          {/* Company identification toggle */}
          <div>
            <div style={{ marginBottom: "0.5rem" }}>
              <label className="label" style={{ marginBottom: "0.5rem", display: "block" }}>
                🏢 Компанияны растау тәсілі
              </label>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <button
                  type="button"
                  className={`btn ${useBin ? "btn-primary" : "btn-outline"}`}
                  onClick={() => setUseBin(true)}
                  style={{ flex: 1, padding: "0.5rem", fontSize: "0.85rem" }}
                >
                  🆔 БИН арқылы
                </button>
                <button
                  type="button"
                  className={`btn ${!useBin ? "btn-primary" : "btn-outline"}`}
                  onClick={() => setUseBin(false)}
                  style={{ flex: 1, padding: "0.5rem", fontSize: "0.85rem" }}
                >
                  🏢 Компания аты арқылы
                </button>
              </div>
            </div>

            {useBin ? (
              <div>
                <label className="label">🆔 БИН</label>
                <input
                  className="input"
                  type="text"
                  value={bin}
                  onChange={(e) => setBin(e.target.value.replace(/\D/g, "").slice(0, 12))}
                  placeholder="123456789012 (12 цифр)"
                  maxLength={12}
                />
                <p style={{ color: "var(--muted)", fontSize: "0.8rem", marginTop: "0.25rem" }}>
                  🔍 Мемлекеттік тізілімде автоматты тексеріледі
                </p>
              </div>
            ) : (
              <div>
                <label className="label">🏢 Компания аты</label>
                <input
                  className="input"
                  type="text"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="«SmartTender» ЖШС"
                />
                <p style={{ color: "var(--muted)", fontSize: "0.8rem", marginTop: "0.25rem" }}>
                  🏢 Қолмен енгізілетін компания аты
                </p>
              </div>
            )}
          </div>

          {error && (
            <div
              style={{
                background: "var(--danger-light)",
                border: "1px solid var(--danger)",
                borderRadius: "var(--radius)",
                padding: "0.75rem",
                color: "var(--danger)",
                fontSize: "0.9rem",
              }}
            >
              ⚠️ {error}
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary btn-lg"
            disabled={submitting}
            style={{ width: "100%", marginTop: "0.25rem" }}
          >
            {submitting ? "⏳ Тіркелуде..." : "🚀 Тіркелу"}
          </button>
        </form>

        <div
          style={{
            marginTop: "1.5rem",
            textAlign: "center",
            fontSize: "0.9rem",
            color: "var(--muted)",
          }}
        >
          Аккаунтыңыз бар ма?{" "}
          <Link to="/login" style={{ color: "var(--accent)", fontWeight: 500 }}>
            🔑 Кіру
          </Link>
        </div>
      </div>
    </div>
  );
}
