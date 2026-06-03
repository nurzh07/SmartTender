import { useEffect, useState } from "react";
import { api } from "../api";

interface Report {
  id: number;
  report_type: string;
  period: string;
  file_url: string;
  created_at: string;
}

export function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      const token = localStorage.getItem("access_token");
      const response = await fetch("http://localhost:8000/api/reports/", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      const data = await response.json();
      setReports(data);
    } catch (error) {
      console.error("Error fetching reports:", error);
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async (type: string) => {
    try {
      const token = localStorage.getItem("access_token");
      const period = new Date().toISOString().slice(0, 7);
      const response = await fetch("http://localhost:8000/api/reports/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ report_type: type, period }),
      });
      const data = await response.json();
      alert(`Есеп құрылды: ${data.task_id}`);
      fetchReports();
    } catch (error) {
      console.error("Error generating report:", error);
    }
  };

  if (loading) return <div>Жүктелуде...</div>;

  return (
    <div style={{ padding: "20px" }}>
      <h1>Есептер</h1>
      
      <div style={{ marginBottom: "20px" }}>
        <h3>Жаңа есеп құру</h3>
        <button onClick={() => generateReport("monthly_tenders_pdf")}>
          Айлық тендер PDF
        </button>
        <button onClick={() => generateReport("supplier_ratings_excel")} style={{ marginLeft: "10px" }}>
          Жеткізуші рейтингтері Excel
        </button>
        <button onClick={() => generateReport("budget_analytics")} style={{ marginLeft: "10px" }}>
          Бюджет аналитикасы
        </button>
      </div>

      <h3>Есептер тізімі</h3>
      {reports.length === 0 ? (
        <p>Есептер жоқ</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={{ border: "1px solid #ddd", padding: "8px" }}>ID</th>
              <th style={{ border: "1px solid #ddd", padding: "8px" }}>Түрі</th>
              <th style={{ border: "1px solid #ddd", padding: "8px" }}>Период</th>
              <th style={{ border: "1px solid #ddd", padding: "8px" }}>Құрылған</th>
              <th style={{ border: "1px solid #ddd", padding: "8px" }}>Әрекет</th>
            </tr>
          </thead>
          <tbody>
            {reports.map((report) => (
              <tr key={report.id}>
                <td style={{ border: "1px solid #ddd", padding: "8px" }}>{report.id}</td>
                <td style={{ border: "1px solid #ddd", padding: "8px" }}>{report.report_type}</td>
                <td style={{ border: "1px solid #ddd", padding: "8px" }}>{report.period}</td>
                <td style={{ border: "1px solid #ddd", padding: "8px" }}>
                  {new Date(report.created_at).toLocaleString("kk-KZ")}
                </td>
                <td style={{ border: "1px solid #ddd", padding: "8px" }}>
                  {report.file_url && (
                    <a
                      href={`http://localhost:8000${report.file_url}`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Жүктеу
                    </a>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
