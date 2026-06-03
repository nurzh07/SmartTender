import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getTenders } from "../api";
import { useAuth } from "../context/AuthContext";
import type { Tender } from "../types";

export function DashboardPage() {
  const { user } = useAuth();
  const [tenders, setTenders] = useState<Tender[]>([]);

  useEffect(() => {
    getTenders(1).then(setTenders).catch(() => setTenders([]));
  }, []);

  const published = tenders.filter((t) => t.status === "published").length;
  const draft = tenders.filter((t) => t.status === "draft").length;

  return (
    <div>
      <h1 className="page-title">Қош келдіңіз, {user?.full_name || "пайдаланушы"}!</h1>
      <p className="page-sub">SmartTender — ішкі сатып алу және тендерлерді басқару</p>

      <div className="grid-3">
        <div className="card">
          <div style={{ color: "var(--muted)", fontSize: "0.85rem" }}>Барлық тендерлер</div>
          <div style={{ fontSize: "2rem", fontWeight: 700 }}>{tenders.length}</div>
        </div>
        <div className="card">
          <div style={{ color: "var(--muted)", fontSize: "0.85rem" }}>Жарияланған</div>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "var(--accent)" }}>
            {published}
          </div>
        </div>
        <div className="card">
          <div style={{ color: "var(--muted)", fontSize: "0.85rem" }}>Жобалар</div>
          <div style={{ fontSize: "2rem", fontWeight: 700 }}>{draft}</div>
        </div>
      </div>

      <div className="card">
        <h2 style={{ marginBottom: "1rem", fontSize: "1.1rem" }}>Соңғы тендерлер</h2>
        {tenders.slice(0, 5).map((t) => (
          <Link
            key={t.id}
            to={`/tenders/${t.id}`}
            className="tender-row"
            style={{ marginBottom: "0.5rem", textDecoration: "none", color: "inherit" }}
          >
            <div>
              <strong>{t.title}</strong>
              <div style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
                Бюджет: {Number(t.budget).toLocaleString("kk-KZ")} ₸
              </div>
            </div>
            <span className={`badge badge-${t.status}`}>{t.status}</span>
          </Link>
        ))}
        {tenders.length === 0 && (
          <p style={{ color: "var(--muted)" }}>Тендерлер жоқ. Тендерлер бөліміне өтіңіз.</p>
        )}
        <Link to="/tenders" className="btn btn-primary" style={{ marginTop: "1rem" }}>
          Барлық тендерлер
        </Link>
      </div>
    </div>
  );
}
