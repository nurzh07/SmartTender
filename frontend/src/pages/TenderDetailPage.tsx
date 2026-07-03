import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  approveTender,
  createProposal,
  deleteTender,
  getApproval,
  getProposals,
  getTender,
  publishTender,
  rejectTender,
  submitTender,
  updateTenderStatus,
} from "../api";
import { RoleBanner } from "../components/RoleBanner";
import { getRoleConfig } from "../roleConfig";
import { useAuth } from "../context/AuthContext";
import type { ApprovalStep, Proposal, Tender, UserRole } from "../types";

const ROLE_LABELS: Record<UserRole, string> = {
  superadmin: "Әкімші",
  buyer: "Сатып алушы (Buyer)",
  department_head: "Бөлім басшысы",
  employee: "Қызметкер",
  procurement_manager: "Сатып алу менеджері",
  supplier: "Жеткізуші",
};

function isPendingApproval(tender: Tender) {
  const status = tender.approval_status || "draft";
  return status === "pending_approval" || status.startsWith("pending_step_");
}

function canViewProposals(userRole: UserRole | undefined, tender: Tender, userId?: number) {
  if (!userRole || !userId) return false;
  if (["superadmin", "buyer", "department_head"].includes(userRole)) return true;
  if (userRole === "employee") return tender.created_by === userId;
  if (userRole === "supplier") return tender.status === "published";
  return false;
}

function canSubmit(userRole: UserRole | undefined, tender: Tender, userId?: number) {
  if (!userRole || !userId || tender.status !== "draft" || isPendingApproval(tender)) return false;
  if (!["employee", "buyer", "superadmin"].includes(userRole)) return false;
  return userRole === "superadmin" || tender.created_by === userId;
}

function canApprove(userRole: UserRole | undefined, steps: ApprovalStep[]) {
  const pending = steps.find((s) => s.status === "pending");
  if (!pending || !userRole) return false;
  if (userRole === "superadmin") return true;
  if (pending.step === 1) return userRole === "department_head";
  if (pending.step === 2) return userRole === "buyer";
  return false;
}

