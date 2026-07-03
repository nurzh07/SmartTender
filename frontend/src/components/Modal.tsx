import { ReactNode } from "react";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  size?: "sm" | "md" | "lg";
}

const modalSizes: Record<string, { maxWidth: string }> = {
  sm: { maxWidth: "400px" },
  md: { maxWidth: "500px" },
  lg: { maxWidth: "700px" },
};

export function Modal({ isOpen, onClose, title, children, size = "md" }: ModalProps) {
  if (!isOpen) return null;

  const sizeStyles = modalSizes[size];

  return (
    <div
      className="modal-overlay"
      onClick={onClose}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: "rgba(0, 0, 0, 0.6)",
        backdropFilter: "blur(4px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
        padding: "1rem",
        animation: "fadeIn 0.2s ease-out",
      }}
    >
      <div
        className="modal"
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "var(--surface)",
          borderRadius: "var(--radius-lg)",
          boxShadow: "var(--shadow-xl)",
          width: "100%",
          maxWidth: sizeStyles.maxWidth,
          maxHeight: "90vh",
          overflow: "auto",
          animation: "slideUp 0.3s ease-out",
        }}
      >
        {title && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "1.25rem 1.5rem",
              borderBottom: "1px solid var(--border)",
            }}
          >
            <h2
              style={{
                fontSize: "1.25rem",
                fontWeight: 600,
                margin: 0,
                color: "var(--text)",
              }}
            >
              {title}
            </h2>
            <button
              type="button"
              onClick={onClose}
              style={{
                background: "none",
                border: "none",
                color: "var(--muted)",
                cursor: "pointer",
                fontSize: "1.5rem",
                padding: "0.25rem",
                lineHeight: 1,
                borderRadius: "4px",
                transition: "all 0.2s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "var(--surface2)";
                e.currentTarget.style.color = "var(--text)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "none";
                e.currentTarget.style.color = "var(--muted)";
              }}
            >
              ×
            </button>
          </div>
        )}
        <div style={{ padding: "1.5rem" }}>{children}</div>
      </div>
    </div>
  );
}

interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: "danger" | "warning" | "info";
}

export function ConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = "Растау",
  cancelText = "Болдырмау",
  variant = "danger",
}: ConfirmModalProps) {
  if (!isOpen) return null;

  const variantColors: Record<string, { bg: string; border: string; text: string }> = {
    danger: {
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

  const colors = variantColors[variant];

  const handleConfirm = () => {
    onConfirm();
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} size="sm">
      <div style={{ textAlign: "center" }}>
        <div
          style={{
            fontSize: "3rem",
            marginBottom: "1rem",
          }}
        >
          {variant === "danger" ? "⚠️" : variant === "warning" ? "🔔" : "ℹ️"}
        </div>
        <p
          style={{
            fontSize: "1rem",
            color: "var(--text-secondary)",
            lineHeight: 1.6,
            marginBottom: "1.5rem",
          }}
        >
          {message}
        </p>
        <div
          style={{
            display: "flex",
            gap: "0.75rem",
            justifyContent: "center",
          }}
        >
          <button
            type="button"
            className="btn btn-outline"
            onClick={onClose}
            style={{ flex: 1 }}
          >
            {cancelText}
          </button>
          <button
            type="button"
            className="btn"
            onClick={handleConfirm}
            style={{
              flex: 1,
              background: colors.bg,
              border: `1px solid ${colors.border}`,
              color: colors.text,
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = colors.border;
              e.currentTarget.style.color = "white";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = colors.bg;
              e.currentTarget.style.color = colors.text;
            }}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </Modal>
  );
}
