import { useEffect, useRef, useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Bar, Doughnut } from "react-chartjs-2";
import { useAuth } from "../context/AuthContext";
import {
  getAdminDashboard,
  getBuyerDashboard,
  getSupplierDashboard,
} from "../api";
import type {
  AdminDashboard,
  BuyerDashboard,
  MonthlyBar,
  StatusPie,
  SupplierDashboard,
  TopSupplier,
} from "../types";

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend);

// ── Chart helpers ────────────────────────────────────────────

const BAR_OPTS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    x: { grid: { color: "rgba(255,255,255,0.06)" }, ticks: { color: "#8b9cb3" } },
    y: { grid: { color: "rgba(255,255,255,0.06)" }, ticks: { color: "#8b9cb3" } },
  },
};

const DONUT_OPTS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: "bottom" as const,
      labels: { color: "#8b9cb3", padding: 12, font: { size: 12 } },
    },
  },
};

const PIE_COLORS = [
  "#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#a855f7", "#06b6d4",
];

function monthlyBarData(data: MonthlyBar[]) {
  return {
    labels: data.map((d) => d.month_label),
    datasets: [
      {
        label: "Тендерлер",
        data: data.map((d) => d.count),
        backgroundColor: "rgba(59, 130, 246, 0.7)",
        borderColor: "#3b82f6",
        borderWidth: 1,
        borderRadius: 6,
      },
    ],
  };
}

function pieData(items: StatusPie[]) {
  return {
    labels: items.map((i) => i.label),
    datasets: [
      {
        data: items.map((i) => i.count),
        backgroundColor: PIE_COLORS,
        borderColor: "#1a2332",
        borderWidth: 2,
      },
    ],
  };
}

// ── Stat card ────────────────────────────────────────────────

function StatCard({
  label,
  value,
  sub,
  color = "var(--accent)",
  icon,
}: {
  label: string;
  value: string | number;
  sub?: string;
  color?: string;
  icon?: string;
}) {
  return (
    <div
      className="card stat-card"
      style={{ position: "relative", overflow: "hidden" }}
    >
      <div style={{ position: "absolute", top: 14, right: 16, fontSize: 28, opacity: 0.2 }}>
        {icon}
      </div>
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={{ color, fontSize: "1.9rem" }}>
        {value}
      </div>
      {sub && (
        <div style={{ fontSize: "0.8rem", color: "var(--muted)", marginTop: 4 }}>{sub}</div>
      )}
    </div>
  );
}

// ── Section card ─────────────────────────────────────────────

function ChartCard({
  title,
  height = 240,
  children,
}: {
  title: string;
  height?: number;
  children: React.ReactNode;
}) {
  return (
    <div className="card" style={{ padding: "1.25rem" }}>
      <div
        className="section-title"
        style={{ marginBottom: "1rem", fontSize: "1rem", fontWeight: 600 }}
      >
        {title}
      </div>
      <div style={{ height }}>{children}</div>
    </div>
  );
}

// ── Suppliers table ───────────────────────────────────────────

