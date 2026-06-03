import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  approveTender,
  createProposal,
  getApproval,
  getProposals,
  getTender,
  rejectTender,
  submitTender,
} from "../api";
import { useAuth } from "../context/AuthContext";
import type { ApprovalStep, Proposal, Tender } from "../types";

export function TenderDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const [tender, setTender] = useState<Tender | null>(null);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [approval, setApproval] = useState<ApprovalStep[]>([]);
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");

  const tenderId = Number(id);

  const reload = async () => {
    if (!tenderId) return;
    try {
      const [t, p, a] = await Promise.all([
        getTender(tenderId),
        getProposals(tenderId).catch(() => []),
        getApproval(tenderId).catch(() => []),
      ]);
      setTender(t);
      setProposals(p);
      setApproval(a);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Қате");
    }
  };

  useEffect(() => {
    reload();
  }, [tenderId]);

  const isEmployee = user?.role === "employee" || user?.role === "superadmin";
  const isApprover = user?.role === "department_head" || user?.role === "procurement_manager" || user?.role === "superadmin";
  const isSupplier = user?.role === "supplier";

  const handleProposal = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await createProposal(tenderId, {
        price: Number(fd.get("price")),
        delivery_days: Number(fd.get("delivery_days")),
        comment: (fd.get("comment") as string) || undefined,
      });
      setMsg("Ұсыныс жіберілді!");
      reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Қате");
    }
  };

  if (!tender) {
    return <p style={{ color: "var(--muted)" }}>Жүктелуде...</p>;
  }

  return (
    <div className="detail-grid">
      <Link to="/tenders" style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
        ← Тендерлерге қайту
      </Link>

      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <h1 className="page-title" style={{ marginBottom: "0.5rem" }}>
              {tender.title}
            </h1>
            <span className={`badge badge-${tender.status}`}>{tender.status}</span>
          </div>
        </div>
        <p style={{ marginTop: "1rem", color: "var(--muted)" }}>{tender.description || "—"}</p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "1rem", marginTop: "1.5rem" }}>
          <div>
            <div className="label">Бюджет</div>
            <strong>{Number(tender.budget).toLocaleString("kk-KZ")} ₸</strong>
          </div>
          <div>
            <div className="label">Дедлайн</div>
            <strong>{new Date(tender.deadline).toLocaleString("kk-KZ")}</strong>
          </div>
        </div>

        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginTop: "1.5rem" }}>
          {isEmployee && tender.status === "draft" && (
            <button
              type="button"
              className="btn btn-primary"
              onClick={async () => {
                await submitTender(tenderId);
                setMsg("Бекітуге жіберілді");
                reload();
              }}
            >
              Бекітуге жіберу
            </button>
          )}
          {isApprover && approval.some((s) => s.status === "pending") && (
            <>
              <button
                type="button"
                className="btn btn-success"
                onClick={async () => {
                  await approveTender(tenderId);
                  setMsg("Бекітілді");
                  reload();
                }}
              >
                Бекіту
              </button>
              <button
                type="button"
                className="btn btn-danger"
                onClick={async () => {
                  await rejectTender(tenderId, "Қабылданбады");
                  setMsg("Қабылданбады");
                  reload();
                }}
              >
                Қабылдамау
              </button>
            </>
          )}
        </div>
        {msg && <p style={{ color: "var(--success)", marginTop: "1rem" }}>{msg}</p>}
        {error && <p className="error-msg">{error}</p>}
      </div>

      {approval.length > 0 && (
        <div className="card">
          <h2 style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>Бекіту workflow</h2>
          {approval.map((s) => (
            <div
              key={s.id}
              style={{
                padding: "0.75rem",
                borderBottom: "1px solid var(--border)",
                display: "flex",
                justifyContent: "space-between",
              }}
            >
              <span>Қадам {s.step}</span>
              <span className={`badge badge-${s.status === "approved" ? "awarded" : s.status === "rejected" ? "closed" : "draft"}`}>
                {s.status}
              </span>
            </div>
          ))}
        </div>
      )}

      {isSupplier && tender.status === "published" && (
        <div className="card">
          <h2 style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>Коммерциялық ұсыныс</h2>
          <form className="form-stack" onSubmit={handleProposal}>
            <div>
              <label className="label">Баға (₸)</label>
              <input className="input" name="price" type="number" min="1" required />
            </div>
            <div>
              <label className="label">Жеткізу (күн)</label>
              <input className="input" name="delivery_days" type="number" min="1" required />
            </div>
            <div>
              <label className="label">Түсініктеме</label>
              <textarea className="input" name="comment" rows={2} />
            </div>
            <button type="submit" className="btn btn-primary">
              Ұсыныс жіберу
            </button>
          </form>
        </div>
      )}

      <div className="card">
        <h2 style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>
          Ұсыныстар ({proposals.length})
        </h2>
        {proposals.map((p) => (
          <div
            key={p.id}
            style={{
              padding: "0.85rem",
              borderBottom: "1px solid var(--border)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div>
              <div>Жеткізуші #{p.supplier_id}</div>
              <div style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
                {Number(p.price).toLocaleString("kk-KZ")} ₸ · {p.delivery_days} күн
              </div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontWeight: 700, color: "var(--accent)" }}>Балл: {p.score}</div>
              <span className="badge badge-published">{p.status}</span>
            </div>
          </div>
        ))}
        {proposals.length === 0 && (
          <p style={{ color: "var(--muted)" }}>Ұсыныстар жоқ</p>
        )}
      </div>
    </div>
  );
}
