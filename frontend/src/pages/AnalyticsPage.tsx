import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { getBuyerDashboard, getSupplierDashboard, getAdminDashboard, getTopSuppliers } from "../api";
import type { BuyerDashboard, SupplierDashboard, AdminDashboard, TopSupplier } from "../types";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from "chart.js";
import { Bar, Pie } from "react-chartjs-2";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

export function AnalyticsPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [buyerData, setBuyerData] = useState<BuyerDashboard | null>(null);
  const [supplierData, setSupplierData] = useState<SupplierDashboard | null>(null);
  const [adminData, setAdminData] = useState<AdminDashboard | null>(null);
  const [topSuppliers, setTopSuppliers] = useState<TopSupplier[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        if (user?.role === "buyer" || user?.role === "superadmin") {
          const data = await getBuyerDashboard();
          setBuyerData(data);
        }
        if (user?.role === "supplier" || user?.role === "superadmin") {
          const data = await getSupplierDashboard();
          setSupplierData(data);
        }
        if (user?.role === "superadmin") {
          const data = await getAdminDashboard();
          setAdminData(data);
          const suppliers = await getTopSuppliers();
          setTopSuppliers(suppliers);
        }
      } catch (e) {
        console.error("Analytics fetch error:", e);
      } finally {
        setLoading(false);
      }
    };

    if (user) {
      fetchData();
    }
  }, [user]);

  if (loading) {
    return <div style={{ padding: "2rem" }}>Жүктелуде...</div>;
  }

  if (!user) return null;

  return (
    <div>
      <h1 className="page-title">Аналитика</h1>

      {/* Buyer Dashboard */}
      {(user.role === "buyer" || user.role === "superadmin") && buyerData && (
        <div style={{ marginBottom: "2rem" }}>
          <h2 className="section-title" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            🛒 BUYER аналитикасы
          </h2>
          <div className="grid-3">
            <div className="card" style={{
              background: "linear-gradient(135deg, var(--surface) 0%, rgba(59, 130, 246, 0.1) 100%)",
              borderLeft: "4px solid var(--accent)"
            }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                <div className="stat-label">Айдағы тендерлер</div>
                <span style={{ fontSize: "1.5rem" }}>📊</span>
              </div>
              <div className="stat-value" style={{ color: "var(--accent)" }}>{buyerData.total_tenders_this_month}</div>
            </div>
            <div className="card" style={{
              background: "linear-gradient(135deg, var(--surface) 0%, rgba(16, 185, 129, 0.1) 100%)",
              borderLeft: "4px solid var(--success)"
            }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                <div className="stat-label">Жұмсалған бюджет</div>
                <span style={{ fontSize: "1.5rem" }}>💰</span>
              </div>
              <div className="stat-value" style={{ color: "var(--success)" }}>{buyerData.total_budget_awarded.toLocaleString()} ₸</div>
            </div>
            <div className="card" style={{
              background: "linear-gradient(135deg, var(--surface) 0%, rgba(245, 158, 11, 0.1) 100%)",
              borderLeft: "4px solid var(--warning)"
            }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                <div className="stat-label">Орташа ұсыныс саны</div>
                <span style={{ fontSize: "1.5rem" }}>📝</span>
              </div>
              <div className="stat-value" style={{ color: "var(--warning)" }}>{buyerData.avg_proposals_per_tender.toFixed(1)}</div>
            </div>
          </div>

          <div className="card" style={{ marginTop: "1rem" }}>
            <h3 className="section-title" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              📈 Айлық белсенділік
            </h3>
            <div style={{ height: "300px" }}>
              <Bar
                data={{
                  labels: buyerData.monthly_activity.map((d) => d.month_label),
                  datasets: [{
                    label: "Тендерлер саны",
                    data: buyerData.monthly_activity.map((d) => d.count),
                    backgroundColor: "rgba(59, 130, 246, 0.8)",
                    borderRadius: 6,
                    borderSkipped: false,
                  }],
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      display: false
                    }
                  },
                  scales: {
                    y: {
                      beginAtZero: true,
                      grid: {
                        color: "rgba(45, 63, 86, 0.3)"
                      },
                      ticks: {
                        color: "var(--muted)"
                      }
                    },
                    x: {
                      grid: {
                        display: false
                      },
                      ticks: {
                        color: "var(--muted)"
                      }
                    }
                  }
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Supplier Dashboard */}
      {(user.role === "supplier" || user.role === "superadmin") && supplierData && (
        <div style={{ marginBottom: "2rem" }}>
          <h2 className="section-title" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            🚚 SUPPLIER аналитикасы
          </h2>
          <div className="grid-3">
            <div className="card" style={{
              background: "linear-gradient(135deg, var(--surface) 0%, rgba(59, 130, 246, 0.1) 100%)",
              borderLeft: "4px solid var(--accent)"
            }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                <div className="stat-label">Барлық ұсыныстар</div>
                <span style={{ fontSize: "1.5rem" }}>📝</span>
              </div>
              <div className="stat-value" style={{ color: "var(--accent)" }}>{supplierData.total_proposals}</div>
            </div>
            <div className="card" style={{
              background: "linear-gradient(135deg, var(--surface) 0%, rgba(16, 185, 129, 0.1) 100%)",
              borderLeft: "4px solid var(--success)"
            }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                <div className="stat-label">Жеңімпаздық пайызы</div>
                <span style={{ fontSize: "1.5rem" }}>🏆</span>
              </div>
              <div className="stat-value" style={{ color: supplierData.win_rate > 50 ? "var(--success)" : "var(--warning)" }}>
                {supplierData.win_rate.toFixed(1)}%
              </div>
            </div>
            <div className="card" style={{
              background: "linear-gradient(135deg, var(--surface) 0%, rgba(245, 158, 11, 0.1) 100%)",
              borderLeft: "4px solid var(--warning)"
            }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                <div className="stat-label">Орташа баға</div>
                <span style={{ fontSize: "1.5rem" }}>💵</span>
              </div>
              <div className="stat-value" style={{ color: "var(--warning)" }}>{supplierData.avg_own_price.toLocaleString()} ₸</div>
            </div>
          </div>

          <div className="card" style={{ marginTop: "1rem" }}>
            <h3 className="section-title" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              ⚖️ Жеңістер/Жеңілістер
            </h3>
            <div style={{ height: "300px", maxWidth: "400px", margin: "0 auto" }}>
              <Pie
                data={{
                  labels: supplierData.wins_losses.map((d) => d.label),
                  datasets: [{
                    data: supplierData.wins_losses.map((d) => d.count),
                    backgroundColor: ["rgba(16, 185, 129, 0.8)", "rgba(239, 68, 68, 0.8)"],
                    borderColor: ["rgba(16, 185, 129, 1)", "rgba(239, 68, 68, 1)"],
                    borderWidth: 2,
                  }],
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: "bottom",
                      labels: {
                        color: "var(--text)",
                        padding: 20,
                        font: {
                          size: 12
                        }
                      }
                    }
                  }
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Admin Dashboard */}
      {user.role === "superadmin" && adminData && (
        <div style={{ marginBottom: "2rem" }}>
          <h2 className="section-title" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            👑 SUPERADMIN аналитикасы
          </h2>
          <div className="grid-3">
            <div className="card" style={{
              background: "linear-gradient(135deg, var(--surface) 0%, rgba(59, 130, 246, 0.1) 100%)",
              borderLeft: "4px solid var(--accent)"
            }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                <div className="stat-label">Барлық пайдаланушылар</div>
                <span style={{ fontSize: "1.5rem" }}>👥</span>
              </div>
              <div className="stat-value" style={{ color: "var(--accent)" }}>{adminData.total_users}</div>
            </div>
            <div className="card" style={{
              background: "linear-gradient(135deg, var(--surface) 0%, rgba(16, 185, 129, 0.1) 100%)",
              borderLeft: "4px solid var(--success)"
            }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                <div className="stat-label">Барлық тендерлер</div>
                <span style={{ fontSize: "1.5rem" }}>📋</span>
              </div>
              <div className="stat-value" style={{ color: "var(--success)" }}>{adminData.total_tenders}</div>
            </div>
            <div className="card" style={{
              background: "linear-gradient(135deg, var(--surface) 0%, rgba(245, 158, 11, 0.1) 100%)",
              borderLeft: "4px solid var(--warning)"
            }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                <div className="stat-label">Айналым көлемі</div>
                <span style={{ fontSize: "1.5rem" }}>💰</span>
              </div>
              <div className="stat-value" style={{ color: "var(--warning)" }}>{adminData.total_transaction_volume.toLocaleString()} ₸</div>
            </div>
          </div>

          <div className="card" style={{ marginTop: "1rem" }}>
            <h3 className="section-title" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              🏆 TOP 10 Жеткізушілер
            </h3>
            <div style={{ marginTop: "1rem" }}>
              {topSuppliers.map((s, index) => (
                <div key={s.supplier_id} style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "1rem",
                  borderBottom: "1px solid var(--border)",
                  alignItems: "center",
                  background: index < 3 ? "var(--surface2)" : "transparent",
                  borderRadius: "var(--radius-sm)",
                  marginBottom: "0.25rem"
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                    <div style={{
                      width: "32px",
                      height: "32px",
                      borderRadius: "50%",
                      background: index === 0 ? "var(--warning)" : 
                                 index === 1 ? "var(--muted)" : 
                                 index === 2 ? "var(--accent)" : "var(--surface3)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontWeight: "bold",
                      fontSize: "0.85rem",
                      color: "white"
                    }}>
                      {index + 1}
                    </div>
                    <div>
                      <div style={{ fontWeight: "600", fontSize: "0.95rem" }}>{s.supplier_name}</div>
                      <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>{s.supplier_email}</div>
                    </div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ 
                      fontWeight: "bold", 
                      color: s.win_rate > 50 ? "var(--success)" : "var(--warning)",
                      fontSize: "0.95rem"
                    }}>
                      {s.win_rate.toFixed(1)}% жеңімпаздық
                    </div>
                    <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
                      {s.wins}/{s.total_proposals} жеңістер
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
