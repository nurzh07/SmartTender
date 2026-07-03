import { getRoleConfig } from "../roleConfig";
import type { UserRole } from "../types";

export function RoleBanner({ role }: { role: UserRole }) {
  const config = getRoleConfig(role);
  if (!config) return null;

  return (
    <div className="role-banner" style={{ borderLeftColor: config.accent }}>
      <div className="role-banner-head">
        <span className="role-badge" style={{ background: `${config.accent}22`, color: config.accent }}>
          {config.label}
        </span>
        <p className="role-banner-sub">{config.subtitle}</p>
      </div>
      <ul className="role-task-list">
        {config.tasks.map((task) => (
          <li key={task}>{task}</li>
        ))}
      </ul>
    </div>
  );
}
