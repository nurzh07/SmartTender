import { useCallback, useEffect, useState } from "react";
import { generateReport, getReports } from "../api";
import { useAuth } from "../context/AuthContext";
import type { Report, ReportType } from "../types";

const REPORT_LABELS: Record<ReportType, string> = {
  monthly_tenders_pdf: "Айлық тендер PDF",
  supplier_ratings_excel: "Жеткізуші рейтингтері Excel",
  budget_analytics: "Бюджет аналитикасы",
};

export function ReportsPage() {
  const { user } = useAuth();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");

  const canGenerate =
    user?.role === "procurement_manager" || user?.role === "superadmin";

  const loadReports = useCallback(async () => {
    try {
      const data = await getReports();
      setReports(Array.isArray(data) ? data : []);
      setError("");
    } catch (e) {
      setReports([]);
      setError(e instanceof Error ? e.message : "Есептерді жүктеу қатесі");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadReports();
  }, [loadReports]);

  const handleGenerate = async (type: ReportType) => {
    setBusy(true);
    setError("");
    setMsg("");
    const period = new Date().toISOString().slice(0, 7);
    try {
      const result = await generateReport(type, period);
      setMsg(`Есеп фонда құрылуда (task: ${result.task_id.slice(0, 8)}…)`);
      // Celery тапсырмасы аяқталғанша бірнеше рет жаңарту
      for (const delay of [2000, 3000, 5000]) {
        await new Promise((r) => setTimeout(r, delay));
        await loadReports();
      }
      setMsg("Есеп тізімі жаңартылды");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Есеп құру қатесі");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <h1 className="page-title">Есептер</h1>
      <p className="page-sub">PDF, Excel және бюджет аналитикасы (Celery фонда)</p>

      {canGenerate ? (
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h2 style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>Жаңа есеп құру</h2>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
            {(Object.keys(REPORT_LABELS) as ReportType[]).map((type) => (
              <button
                key={type}
                type="button"
                className="btn btn-primary"
                disabled={busy}
                onClick={() => handleGenerate(type)}
              >
                {REPORT_LABELS[type]}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <p style={{ color: "var(--muted)" }}>
            Есеп құру тек сатып алу менеджері немесе әкімші рөлі үшін қолжетімді.
          </p>
        </div>
      )}

      {msg && <p style={{ color: "var(--success)", marginBottom: "1rem" }}>{msg}</p>}
      {error && <p className="error-msg">{error}</p>}

      <div className="card">
        <h2 style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>Есептер тізімі</h2>
        {loading && <p style={{ color: "var(--muted)" }}>Жүктелуде...</p>}
        {!loading && reports.length === 0 && (
          <p style={{ color: "var(--muted)" }}>Есептер жоқ. Жаңа есеп құрыңыз.</p>
        )}
        {!loading &&
          reports.map((report) => (
            <div
              key={report.id}
              style={{
                padding: "0.85rem",
                borderBottom: "1px solid var(--border)",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: "1rem",
              }}
            >
              <div>
                <strong>{REPORT_LABELS[report.report_type] || report.report_type}</strong>
                <div style={{ color: "var(--muted)", fontSize: "0.85rem", marginTop: "0.25rem" }}>
                  Период: {report.period} ·{" "}
                  {new Date(report.created_at).toLocaleString("kk-KZ")}
                </div>
              </div>
              {report.file_url ? (
                <a
                  href={report.file_url}
                  className="btn btn-secondary"
                  style={{ textDecoration: "none", fontSize: "0.85rem" }}
                  download
                >
                  Жүктеу
                </a>
              ) : (
                <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>Файл жоқ</span>
              )}
            </div>
          ))}
      </div>
    </div>
  );
}
