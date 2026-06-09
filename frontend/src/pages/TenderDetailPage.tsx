import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  approveTender,
  createProposal,
  getApproval,
  getProposals,
  getTender,
  publishTender,
  rejectTender,
  submitTender,
} from "../api";
import { useAuth } from "../context/AuthContext";
import type { ApprovalStep, Proposal, Tender, UserRole } from "../types";

const ROLE_LABELS: Record<UserRole, string> = {
  superadmin: "Әкімші",
  procurement_manager: "Сатып алу менеджері",
  department_head: "Бөлім басшысы",
  employee: "Қызметкер",
  supplier: "Жеткізуші",
};

function isPendingApproval(tender: Tender) {
  const status = tender.approval_status || "draft";
  return status === "pending_approval" || status.startsWith("pending_step_");
}

function canViewProposals(userRole: UserRole | undefined, tender: Tender, userId?: number) {
  if (!userRole || !userId) return false;
  if (["superadmin", "procurement_manager", "department_head"].includes(userRole)) return true;
  if (userRole === "employee") return tender.created_by === userId;
  if (userRole === "supplier") return tender.status === "published";
  return false;
}

function canSubmit(userRole: UserRole | undefined, tender: Tender, userId?: number) {
  if (!userRole || !userId || tender.status !== "draft" || isPendingApproval(tender)) return false;
  if (!["employee", "procurement_manager", "superadmin"].includes(userRole)) return false;
  return userRole === "superadmin" || tender.created_by === userId;
}

function canPublish(userRole: UserRole | undefined, tender: Tender, userId?: number) {
  if (!userRole || tender.status !== "draft") return false;
  if (!["procurement_manager", "superadmin"].includes(userRole)) return false;
  return userRole === "superadmin" || tender.created_by === userId;
}

function canApprove(userRole: UserRole | undefined, steps: ApprovalStep[]) {
  const pending = steps.find((s) => s.status === "pending");
  if (!pending || !userRole) return false;
  if (userRole === "superadmin") return true;
  if (pending.step === 1) return userRole === "department_head";
  if (pending.step === 2) return userRole === "procurement_manager";
  return false;
}

export function TenderDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const [tender, setTender] = useState<Tender | null>(null);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [approval, setApproval] = useState<ApprovalStep[]>([]);
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);

  const tenderId = Number(id);

  const reload = async () => {
    if (!tenderId || !user) return;
    setError("");
    try {
      const t = await getTender(tenderId);
      setTender(t);

      const approvalSteps = isPendingApproval(t) || t.approval_status === "approved" || t.approval_status === "rejected"
        ? await getApproval(tenderId).catch(() => [])
        : [];
      setApproval(approvalSteps);

      if (canViewProposals(user.role, t, user.id)) {
        const p = await getProposals(tenderId).catch(() => []);
        setProposals(p);
      } else {
        setProposals([]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Қате");
    }
  };

  useEffect(() => {
    reload();
  }, [tenderId, user?.id]);

  const runAction = async (action: () => Promise<unknown>, successMsg: string) => {
    setBusy(true);
    setError("");
    setMsg("");
    try {
      await action();
      setMsg(successMsg);
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Қате");
    } finally {
      setBusy(false);
    }
  };

  const handleProposal = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    await runAction(
      () =>
        createProposal(tenderId, {
          price: Number(fd.get("price")),
          delivery_days: Number(fd.get("delivery_days")),
          comment: (fd.get("comment") as string) || undefined,
        }),
      "Ұсыныс сәтті жіберілді!"
    );
    e.currentTarget.reset();
  };

  if (!tender) {
    return <p style={{ color: "var(--muted)" }}>Жүктелуде...</p>;
  }

  const isOwner = user?.id === tender.created_by;
  const showSubmit = canSubmit(user?.role, tender, user?.id);
  const showPublish = canPublish(user?.role, tender, user?.id);
  const showApprove = canApprove(user?.role, approval);
  const showProposalForm = user?.role === "supplier" && tender.status === "published";
  const showProposals = canViewProposals(user?.role, tender, user?.id);

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
            {tender.approval_status && tender.approval_status !== "draft" && (
              <span className="badge badge-draft" style={{ marginLeft: "0.5rem" }}>
                {tender.approval_status}
              </span>
            )}
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

        {user && (
          <p style={{ marginTop: "1rem", fontSize: "0.85rem", color: "var(--muted)" }}>
            Сіз: <strong>{ROLE_LABELS[user.role]}</strong>
            {isOwner ? " · бұл сіздің өтініміңіз" : " · бұл басқа қызметкердің өтінімі"}
          </p>
        )}

        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginTop: "1.5rem" }}>
          {showSubmit && (
            <button
              type="button"
              className="btn btn-primary"
              disabled={busy}
              onClick={() => runAction(() => submitTender(tenderId), "Бекітуге жіберілді")}
            >
              Бекітуге жіберу
            </button>
          )}
          {showPublish && (
            <button
              type="button"
              className="btn btn-primary"
              disabled={busy}
              onClick={() => runAction(() => publishTender(tenderId), "Тендер жарияланды")}
            >
              Жариялау (бекітусіз)
            </button>
          )}
          {showApprove && (
            <>
              <button
                type="button"
                className="btn btn-success"
                disabled={busy}
                onClick={() => runAction(() => approveTender(tenderId), "Бекітілді")}
              >
                Бекіту
              </button>
              <button
                type="button"
                className="btn btn-danger"
                disabled={busy}
                onClick={() => runAction(() => rejectTender(tenderId, "Қабылданбады"), "Қабылданбады")}
              >
                Қабылдамау
              </button>
            </>
          )}
        </div>

        {!showSubmit && !showPublish && !showApprove && user?.role === "employee" && tender.status === "draft" && !isOwner && (
          <p style={{ marginTop: "1rem", color: "var(--muted)", fontSize: "0.9rem" }}>
            Бұл өтінім сізге тиесілі емес — тек өз өтініміңізді бекітуге жібере аласыз.
          </p>
        )}

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
              <span>
                Қадам {s.step}: {s.step === 1 ? "Бөлім басшысы" : "Сатып алу менеджері"}
              </span>
              <span className={`badge badge-${s.status === "approved" ? "awarded" : s.status === "rejected" ? "closed" : "draft"}`}>
                {s.status}
              </span>
            </div>
          ))}
        </div>
      )}

      {showProposalForm && (
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
            <button type="submit" className="btn btn-primary" disabled={busy}>
              Ұсыныс жіберу
            </button>
          </form>
        </div>
      )}

      {user?.role === "supplier" && tender.status !== "published" && (
        <div className="card">
          <p style={{ color: "var(--muted)" }}>
            Ұсыныс жіберу үшін тендер <strong>published</strong> статусында болуы керек.
          </p>
        </div>
      )}

      {showProposals && (
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
                <div>{p.supplier_name || `Жеткізуші #${p.supplier_id}`}</div>
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
      )}
    </div>
  );
}
