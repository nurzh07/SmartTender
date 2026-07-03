import { useToast } from "../context/ToastContext";

const toastIcons: Record<string, string> = {
  success: "✅",
  error: "❌",
  warning: "⚠️",
  info: "ℹ️",
};

const toastColors: Record<string, { bg: string; border: string; text: string }> = {
  success: {
    bg: "var(--success-light)",
    border: "var(--success)",
    text: "var(--success)",
  },
  error: {
    bg: "var(--danger-light)",
    border: "var(--danger)",
    text: "var(--danger)",
  },
  warning: {
    bg: "var(--warning-light)",
    border: "var(--warning)",
    text: "var(--warning)",
  },
  info: {
    bg: "var(--accent-light)",
    border: "var(--accent)",
    text: "var(--accent)",
  },
};

export function ToastContainer() {
  const { toasts, removeToast } = useToast();

  return (
    <div
      style={{
        position: "fixed",
        top: "1rem",
        right: "1rem",
        zIndex: 9999,
        display: "flex",
        flexDirection: "column",
        gap: "0.5rem",
        maxWidth: "400px",
      }}
    >
      {toasts.map((toast) => {
        const colors = toastColors[toast.type];
        return (
          <div
            key={toast.id}
            style={{
              background: colors.bg,
              border: `1px solid ${colors.border}`,
              borderRadius: "var(--radius)",
              padding: "1rem",
              boxShadow: "var(--shadow-lg)",
              display: "flex",
              alignItems: "center",
              gap: "0.75rem",
              animation: "slideIn 0.3s ease-out",
              minWidth: "300px",
            }}
          >
            <span style={{ fontSize: "1.25rem" }}>{toastIcons[toast.type]}</span>
            <span style={{ flex: 1, color: colors.text, fontSize: "0.9rem" }}>
              {toast.message}
            </span>
            <button
              type="button"
              onClick={() => removeToast(toast.id)}
              style={{
                background: "none",
                border: "none",
                color: colors.text,
                cursor: "pointer",
                fontSize: "1.25rem",
                padding: "0.25rem",
                lineHeight: 1,
                opacity: 0.7,
              }}
              onMouseEnter={(e) => e.currentTarget.style.opacity = "1"}
              onMouseLeave={(e) => e.currentTarget.style.opacity = "0.7"}
            >
              ×
            </button>
          </div>
        );
      })}
    </div>
  );
}
