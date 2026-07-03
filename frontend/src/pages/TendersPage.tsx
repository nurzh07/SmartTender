import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { createTender, getTenders, deleteTender } from "../api";
import { RoleBanner } from "../components/RoleBanner";
import { SkeletonRow } from "../components/Skeleton";
import { ConfirmModal } from "../components/Modal";
import { useAuth } from "../context/AuthContext";
import {
  canCreateTender,
  defaultStatusFilter,
  filterTendersForRole,
  rolePageSubtitle,
  rolePageTitle,
} from "../utils/tenderFilters";
import type { Tender, TenderStatus, UserRole } from "../types";

const ALL_STATUSES: { value: string; label: string }[] = [
  { value: "", label: "Барлығы" },
  { value: "draft", label: "Жоба" },
  { value: "published", label: "Жарияланған" },
  { value: "evaluation", label: "Бағалау" },
  { value: "awarded", label: "Жеңімпаз" },
  { value: "closed", label: "Жабық" },
];

const SUPPLIER_STATUSES = ALL_STATUSES.filter((s) => !s.value || s.value === "published");

function statusesForRole(role: UserRole) {
  if (role === "supplier") return SUPPLIER_STATUSES;
  return ALL_STATUSES;
}

export function TendersPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const role = user?.role ?? "employee";
  const [tenders, setTenders] = useState<Tender[]>([]);
  const [status, setStatus] = useState(defaultStatusFilter(role));
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [error, setError] = useState("");

  const canCreate = canCreateTender(role);
  const createLabel = role === "employee" ? "+ Жаңа өтінім" : "+ Жаңа тендер";

  const load = () => {
    setLoading(true);
    getTenders(1, status || undefined)
      .then((data) => {
        const scoped = user ? filterTendersForRole(data, role, user.id) : data;
        if (role === "superadmin") {
          setTenders(data);
        } else if (role === "supplier") {
          setTenders(scoped.filter((t) => !status || t.status === status));
        } else {
          setTenders(scoped);
        }
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    setStatus(defaultStatusFilter(role));
  }, [role]);

  useEffect(() => {
    load();
  }, [status, user?.id]);

  const handleCreate = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      const t = await createTender({
        title: fd.get("title"),
        description: fd.get("description") || null,
        budget: Number(fd.get("budget")),
        deadline: new Date(fd.get("deadline") as string).toISOString(),
      });
      setShowCreate(false);
      navigate(`/tenders/${t.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Қате");
    }
  };

  return (
    <div>
      <h1 className="page-title">{rolePageTitle(role)}</h1>
      <p className="page-sub">{rolePageSubtitle(role)}</p>
      <RoleBanner role={role} />

      <div className="toolbar">
        {role !== "employee" && (
          <select
            className="input"
            style={{ width: "auto", minWidth: "160px" }}
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            {statusesForRole(role).map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        )}
        {canCreate && (
          <button type="button" className="btn btn-primary" onClick={() => setShowCreate(true)}>
            {createLabel}
          </button>
        )}
      </div>

      {error && <p className="error-msg">{error}</p>}
      {loading && (
        <div className="tender-list">
          <SkeletonRow />
          <SkeletonRow />
          <SkeletonRow />
          <SkeletonRow />
          <SkeletonRow />
        </div>
      )}

      {!loading && (
        <div className="tender-list">
        {tenders.map((t) => (
          <div
            key={t.id}
            className="tender-row"
            onClick={() => navigate(`/tenders/${t.id}`)}
            onKeyDown={(e) => e.key === "Enter" && navigate(`/tenders/${t.id}`)}
            role="button"
            tabIndex={0}
            style={{
              display: "grid",
              gridTemplateColumns: "1fr auto",
              gap: "1rem",
              alignItems: "center",
            }}
          >
            <div>
              <div style={{ display: "flex", alignItems: "flex-start", gap: "0.75rem" }}>
                <span style={{ fontSize: "1.5rem" }}>
                  {t.status === "published" ? "📋" : 
                   t.status === "draft" ? "📝" :
                   t.status === "evaluation" ? "⚖️" :
                   t.status === "awarded" ? "🏆" :
                   t.status === "closed" ? "🔒" : "📄"}
                </span>
                <div style={{ flex: 1 }}>
                  <strong style={{ fontSize: "1rem", fontWeight: 600 }}>{t.title}</strong>
                  <div style={{ 
                    color: "var(--text-secondary)", 
                    fontSize: "0.85rem", 
                    marginTop: "0.35rem",
                    lineHeight: 1.4
                  }}>
                    {t.description?.slice(0, 100) || "Сипаттама жоқ"}
                  </div>
                  <div style={{ 
                    display: "flex", 
                    gap: "1rem", 
                    fontSize: "0.8rem", 
                    color: "var(--muted)", 
                    marginTop: "0.5rem",
                    flexWrap: "wrap"
                  }}>
                    <span style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
                      💰 {Number(t.budget).toLocaleString("kk-KZ")} ₸
                    </span>
                    <span style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
                      📅 {new Date(t.deadline).toLocaleDateString("kk-KZ")}
                    </span>
                    {t.approval_status && t.approval_status !== "draft" && (
                      <span style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
                        ✋ {t.approval_status}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
            <span 
              className={`badge badge-${t.status as TenderStatus}`}
              style={{ 
                padding: "0.35rem 0.75rem",
                fontSize: "0.75rem",
                fontWeight: 600,
                textTransform: "uppercase",
                letterSpacing: "0.05em"
              }}
            >
              {t.status}
            </span>
          </div>
        ))}
      </div>
      )}

      {!loading && tenders.length === 0 && (
        <p style={{ color: "var(--muted)", textAlign: "center", padding: "2rem" }}>
          {role === "employee"
            ? "Өтінімдер жоқ. «Жаңа өтінім» батырмасы арқылы жасаңыз."
            : role === "supplier"
              ? "Ашық тендерлер жоқ."
              : "Тендерлер табылмады"}
        </p>
      )}

      {showCreate && (
        <div className="modal-overlay" onClick={() => setShowCreate(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2 style={{ marginBottom: "1rem" }}>
              {role === "employee" ? "Жаңа сатып алу өтінімі" : "Жаңа тендер"}
            </h2>
            <form className="form-stack" onSubmit={handleCreate}>
              <div>
                <label className="label">Атауы</label>
                <input className="input" name="title" required />
              </div>
              <div>
                <label className="label">Сипаттама</label>
                <textarea className="input" name="description" rows={3} />
              </div>
              <div>
                <label className="label">Бюджет (₸)</label>
                <input className="input" name="budget" type="number" min="1" required />
              </div>
              <div>
                <label className="label">Дедлайн</label>
                <input className="input" name="deadline" type="datetime-local" required />
              </div>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <button type="submit" className="btn btn-primary">
                  Жасау
                </button>
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreate(false)}>
                  Болдырмау
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
