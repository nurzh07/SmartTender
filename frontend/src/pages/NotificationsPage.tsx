import { useEffect, useState } from "react";
import { getNotifications, markNotificationRead } from "../api";
import type { Notification } from "../types";

export function NotificationsPage() {
  const [items, setItems] = useState<Notification[]>([]);

  useEffect(() => {
    getNotifications().then(setItems).catch(() => setItems([]));
  }, []);

  return (
    <div>
      <h1 className="page-title">Хабарламалар</h1>
      <p className="page-sub">Email, Telegram және жүйелік хабарламалар</p>

      <div className="card">
        {items.map((n) => (
          <div
            key={n.id}
            style={{
              padding: "1rem",
              borderBottom: "1px solid var(--border)",
              opacity: n.is_read ? 0.7 : 1,
            }}
          >
            <div style={{ fontSize: "0.75rem", color: "var(--muted)" }}>
              {n.type} · {new Date(n.sent_at).toLocaleString("kk-KZ")}
            </div>
            <p style={{ marginTop: "0.35rem" }}>{n.message}</p>
            {!n.is_read && (
              <button
                type="button"
                className="btn btn-secondary"
                style={{ marginTop: "0.5rem", fontSize: "0.8rem" }}
                onClick={async () => {
                  await markNotificationRead(n.id);
                  setItems((prev) =>
                    prev.map((x) => (x.id === n.id ? { ...x, is_read: true } : x))
                  );
                }}
              >
                Оқылды деп белгілеу
              </button>
            )}
          </div>
        ))}
        {items.length === 0 && (
          <p style={{ color: "var(--muted)", padding: "1rem" }}>Хабарламалар жоқ</p>
        )}
      </div>
    </div>
  );
}
