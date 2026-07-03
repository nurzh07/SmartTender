import { Link } from "react-router-dom";
import { getTenders, getUsers, getTelegramStatus, getTelegramConnectCode, disconnectTelegram } from "../api";
import { RoleBanner } from "../components/RoleBanner";
import { useAuth } from "../context/AuthContext";
import { filterTendersForRole, tendersNeedingAction } from "../utils/tenderFilters";
import type { Tender, User } from "../types";
import { useEffect, useState } from "react";
import { SkeletonGrid, SkeletonRow } from "../components/Skeleton";

function StatCard({
  label,
  value,
  color,
  to,
  icon,
}: {
  label: string;
  value: number | string;
  color?: string;
  to?: string;
  icon?: string;
}) {
  const inner = (
    <div className="card stat-card" style={{
      background: `linear-gradient(135deg, var(--surface) 0%, ${color ? color + '20' : 'var(--surface2)'} 100%)`,
      borderLeft: `4px solid ${color || 'var(--accent)'}`,
    }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem" }}>
        <div className="stat-label">{label}</div>
        {icon && <span style={{ fontSize: "1.5rem" }}>{icon}</span>}
      </div>
      <div className="stat-value" style={color ? { color } : undefined}>
        {value}
      </div>
    </div>
  );
  return to ? (
    <Link to={to} style={{ textDecoration: "none", color: "inherit" }}>
      {inner}
    </Link>
  ) : (
    inner
  );
}

function ActionList({ title, items, empty }: { title: string; items: Tender[]; empty: string }) {
  return (
    <div className="card">
      <h2 className="section-title">{title}</h2>
      {items.slice(0, 5).map((t) => (
        <Link key={t.id} to={`/tenders/${t.id}`} className="tender-row action-row">
          <div>
            <strong>{t.title}</strong>
            <div className="row-meta">
              {Number(t.budget).toLocaleString("kk-KZ")} ₸ ·{" "}
              {new Date(t.deadline).toLocaleDateString("kk-KZ")}
            </div>
          </div>
          <span className={`badge badge-${t.status}`}>{t.status}</span>
        </Link>
      ))}
      {items.length === 0 && <p className="empty-text">{empty}</p>}
    </div>
  );
}

function TelegramConnectCard() {
  const [linked, setLinked] = useState(false);
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getTelegramStatus().then((data) => setLinked(data.linked)).catch(() => {});
  }, []);

  const handleConnect = async () => {
    setLoading(true);
    try {
      const data = await getTelegramConnectCode();
      setCode(data.code);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    setLoading(true);
    try {
      await disconnectTelegram();
      setLinked(false);
      setCode("");
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2 className="section-title">📱 Telegram байланысы</h2>
      {linked ? (
        <div>
          <p style={{ color: "var(--success)", marginBottom: "0.5rem" }}>✅ Telegram байланысқан</p>
          <button className="btn btn-secondary btn-sm" onClick={handleDisconnect} disabled={loading}>
            {loading ? "Жүктелуде..." : "Ажырату"}
          </button>
        </div>
      ) : code ? (
        <div>
          <p>Бұл кодты Telegram ботына жіберіңіз:</p>
          <div style={{ 
            background: "var(--muted-bg)", 
            padding: "1rem", 
            borderRadius: "8px", 
            fontSize: "1.5rem", 
            fontWeight: "bold",
            textAlign: "center",
            marginBottom: "1rem",
            letterSpacing: "2px"
          }}>
            {code}
          </div>
          <p style={{ fontSize: "0.9rem", color: "var(--muted)" }}>
            1. <a href="https://t.me/SmartTenderKZBot" target="_blank" rel="noopener noreferrer">@SmartTenderKZBot</a> ботына өтіңіз<br/>
            2. <code>/connect {code}</code> командасын жіберіңіз
          </p>
          <button className="btn btn-secondary btn-sm" onClick={() => setCode("")}>
            Жаңа код
          </button>
        </div>
      ) : (
        <div>
          <p style={{ marginBottom: "0.5rem" }}>Telegram арқылы хабарландыру алу үшін аккаунтыңызды байланыстырыңыз.</p>
          <button className="btn btn-primary btn-sm" onClick={handleConnect} disabled={loading}>
            {loading ? "Жүктелуде..." : "Байланыстыру"}
          </button>
        </div>
      )}
    </div>
  );
}

function CompanyVerificationBadge({ user }: { user: User }) {
  if (!user.bin_verified || !user.company_official_name) return null;
  
  return (
    <div style={{
      background: "rgba(34, 197, 94, 0.1)",
      border: "1px solid rgba(34, 197, 94, 0.3)",
      borderRadius: "8px",
      padding: "0.75rem",
      marginTop: "1rem"
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
        <span style={{ fontSize: "1.25rem" }}>✓</span>
        <div>
          <div style={{ fontWeight: "bold", color: "var(--success)", fontSize: "0.9rem" }}>
            Расталған компания
          </div>
          <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
            {user.company_official_name}
          </div>
        </div>
      </div>
    </div>
  );
}

function SupplierDashboard({ tenders }: { tenders: Tender[] }) {
  const open = tenders.filter((t) => t.status === "published");
  return (
    <>
      <div className="grid-3">
        <StatCard label="Ашық тендерлер" value={open.length} color="var(--success)" to="/tenders" icon="📋" />
        <StatCard label="Барлық лоттар" value={open.length} to="/tenders" icon="📦" />
      </div>
      <ActionList
        title="Ұсыныс жіберуге болатын тендерлер"
        items={open}
        empty="Қазір ашық тендер жоқ."
      />
    </>
  );
}

function BuyerDashboard({ tenders, userId }: { tenders: Tender[]; userId: number }) {
  const toPublish = tenders.filter((t) => t.approval_status === "approved" && t.status === "draft");
  const toApprove = tenders.filter((t) => t.approval_status === "pending_step_2");
  const active = tenders.filter((t) => ["published", "evaluation"].includes(t.status));
  const mine = tenders.filter((t) => t.created_by === userId);

  return (
    <>
      <div className="grid-3">
        <StatCard label="Жариялауға дайын" value={toPublish.length} color="var(--warning)" to="/tenders" icon="🚀" />
        <StatCard label="Бекіту күтуде (2-қадам)" value={toApprove.length} color="var(--accent)" to="/tenders" icon="⏳" />
        <StatCard label="Белсенді тендерлер" value={active.length} color="var(--success)" to="/tenders" icon="📊" />
      </div>
      {toApprove.length > 0 && (
        <ActionList title="Бекіту қажет — қызметкер өтінімі" items={toApprove} empty="" />
      )}
      {toPublish.length > 0 && (
        <ActionList title="Жариялау керек" items={toPublish} empty="" />
      )}
      <ActionList title="Менің тендерлерім" items={mine} empty="Тендер жоқ. Жаңасын жасаңыз." />
    </>
  );
}

function EmployeeDashboard({ tenders, userId }: { tenders: Tender[]; userId: number }) {
  const mine = tenders.filter((t) => t.created_by === userId);
  const drafts = mine.filter((t) => t.status === "draft" && !["pending_approval", "approved"].includes(t.approval_status || "draft") && !(t.approval_status || "").startsWith("pending"));
  const pending = mine.filter((t) => (t.approval_status || "").startsWith("pending"));
  const done = mine.filter((t) => t.approval_status === "approved" || t.status !== "draft");

  return (
    <>
      <div className="grid-3">
        <StatCard label="Жоба (жіберілмеген)" value={drafts.length} to="/tenders" />
        <StatCard label="Бекітуде" value={pending.length} color="var(--warning)" to="/tenders" />
        <StatCard label="Бекітілген/жарияланған" value={done.length} color="var(--success)" to="/tenders" />
      </div>
      <ActionList
        title="Жіберу керек өтінімдер"
        items={drafts}
        empty="Барлық өтінімдер жіберілген."
      />
      <ActionList title="Бекіту процесінде" items={pending} empty="Бекіту күтетін өтінім жоқ." />
    </>
  );
}

function DepartmentHeadDashboard({ tenders }: { tenders: Tender[] }) {
  const queue = tenders.filter((t) => t.approval_status === "pending_approval");
  const approved = tenders.filter((t) => t.approval_status === "pending_step_2" || t.approval_status === "approved");
  const rejected = tenders.filter((t) => t.approval_status === "rejected");

  return (
    <>
      <div className="grid-3">
        <StatCard label="Кезекте" value={queue.length} color="var(--warning)" to="/approvals" />
        <StatCard label="Бекітілді (келесі қадам)" value={approved.length} />
        <StatCard label="Қабылданбады" value={rejected.length} color="var(--danger)" />
      </div>
      <ActionList
        title="Бекіту кезегі — сіздің шешіміңіз керек"
        items={queue}
        empty="Кезекте өтінім жоқ."
      />
    </>
  );
}

function SuperadminDashboard({ tenders, users }: { tenders: Tender[]; users: User[] }) {
  return (
    <>
      <div className="grid-3">
        <StatCard label="Тендерлер" value={tenders.length} to="/tenders" />
        <StatCard label="Пайдаланушылар" value={users.length} to="/users" />
        <StatCard
          label="Белсенді"
          value={users.filter((u) => u.is_active).length}
          color="var(--success)"
          to="/users"
        />
      </div>
      <ActionList title="Соңғы тендерлер" items={tenders} empty="Тендерлер жоқ." />
    </>
  );
}

export function DashboardPage() {
  const { user } = useAuth();
  const [tenders, setTenders] = useState<Tender[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getTenders(1),
      user?.role === "superadmin" ? getUsers() : Promise.resolve([])
    ])
      .then(([t, u]) => {
        setTenders(t);
        if (user?.role === "superadmin") {
          setUsers(u as User[]);
        }
      })
      .catch(() => {
        setTenders([]);
        setUsers([]);
      })
      .finally(() => setLoading(false));
  }, [user?.role]);

  if (!user) return null;

  if (loading) {
    return (
      <div>
        <h1 className="page-title">Қош келдіңіз!</h1>
        <SkeletonGrid count={3} />
        <div className="card" style={{ marginTop: "1rem" }}>
          <h2 className="section-title">Жүктелуде...</h2>
          <SkeletonRow />
          <SkeletonRow />
          <SkeletonRow />
        </div>
      </div>
    );
  }

  const role = user.role;
  const scoped =
    role === "superadmin"
      ? tenders
      : filterTendersForRole(tenders, role, user.id);
  const actions = tendersNeedingAction(tenders, role, user.id);

  return (
    <div>
      <h1 className="page-title">Қош келдіңіз, {user.full_name || user.email}!</h1>
      <RoleBanner role={role} />
      <CompanyVerificationBadge user={user} />

      <div className="grid-2" style={{ marginTop: "1.5rem" }}>
        <div>
          {actions.length > 0 && role !== "superadmin" && (
            <div className="card action-alert">
              <strong>⚡ Сізде {actions.length} тапсырма бар</strong>
              <Link to={role === "department_head" ? "/approvals" : "/tenders"} className="btn btn-primary btn-sm">
                Қарау
              </Link>
            </div>
          )}

          <div style={{ marginTop: "1.5rem" }}>
            {role === "supplier" && <SupplierDashboard tenders={tenders} />}
            {role === "buyer" && <BuyerDashboard tenders={tenders} userId={user.id} />}
            {role === "employee" && <EmployeeDashboard tenders={scoped} userId={user.id} />}
            {role === "department_head" && <DepartmentHeadDashboard tenders={tenders} />}
            {role === "superadmin" && <SuperadminDashboard tenders={tenders} users={users} />}
          </div>
        </div>

        <div>
          <TelegramConnectCard />
        </div>
      </div>
    </div>
  );
}