function SuppliersTable({ suppliers }: { suppliers: TopSupplier[] }) {
  if (!suppliers.length) return <p className="empty-text">Мәлімет жоқ.</p>;
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>#</th>
          <th>Жеткізуші</th>
          <th>Ұсыныстар</th>
          <th>Жеңімпаз</th>
          <th>Win Rate</th>
        </tr>
      </thead>
      <tbody>
        {suppliers.map((s, i) => (
          <tr key={s.supplier_id}>
            <td style={{ color: "var(--muted)" }}>{i + 1}</td>
            <td>
              <div style={{ fontWeight: 600 }}>{s.supplier_name}</div>
              <div style={{ fontSize: "0.78rem", color: "var(--muted)" }}>{s.supplier_email}</div>
            </td>
            <td>{s.total_proposals}</td>
            <td style={{ color: "var(--success)" }}>{s.wins}</td>
            <td>
              <span
                style={{
                  background:
                    s.win_rate >= 50
                      ? "rgba(34,197,94,0.15)"
                      : "rgba(239,68,68,0.15)",
                  color: s.win_rate >= 50 ? "var(--success)" : "var(--danger)",
                  padding: "2px 8px",
                  borderRadius: 6,
                  fontWeight: 700,
                  fontSize: "0.85rem",
                }}
              >
                {s.win_rate}%
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// ═══════════════════════════════════════════════════════════════
// BUYER DASHBOARD
// ═══════════════════════════════════════════════════════════════

function BuyerAnalytics() {
  const [data, setData] = useState<BuyerDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getBuyerDashboard()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading)
    return (
      <div style={{ textAlign: "center", padding: "4rem", color: "var(--muted)" }}>
        📊 Деректер жүктелуде...
      </div>
    );
  if (error)
    return (
      <div className="card" style={{ color: "var(--danger)", padding: "1.5rem" }}>
        ⚠️ {error}
      </div>
    );
  if (!data) return null;

  const change = data.total_tenders_this_month - data.total_tenders_last_month;
  const changeSub = `${change >= 0 ? "+" : ""}${change} өткен айға қарағанда`;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div className="grid-3">
        <StatCard
          label="Тендерлер (бұл ай)"
          value={data.total_tenders_this_month}
          sub={changeSub}
          color={change >= 0 ? "var(--success)" : "var(--danger)"}
          icon="📋"
        />
        <StatCard
          label="Жалпы бюджет (жеңімпаз)"
          value={`${(data.total_budget_awarded / 1_000_000).toFixed(1)}M ₸`}
          icon="💰"
        />
        <StatCard
          label="Орт. ұсыныс / тендер"
          value={data.avg_proposals_per_tender.toFixed(1)}
          icon="📨"
        />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
        <ChartCard title="📅 Ай сайынғы белсенділік (соңғы 6 ай)">
          <Bar data={monthlyBarData(data.monthly_activity)} options={BAR_OPTS} />
        </ChartCard>
        <ChartCard title="🥧 Тендер статустары">
          <Doughnut data={pieData(data.status_distribution)} options={DONUT_OPTS} />
        </ChartCard>
      </div>

      <div className="card">
        <div className="section-title" style={{ marginBottom: "1rem" }}>
          🏆 Үздік жеткізушілер (жеңу деңгейі бойынша)
        </div>
        <SuppliersTable suppliers={data.top_suppliers} />
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// SUPPLIER DASHBOARD
// ═══════════════════════════════════════════════════════════════

function SupplierAnalytics() {
  const [data, setData] = useState<SupplierDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getSupplierDashboard()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading)
    return (
      <div style={{ textAlign: "center", padding: "4rem", color: "var(--muted)" }}>
        📊 Деректер жүктелуде...
      </div>
    );
  if (error)
    return (
      <div className="card" style={{ color: "var(--danger)", padding: "1.5rem" }}>
        ⚠️ {error}
      </div>
    );
  if (!data) return null;

  const priceDiff = data.avg_market_price
    ? (((data.avg_own_price - data.avg_market_price) / data.avg_market_price) * 100).toFixed(1)
    : "0";
  const priceDiffNum = parseFloat(priceDiff);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div className="grid-3">
        <StatCard label="Жалпы ұсыныстар" value={data.total_proposals} icon="📨" />
        <StatCard
          label="Жеңу деңгейі"
          value={`${data.win_rate}%`}
          color={data.win_rate >= 30 ? "var(--success)" : "var(--warning)"}
          icon="🏆"
        />
        <StatCard
          label="Орт. баға — нарықпен"
          value={`${priceDiffNum >= 0 ? "+" : ""}${priceDiff}%`}
          color={priceDiffNum <= 0 ? "var(--success)" : "var(--danger)"}
          sub={`Сіз: ${(data.avg_own_price / 1000).toFixed(0)}K ₸ · Нарық: ${(data.avg_market_price / 1000).toFixed(0)}K ₸`}
          icon="📊"
        />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
        <ChartCard title="📅 Ай сайынғы қатысу (соңғы 6 ай)">
          <Bar data={monthlyBarData(data.monthly_activity)} options={BAR_OPTS} />
        </ChartCard>
        <ChartCard title="🥧 Жеңілді / Жеңілмеді">
          <Doughnut data={pieData(data.wins_losses)} options={DONUT_OPTS} />
        </ChartCard>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// ADMIN DASHBOARD
// ═══════════════════════════════════════════════════════════════

function AdminAnalytics() {
  const [data, setData] = useState<AdminDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getAdminDashboard()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading)
    return (
      <div style={{ textAlign: "center", padding: "4rem", color: "var(--muted)" }}>
        📊 Деректер жүктелуде...
      </div>
    );
  if (error)
    return (
      <div className="card" style={{ color: "var(--danger)", padding: "1.5rem" }}>
        ⚠️ {error}
      </div>
    );
  if (!data) return null;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* KPI cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: "1rem" }}>
        <StatCard label="Жалпы пайдаланушылар" value={data.total_users} icon="👥" />
        <StatCard label="Сатып алушылар" value={data.total_buyers} color="var(--accent)" icon="🏢" />
        <StatCard label="Жеткізушілер" value={data.total_suppliers} color="var(--success)" icon="🚛" />
        <StatCard label="Жалпы тендерлер" value={data.total_tenders} icon="📋" />
        <StatCard
          label="Жалпы транзакция"
          value={`${(data.total_transaction_volume / 1_000_000).toFixed(1)}M ₸`}
          color="var(--warning)"
          icon="💳"
        />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "1.5rem" }}>
        <ChartCard title="📅 Платформа белсенділігі (соңғы 6 ай)" height={260}>
          <Bar data={monthlyBarData(data.monthly_activity)} options={BAR_OPTS} />
        </ChartCard>
        <ChartCard title="🥧 Тендер статустары" height={260}>
          <Doughnut data={pieData(data.status_distribution)} options={DONUT_OPTS} />
        </ChartCard>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
        <div className="card">
          <div className="section-title" style={{ marginBottom: "1rem" }}>
            🏆 Үздік жеткізушілер (Top 10)
          </div>
          <SuppliersTable suppliers={data.top_suppliers} />
        </div>

        <div className="card">
          <div className="section-title" style={{ marginBottom: "1rem" }}>
            🏢 Белсенді сатып алушылар (Top 10)
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Сатып алушы</th>
                <th>Тендерлер</th>
                <th>Бюджет</th>
              </tr>
            </thead>
            <tbody>
              {data.top_buyers.map((b, i) => (
                <tr key={b.buyer_id}>
                  <td style={{ color: "var(--muted)" }}>{i + 1}</td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{b.buyer_name}</div>
                    <div style={{ fontSize: "0.78rem", color: "var(--muted)" }}>{b.buyer_email}</div>
                  </td>
                  <td>{b.total_tenders}</td>
                  <td style={{ color: "var(--warning)" }}>
                    {(b.total_budget / 1_000_000).toFixed(1)}M ₸
                  </td>
                </tr>
              ))}
              {!data.top_buyers.length && (
                <tr>
                  <td colSpan={4} style={{ color: "var(--muted)" }}>
                    Мәлімет жоқ
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// MAIN PAGE
// ═══════════════════════════════════════════════════════════════

type Tab = "buyer" | "supplier" | "admin";

export function AnalyticsDashboard() {
  const { user } = useAuth();
  const role = user?.role;

  const [tab, setTab] = useState<Tab>(() => {
    if (role === "superadmin") return "admin";
    if (role === "supplier") return "supplier";
    return "buyer";
  });

  const tabs: { id: Tab; label: string; icon: string; roles: string[] }[] = [
    { id: "buyer", label: "Сатып алушы", icon: "🏢", roles: ["buyer", "superadmin"] },
    { id: "supplier", label: "Жеткізуші", icon: "🚛", roles: ["supplier", "superadmin"] },
    { id: "admin", label: "Админ", icon: "⚙️", roles: ["superadmin"] },
  ];

  const visibleTabs = tabs.filter((t) => role && t.roles.includes(role));

  return (
    <div>
      <h1 className="page-title">📊 Аналитика дашборды</h1>
      <p className="page-sub" style={{ marginBottom: "1.5rem" }}>
        Нақты уақыттағы аналитика (Redis кэш · 1 сағ TTL)
      </p>

      {/* Tab switcher */}
      {visibleTabs.length > 1 && (
        <div
          style={{
            display: "flex",
            gap: "0.5rem",
            marginBottom: "1.75rem",
            background: "var(--surface)",
            padding: "4px",
            borderRadius: 12,
            border: "1px solid var(--border)",
            width: "fit-content",
          }}
        >
          {visibleTabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              style={{
                padding: "0.5rem 1.1rem",
                borderRadius: 9,
                border: "none",
                cursor: "pointer",
                fontWeight: 600,
                fontSize: "0.9rem",
                transition: "all 0.15s",
                background: tab === t.id ? "var(--accent)" : "transparent",
                color: tab === t.id ? "white" : "var(--muted)",
              }}
            >
              {t.icon} {t.label}
            </button>
          ))}
        </div>
      )}

      {tab === "buyer" && <BuyerAnalytics />}
      {tab === "supplier" && <SupplierAnalytics />}
      {tab === "admin" && <AdminAnalytics />}
    </div>
  );
}
