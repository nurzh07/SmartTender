import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getRoleConfig } from "../roleConfig";

export function Layout() {
  const { user, logout } = useAuth();
  const config = getRoleConfig(user?.role ?? "employee");

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          Smart<span>Tender</span>
        </div>
        {config && (
          <div className="sidebar-role" style={{ borderColor: config.accent }}>
            <div className="sidebar-role-label" style={{ color: config.accent }}>
              {config.label}
            </div>
            <div className="sidebar-role-sub">{config.subtitle}</div>
          </div>
        )}
        <nav>
          {config?.nav.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end}>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div style={{ marginTop: "auto", paddingTop: "1rem", fontSize: "0.85rem" }}>
          <div style={{ color: "var(--muted)" }}>{user?.full_name || user?.email}</div>
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
