import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getTenders } from "../api";
import { RoleBanner } from "../components/RoleBanner";
import { useAuth } from "../context/AuthContext";
import type { Tender } from "../types";

export function ApprovalsPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [tenders, setTenders] = useState<Tender[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getTenders(1)
      .then((data) => {
        setTenders(data.filter((t) => t.approval_status === "pending_approval"));
      })
      .catch(() => setTenders([]))
      .finally(() => setLoading(false));
  }, []);

  if (user?.role !== "department_head" && user?.role !== "superadmin") {
    return (
      <p className="error-msg">Бұл бет тек бөлім басшысына арналған.</p>
    );
  }

  return (
    <div>
      <h1 className="page-title">Бекіту кезегі</h1>
      <p className="page-sub">Қызметкерлерден келген сатып алу өтінімдері — 1-қадам</p>
      <RoleBanner role="department_head" />

      {loading && <p style={{ color: "var(--muted)" }}>Жүктелуде...</p>}

      <div className="tender-list">
        {tenders.map((t) => (
          <div
            key={t.id}
            className="tender-row"
            onClick={() => navigate(`/tenders/${t.id}`)}
            role="button"
            tabIndex={0}
          >
            <div>
              <strong>{t.title}</strong>
              <div className="row-meta">
                {Number(t.budget).toLocaleString("kk-KZ")} ₸ ·{" "}
                {new Date(t.deadline).toLocaleDateString("kk-KZ")}
              </div>
            </div>
            <span className="badge badge-draft">бекіту күтуде</span>
          </div>
        ))}
      </div>

      {!loading && tenders.length === 0 && (
        <p className="empty-text" style={{ textAlign: "center", padding: "2rem" }}>
          Кезекте өтінім жоқ — барлығы өңделген.
        </p>
      )}
    </div>
  );
}
