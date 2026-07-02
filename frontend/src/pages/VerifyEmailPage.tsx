import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { verifyEmail } from "../api";

export function VerifyEmailPage() {
  const [params] = useSearchParams();
  const token = params.get("token") || "";
  const [message, setMessage] = useState("Email расталуда...");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) {
      setError("Растау токені жоқ");
      return;
    }
    verifyEmail(token)
      .then((user) => {
        setMessage(`Email сәтті расталды: ${user.email}`);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Растау сәтсіз");
      });
  }, [token]);

  return (
    <div className="login-page">
      <div className="card login-card">
        <h1>Email растау</h1>
        {error ? <p className="error-msg">{error}</p> : <p style={{ color: "var(--success)" }}>{message}</p>}
        <Link to="/login" className="btn btn-primary" style={{ display: "inline-block", marginTop: "1rem" }}>
          Кіру
        </Link>
      </div>
    </div>
  );
}
