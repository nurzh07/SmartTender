import { useState, useEffect } from "react";
import {
  getMyPermissions,
  checkPermission,
  initializePermissions,
  grantRolePermission,
  revokeRolePermission,
  getRolePermissions,
} from "../api";
import { useAuth } from "../context/AuthContext";

const ROLES = [
  "superadmin",
  "buyer",
  "department_head",
  "employee",
  "supplier",
  "procurement_manager",
];

export function PermissionsPage() {
  const { user } = useAuth();
  const [myPermissions, setMyPermissions] = useState<any[]>([]);
  const [selectedRole, setSelectedRole] = useState<string>("");
  const [rolePermissions, setRolePermissions] = useState<any[]>([]);
  const [allPermissions, setAllPermissions] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [checkPermissionName, setCheckPermissionName] = useState("");
  const [checkResult, setCheckResult] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<"my" | "role" | "check" | "init">("my");

  useEffect(() => {
    loadMyPermissions();
  }, []);

  const loadMyPermissions = async () => {
    try {
      const data = await getMyPermissions();
      setMyPermissions(data.permissions || []);
      if (data.permissions?.length > 0) {
        setAllPermissions(data.permissions.map((p: any) => p.name || p));
      }
    } catch (error) {
      console.error("Failed to load my permissions:", error);
    }
  };

  const loadRolePermissions = async (role: string) => {
    if (!role) return;
    try {
      const data = await getRolePermissions(role);
      setRolePermissions(data.permissions || []);
    } catch (error) {
      console.error("Failed to load role permissions:", error);
    }
  };

  const handleRoleChange = (role: string) => {
    setSelectedRole(role);
    loadRolePermissions(role);
  };

  const handleInitializePermissions = async () => {
    if (!confirm("Барлық рөлдер үшін стандарт құқықтарды инициализациялаңыз. Бұл әрекет қателеседібе?")) return;
    setLoading(true);
    try {
      await initializePermissions();
      alert("Құқықтар инициализацияланды!");
      loadMyPermissions();
    } catch (error) {
      console.error("Failed to initialize permissions:", error);
      alert("Қате орын алды!");
    } finally {
      setLoading(false);
    }
  };

  const handleCheckPermission = async () => {
    if (!checkPermissionName) {
      alert("Құқықтың атын енгізіңіз");
      return;
    }
    try {
      const data = await checkPermission(checkPermissionName);
      setCheckResult(data);
    } catch (error) {
      console.error("Failed to check permission:", error);
      setCheckResult({ has_permission: false, error: "Қате орын алды" });
    }
  };

  const handleGrantPermission = async (permissionName: string) => {
    if (!selectedRole) return;
    try {
      await grantRolePermission(selectedRole, permissionName);
      alert("Құқық берілді!");
      loadRolePermissions(selectedRole);
    } catch (error) {
      console.error("Failed to grant permission:", error);
      alert("Қате орын алды!");
    }
  };

  const handleRevokePermission = async (permissionName: string) => {
    if (!selectedRole) return;
    try {
      await revokeRolePermission(selectedRole, permissionName);
      alert("Құқық алынды!");
      loadRolePermissions(selectedRole);
    } catch (error) {
      console.error("Failed to revoke permission:", error);
      alert("Қате орын алды!");
    }
  };

  const hasPermission = (permissionName: string) => {
    return rolePermissions.some((p) => p.name === permissionName || p === permissionName);
  };

  const getRoleLabel = (role: string) => {
    const labels: Record<string, string> = {
      superadmin: "Әкімші",
      buyer: "Сатып алушы",
      department_head: "Бөлім басшысы",
      employee: "Қызметкер",
      supplier: "Жеткізуші",
      procurement_manager: "Сатып алу менеджері",
    };
    return labels[role] || role;
  };

  return (
    <div className="container-fluid py-4">
      <div className="row mb-4">
        <div className="col-12">
          <h2 className="mb-3">Рөлдік құқықтар</h2>
          <p className="text-muted">Платформадағы рөлдер мен олардың құқықтарын басқару</p>
        </div>
      </div>

      {/* Tabs */}
      <ul className="nav nav-tabs mb-4">
        <li className="nav-item">
          <button
            className={`nav-link ${activeTab === "my" ? "active" : ""}`}
            onClick={() => setActiveTab("my")}
          >
            Менің құқықтарым
          </button>
        </li>
        <li className="nav-item">
          <button
            className={`nav-link ${activeTab === "role" ? "active" : ""}`}
            onClick={() => setActiveTab("role")}
          >
            Рөлдердің құқықтары
          </button>
        </li>
        <li className="nav-item">
          <button
            className={`nav-link ${activeTab === "check" ? "active" : ""}`}
            onClick={() => setActiveTab("check")}
          >
            Құқықты тексеру
          </button>
        </li>
        <li className="nav-item">
          <button
            className={`nav-link ${activeTab === "init" ? "active" : ""}`}
            onClick={() => setActiveTab("init")}
          >
            Инициализация
          </button>
        </li>
      </ul>

      {/* My Permissions Tab */}
      {activeTab === "my" && (
        <div className="card">
          <div className="card-header">
            <h5 className="mb-0">Менің құқықтарым ({user?.role})</h5>
          </div>
          <div className="card-body">
            {myPermissions.length === 0 ? (
              <p className="text-muted mb-0">Құқықтар жоқ</p>
            ) : (
              <div className="row">
                {myPermissions.map((perm, index) => (
                  <div key={index} className="col-md-4 mb-2">
                    <div className="d-flex align-items-center">
                      <span className="badge bg-success me-2">✓</span>
                      <span>{typeof perm === "string" ? perm : perm.name}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Role Permissions Tab */}
      {activeTab === "role" && (
        <div>
          <div className="card mb-4">
            <div className="card-header">
              <h5 className="mb-0">Рөлді таңдау</h5>
            </div>
            <div className="card-body">
              <div className="row">
                <div className="col-md-6">
                  <label className="form-label">Рөл</label>
                  <select
                    className="form-select"
                    value={selectedRole}
                    onChange={(e) => handleRoleChange(e.target.value)}
                  >
                    <option value="">Рөлді таңдаңыз</option>
                    {ROLES.map((role) => (
                      <option key={role} value={role}>
                        {getRoleLabel(role)}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          </div>

          {selectedRole && (
            <div className="card">
              <div className="card-header">
                <h5 className="mb-0">{getRoleLabel(selectedRole)} - құқықтары</h5>
              </div>
              <div className="card-body">
                {rolePermissions.length === 0 ? (
                  <p className="text-muted mb-0">Бұл рөлде құқықтар жоқ</p>
                ) : (
                  <div className="table-responsive">
                    <table className="table">
                      <thead>
                        <tr>
                          <th>Құқықтың аты</th>
                          <th>Сипаттама</th>
                          <th>Әрекет</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rolePermissions.map((perm, index) => {
                          const name = typeof perm === "string" ? perm : perm.name;
                          const description = typeof perm === "string" ? "" : perm.description;
                          return (
                            <tr key={index}>
                              <td>
                                <code>{name}</code>
                              </td>
                              <td>{description || "-"}</td>
                              <td>
                                <button
                                  className="btn btn-sm btn-outline-danger"
                                  onClick={() => handleRevokePermission(name)}
                                >
                                  ❌ Өшіру
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}

                {allPermissions.length > 0 && (
                  <div className="mt-4">
                    <h6>Барлық құқықтардан:</h6>
                    <div className="row">
                      {allPermissions.map((perm, index) => (
                        <div key={index} className="col-md-4 mb-2">
                          <div className="d-flex align-items-center">
                            {hasPermission(perm) ? (
                              <>
                                <span className="badge bg-success me-2">✓</span>
                                <span>{perm}</span>
                              </>
                            ) : (
                              <>
                                <span className="badge bg-secondary me-2">○</span>
                                <span className="text-muted me-2">{perm}</span>
                                <button
                                  className="btn btn-sm btn-outline-primary"
                                  onClick={() => handleGrantPermission(perm)}
                                >
                                  + Беру
                                </button>
                              </>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Check Permission Tab */}
      {activeTab === "check" && (
        <div className="card">
          <div className="card-header">
            <h5 className="mb-0">Құқықты тексеру</h5>
          </div>
          <div className="card-body">
            <div className="row mb-3">
              <div className="col-md-8">
                <label className="form-label">Құқықтың аты</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Мысалы: create_tender"
                  value={checkPermissionName}
                  onChange={(e) => setCheckPermissionName(e.target.value)}
                />
              </div>
              <div className="col-md-4 d-flex align-items-end">
                <button className="btn btn-primary w-100" onClick={handleCheckPermission}>
                  Тексеру
                </button>
              </div>
            </div>

            {checkResult && (
              <div className={`alert ${checkResult.has_permission ? "alert-success" : "alert-danger"}`}>
                <h6>Нәтиже:</h6>
                <p>
                  <strong>Құқық бар ма:</strong> {checkResult.has_permission ? "Иә ✓" : "Жоқ ✗"}
                </p>
                {checkResult.error && (
                  <p className="text-danger">
                    <strong>Қате:</strong> {checkResult.error}
                  </p>
                )}
                {checkResult.message && (
                  <p>
                    <strong>Хабар:</strong> {checkResult.message}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Initialize Tab */}
      {activeTab === "init" && (
        <div className="card">
          <div className="card-header">
            <h5 className="mb-0">Құқықтарды инициализациялау</h5>
          </div>
          <div className="card-body">
            <p className="text-muted mb-3">
              Бұл әрекет барлық рөлдер үшін стандарт құқықтарын қалпына келтіреді. Бұл әрекетті тек бір рет орындау қажет.
            </p>
            <button
              className="btn btn-warning"
              onClick={handleInitializePermissions}
              disabled={loading}
            >
              {loading ? "Жүктелуде..." : "🔄 Құқықтарды инициализациялау"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
