import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const ROLE_LABELS: Record<string, string> = {
  superadmin: "Әкімші",
  buyer: "Сатып алушы (Buyer)",
  department_head: "Бөлім басшысы",
  employee: "Қызметкер",
  supplier: "Жеткізуші",
};

export function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          Smart<span>Tender</span>
        </div>
        <nav>
          <NavLink to="/" end>
            Басты бет
          </NavLink>
          <NavLink to="/tenders">Тендерлер</NavLink>
          <NavLink to="/notifications">Хабарламалар</NavLink>
          <NavLink to="/reports">Есептер</NavLink>
        </nav>
        <div style={{ marginTop: "auto", paddingTop: "1rem", fontSize: "0.85rem" }}>
          <div style={{ color: "var(--muted)" }}>{user?.full_name || user?.email}</div>
          <div style={{ color: "var(--accent)", fontSize: "0.75rem" }}>
            {user?.role && ROLE_LABELS[user.role]}
          </div>
          <button
            type="button"
            className="btn btn-secondary"
            style={{ marginTop: "0.75rem", width: "100%" }}
            onClick={logout}
          >
            Шығу
          </button>
        </div>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
