import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getRoleConfig } from "../roleConfig";

const navIcons: Record<string, string> = {
  "/": "🏠",
  "/tenders": "📋",
  "/proposals": "📝",
  "/analytics": "📊",
  "/users": "👥",
  "/reports": "📈",
  "/departments": "🏢",
  "/categories": "🗂️",
};

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
              <span>{navIcons[item.to] || "📄"}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div style={{ 
            display: "flex", 
            alignItems: "center", 
            gap: "0.75rem",
            padding: "0.75rem",
            background: "var(--surface2)",
            borderRadius: "var(--radius)",
            marginBottom: "1rem"
          }}>
            <div style={{
              width: "36px",
              height: "36px",
              borderRadius: "50%",
              background: "var(--accent-light)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "1.2rem",
              fontWeight: "600",
              color: "var(--accent)"
            }}>
              {(user?.full_name || user?.email || "U").charAt(0).toUpperCase()}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ 
                fontWeight: 600, 
                fontSize: "0.9rem",
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis"
              }}>
                {user?.full_name || user?.email}
              </div>
              <div style={{ 
                fontSize: "0.8rem", 
                color: "var(--muted)",
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis"
              }}>
                {user?.email}
              </div>
            </div>
          </div>
          <button
            type="button"
            className="btn btn-outline"
            style={{ width: "100%" }}
            onClick={logout}
          >
            🚪 Шығу
          </button>
        </div>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
