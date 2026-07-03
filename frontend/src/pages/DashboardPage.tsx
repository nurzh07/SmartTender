import { Link } from "react-router-dom";
import { getTenders, getUsers } from "../api";
import { RoleBanner } from "../components/RoleBanner";
import { useAuth } from "../context/AuthContext";
import { filterTendersForRole, tendersNeedingAction } from "../utils/tenderFilters";
import type { Tender, User, UserRole } from "../types";
import { useEffect, useState } from "react";

function StatCard({
  label,
  value,
  color,
  to,
}: {
  label: string;
  value: number | string;
  color?: string;
  to?: string;
}) {
  const inner = (
    <div className="card stat-card">
      <div className="stat-label">{label}</div>
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

function SupplierDashboard({ tenders }: { tenders: Tender[] }) {
  const open = tenders.filter((t) => t.status === "published");
  return (
    <>
      <div className="grid-3">
        <StatCard label="Ашық тендерлер" value={open.length} color="var(--success)" to="/tenders" />
        <StatCard label="Барлық лоттар" value={open.length} to="/tenders" />
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
        <StatCard label="Жариялауға дайын" value={toPublish.length} color="var(--warning)" to="/tenders" />
        <StatCard label="Бекіту күтуде (2-қадам)" value={toApprove.length} color="var(--accent)" to="/tenders" />
        <StatCard label="Белсенді тендерлер" value={active.length} color="var(--success)" to="/tenders" />
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

  useEffect(() => {
    getTenders(1).then(setTenders).catch(() => setTenders([]));
    if (user?.role === "superadmin") {
      getUsers().then(setUsers).catch(() => setUsers([]));
    }
  }, [user?.role]);

  if (!user) return null;

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
  );
}
