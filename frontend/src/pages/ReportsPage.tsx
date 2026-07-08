import { useCallback, useEffect, useState } from "react";
import { generateReport, getReports, downloadReport } from "../api";
import { useAuth } from "../context/AuthContext";
import type { Report, ReportType } from "../types";

const REPORT_LABELS: Record<ReportType, string> = {
  monthly_tender_pdf: "Айлық тендер PDF",
  supplier_ratings_excel: "Жеткізуші рейтингтері Excel",
  budget_analytics: "Бюджет аналитикасы",
  tender_summary: "Тендер қорытамасы",
  supplier_performance: "Жеткізуші өнімділігі",
  procurement_report: "Сатып алу есебі",
};

export function ReportsPage() {
  const { user } = useAuth();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [downloading, setDownloading] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");

  const canGenerate =
    user?.role === "buyer" || user?.role === "superadmin" || user?.role === "procurement_manager";

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
    try {
      await generateReport(type);
      setMsg("Есеп фонда құрылуда...");
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

  const handleDownload = async (report: Report) => {
    if (report.status !== "completed") {
      setMsg("Есеп әлі дайын емес");
      return;
    }
    setDownloading(report.id);
    try {
      await downloadReport(report.id);
      setMsg("Есеп сәтті жүктелді");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Жүктеу қатесі");
    } finally {
      setDownloading(null);
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "pending": return "Күтуде";
      case "generating": return "Құрылуда";
      case "completed": return "Дайын";
      case "failed": return "Қате";
      default: return status;
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
            {(Object.keys(REPORT_LABELS) as ReportType[])
              .filter(t => ["monthly_tender_pdf", "supplier_ratings_excel", "budget_analytics"].includes(t))
              .map((type) => (
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
                <strong>{report.title || REPORT_LABELS[report.type] || report.type}</strong>
                <div style={{ color: "var(--muted)", fontSize: "0.85rem", marginTop: "0.25rem" }}>
                  Статус: {getStatusText(report.status)} ·{" "}
                  {new Date(report.created_at).toLocaleString("kk-KZ")}
                </div>
              </div>
              {report.status === "completed" ? (
                <button
                  onClick={() => handleDownload(report)}
                  disabled={downloading === report.id}
                  className="btn btn-secondary"
                  style={{ fontSize: "0.85rem" }}
                >
                  {downloading === report.id ? "Жүктелуде..." : "Жүктеу"}
                </button>
              ) : (
                <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
                  {getStatusText(report.status)}
                </span>
              )}
            </div>
          ))}
      </div>
    </div>
  );
}
