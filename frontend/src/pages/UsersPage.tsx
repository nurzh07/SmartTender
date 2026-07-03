import { useEffect, useState } from "react";
import { getUsers, updateUser, deleteUser } from "../api";
import { RoleBanner } from "../components/RoleBanner";
import { ConfirmModal } from "../components/Modal";
import { useAuth } from "../context/AuthContext";
import type { User, UserRole } from "../types";

const ROLE_LABELS: Record<UserRole, string> = {
  superadmin: "Әкімші",
  buyer: "Buyer",
  department_head: "Бөлім басшысы",
  employee: "Қызметкер",
  procurement_manager: "Сатып алу менеджері",
  supplier: "Жеткізуші",
};

export function UsersPage() {
  const { user } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [userToDelete, setUserToDelete] = useState<User | null>(null);

  const load = () => {
    setLoading(true);
    getUsers()
      .then(setUsers)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  if (user?.role !== "superadmin") {
    return <p className="error-msg">Тек әкімші көре алады.</p>;
  }

  const toggleActive = async (u: User) => {
    setMsg("");
    setError("");
    try {
      await updateUser(u.id, { is_active: !u.is_active });
      setMsg(`${u.email} — ${u.is_active ? "блокталды" : "белсендірілді"}`);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Қате");
    }
  };

  const handleDeleteClick = (u: User) => {
    setUserToDelete(u);
    setDeleteModalOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!userToDelete) return;
    setMsg("");
    setError("");
    try {
      await deleteUser(userToDelete.id);
      setMsg(`${userToDelete.email} жойылды`);
      setDeleteModalOpen(false);
      setUserToDelete(null);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Қате");
    }
  };

  return (
    <div>
      <h1 className="page-title">Пайдаланушылар</h1>
      <p className="page-sub">Блоктау, рөлдер мен статус</p>
      <RoleBanner role="superadmin" />

      {msg && <p style={{ color: "var(--success)", marginBottom: "1rem" }}>{msg}</p>}
      {error && <p className="error-msg">{error}</p>}
      {loading && <p style={{ color: "var(--muted)" }}>Жүктелуде...</p>}

      <div className="card" style={{ marginTop: "1rem" }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Email</th>
              <th>Аты</th>
              <th>Рөл</th>
              <th>Email расталған</th>
              <th>Статус</th>
              <th>Әрекет</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.email}</td>
                <td>{u.full_name || "—"}</td>
                <td>
                  <span className="badge badge-published">{ROLE_LABELS[u.role]}</span>
                </td>
                <td>{u.is_verified ? "✓" : "—"}</td>
                <td>
                  <span className={`badge badge-${u.is_active ? "awarded" : "closed"}`}>
                    {u.is_active ? "белсенді" : "блок"}
                  </span>
                </td>
                <td>
                  {u.id !== user.id && (
                    <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                      <button
                        type="button"
                        className={`btn btn-sm ${u.is_active ? "btn-danger" : "btn-success"}`}
                        onClick={() => toggleActive(u)}
                        style={{ minWidth: "100px" }}
                      >
                        {u.is_active ? "Блоктау" : "Белсендіру"}
                      </button>
                      <button
                        type="button"
                        className="btn btn-sm"
                        onClick={() => handleDeleteClick(u)}
                        style={{
                          minWidth: "80px",
                          background: "var(--danger)",
                          color: "white",
                          border: "1px solid var(--danger)"
                        }}
                      >
                        🗑️ Жою
                      </button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!loading && users.length === 0 && (
          <p className="empty-text">Пайдаланушылар жоқ</p>
        )}
      </div>

      <ConfirmModal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        onConfirm={handleDeleteConfirm}
        title="Аккаунтты жою"
        message={`${userToDelete?.email} пайдаланушысын жойғыңыз келетіне сенімдісіз бе? Бұл әрекет қайтарылмайды.`}
        confirmText="Жою"
        cancelText="Болдырмау"
        variant="danger"
      />
    </div>
  );
}