function canPublish(userRole: UserRole | undefined, tender: Tender, userId?: number) {
  if (!userRole || !userId || tender.status !== "draft") return false;
  if (!["buyer", "superadmin"].includes(userRole)) return false;
  if (userRole === "superadmin") return true;
  const approval = tender.approval_status || "draft";
  if (approval === "approved") return true;
  if (approval === "draft" && tender.created_by === userId) return true;
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
  const showApprove = canApprove(user?.role, approval);
  const showPublish = canPublish(user?.role, tender, user?.id);
  const showProposalForm = user?.role === "supplier" && tender.status === "published";
  const showProposals = canViewProposals(user?.role, tender, user?.id);
  const roleConfig = user ? getRoleConfig(user.role) : null;

  const canManageLifecycle =
    user && ["buyer", "superadmin"].includes(user.role) && tender.status !== "draft";
  const canDelete =
    user &&
    (user.role === "superadmin" ||
      (tender.created_by === user.id && tender.status === "draft"));

  return (
    <div className="detail-grid">
      <Link to="/tenders" style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
        ← Артқа
      </Link>

      {user && <RoleBanner role={user.role} />}

      {roleConfig && (
        <div className="card role-hint">
          <strong>Сіздің тапсырмаңыз:</strong>{" "}
          {user?.role === "employee" && isOwner && showSubmit && "Өтінімді бекітуге жіберіңіз."}
          {user?.role === "employee" && isOwner && isPendingApproval(tender) && "Бекіту нәтижесін күтіңіз."}
          {user?.role === "department_head" && showApprove && "Өтінімді бекітіңіз немесе қабылдамаңыз."}
          {user?.role === "buyer" && showApprove && "Қызметкер өтінімін бекітіңіз (2-қадам)."}
          {user?.role === "buyer" && showPublish && "Тендерді жариялаңыз."}
          {user?.role === "buyer" && tender.status === "published" && "Ұсыныстарды қараңыз, бағалауға өткізіңіз."}
          {user?.role === "buyer" && tender.status === "evaluation" && "Жеңімпаз таңдаңыз."}
          {user?.role === "supplier" && showProposalForm && "Коммерциялық ұсыныс жіберіңіз."}
          {user?.role === "superadmin" && "Толық басқару құқығы."}
        </div>
      )}

      <div className="card" style={{
        background: `linear-gradient(135deg, var(--surface) 0%, ${tender.status === 'published' ? 'rgba(16, 185, 129, 0.05)' : tender.status === 'awarded' ? 'rgba(245, 158, 11, 0.05)' : 'var(--surface)'} 100%)`,
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1rem" }}>
          <div style={{ flex: 1 }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.75rem" }}>
              <h1 className="page-title" style={{ marginBottom: "0", fontSize: "1.5rem" }}>
                {tender.title}
              </h1>
              <span 
                className={`badge badge-${tender.status}`}
                style={{ 
                  padding: "0.4rem 0.75rem",
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  textTransform: "uppercase",
                  letterSpacing: "0.05em"
                }}
              >
                {tender.status === "published" ? "📋 Жарияланған" :
                 tender.status === "draft" ? "📝 Жоба" :
                 tender.status === "evaluation" ? "⚖️ Бағалау" :
                 tender.status === "awarded" ? "🏆 Жеңімпаз" :
                 tender.status === "closed" ? "🔒 Жабық" : tender.status}
              </span>
              {tender.approval_status && tender.approval_status !== "draft" && (
                <span className="badge badge-draft" style={{ marginLeft: "0.5rem" }}>
                  ✋ {tender.approval_status}
                </span>
              )}
            </div>
          </div>
        </div>
        <p style={{ 
          marginTop: "0.5rem", 
          color: "var(--text-secondary)", 
          lineHeight: 1.6,
          fontSize: "0.95rem"
        }}>
          {tender.description || "Сипаттама жоқ"}
        </p>
        <div style={{ 
          display: "grid", 
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", 
          gap: "1.5rem", 
          marginTop: "1.5rem",
          padding: "1rem",
          background: "var(--surface2)",
          borderRadius: "var(--radius)",
          border: "1px solid var(--border)"
        }}>
          <div>
            <div className="label" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              💰 Бюджет
            </div>
            <strong style={{ fontSize: "1.1rem", color: "var(--success)" }}>
              {Number(tender.budget).toLocaleString("kk-KZ")} ₸
            </strong>
          </div>
          <div>
            <div className="label" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              📅 Дедлайн
            </div>
            <strong style={{ fontSize: "1rem" }}>
              {new Date(tender.deadline).toLocaleDateString("kk-KZ")}
            </strong>
          </div>
          <div>
            <div className="label" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              👤 Жасаған
            </div>
            <strong style={{ fontSize: "1rem" }}>
              {tender.created_by}
            </strong>
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
              onClick={() => runAction(() => publishTender(tenderId), "Тендер жарияланды!")}
            >
              Жариялау
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
          {canManageLifecycle && tender.status === "published" && proposals.length > 0 && (
            <button
              type="button"
              className="btn btn-secondary"
              disabled={busy}
              onClick={() =>
                runAction(() => updateTenderStatus(tenderId, "evaluation"), "Бағалау басталды")
              }
            >
              Бағалауға өткізу
            </button>
          )}
          {canManageLifecycle && ["published", "evaluation"].includes(tender.status) && proposals.length > 0 && (
            <button
              type="button"
              className="btn btn-success"
              disabled={busy}
              onClick={() =>
                runAction(() => updateTenderStatus(tenderId, "awarded"), "Жеңімпаз таңдалды!")
              }
            >
              Жеңімпаз таңдау
            </button>
          )}
          {canManageLifecycle && tender.status === "awarded" && (
            <button
              type="button"
              className="btn btn-secondary"
              disabled={busy}
              onClick={() => runAction(() => updateTenderStatus(tenderId, "closed"), "Тендер жабылды")}
            >
              Жабу
            </button>
          )}
          {canDelete && (
            <button
              type="button"
              className="btn btn-danger"
              disabled={busy}
              onClick={() => {
                if (window.confirm("Өшіресіз бе?")) {
                  runAction(async () => {
                    await deleteTender(tenderId);
                    window.location.href = "/tenders";
                  }, "Өшірілді");
                }
              }}
            >
              Өшіру
            </button>
          )}
        </div>

        {!showSubmit && !showApprove && user?.role === "employee" && tender.status === "draft" && !isOwner && (
          <p style={{ marginTop: "1rem", color: "var(--muted)", fontSize: "0.9rem" }}>
            Бұл өтінім сізге тиесілі емес — тек өз өтініміңізді бекітуге жібере аласыз.
          </p>
        )}

        {user?.role === "buyer" && tender.status === "draft" && !showApprove && !showPublish && (
          <p style={{ marginTop: "1rem", color: "var(--muted)", fontSize: "0.9rem" }}>
            Жариялау approval workflow толық аяқталғаннан кейін қолжетімді.
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
                Қадам {s.step}: {s.step === 1 ? "Бөлім басшысы" : "Сатып алушы (Buyer)"}
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
          <h2 style={{ 
            fontSize: "1.1rem", 
            marginBottom: "1rem",
            display: "flex",
            alignItems: "center",
            gap: "0.5rem"
          }}>
            📝 Ұсыныстар ({proposals.length})
          </h2>
          {proposals.map((p, index) => (
            <div
              key={p.id}
              style={{
                padding: "1rem",
                borderBottom: proposals.length > index + 1 ? "1px solid var(--border)" : "none",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                background: index === 0 ? "var(--surface2)" : "transparent",
                borderRadius: "var(--radius-sm)",
                marginBottom: "0.25rem"
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                <div style={{
                  width: "32px",
                  height: "32px",
                  borderRadius: "50%",
                  background: "var(--accent-light)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "1rem"
                }}>
                  🏢
                </div>
                <div>
                  <div style={{ fontWeight: "600", fontSize: "0.95rem" }}>
                    {p.supplier_name || `Жеткізуші #${p.supplier_id}`}
                  </div>
                  <div style={{ color: "var(--muted)", fontSize: "0.85rem", marginTop: "0.25rem" }}>
                    💰 {Number(p.price).toLocaleString("kk-KZ")} ₸ · 📦 {p.delivery_days} күн
                  </div>
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ 
                  fontWeight: "700", 
                  color: p.score > 80 ? "var(--success)" : p.score > 50 ? "var(--warning)" : "var(--accent)",
                  fontSize: "1.1rem"
                }}>
                  {p.score} балл
                </div>
                <span 
                  className="badge badge-published"
                  style={{ 
                    marginTop: "0.25rem",
                    padding: "0.25rem 0.5rem",
                    fontSize: "0.7rem"
                  }}
                >
                  {p.status}
                </span>
              </div>
            </div>
          ))}
          {proposals.length === 0 && (
            <div style={{ 
              textAlign: "center", 
              padding: "2rem", 
              color: "var(--muted)",
              fontSize: "0.9rem"
            }}>
              📭 Ұсыныстар жоқ
            </div>
          )}
        </div>
      )}
    </div>
  );
}
