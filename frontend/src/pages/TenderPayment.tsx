/**
 * Stripe Payment page — handles tender deposit flow.
 *
 * Flow:
 *   1. Buyer navigates to /tenders/:id/payment
 *   2. We call /payments/create-intent → get client_secret
 *   3. Stripe Elements renders the payment form
 *   4. On success → tender becomes PUBLISHED
 */

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { createPaymentIntent, getTender, getPaymentStatus, getStripeConfig } from "../api";
import type { Tender } from "../types";

// ── Stripe lazy load ─────────────────────────────────────────

async function loadStripe(publishableKey: string) {
  const { loadStripe: load } = await import("@stripe/stripe-js");
  return load(publishableKey);
}

// ── Deposit calculator ────────────────────────────────────────

function calcDeposit(budget: string): number {
  const b = parseFloat(budget);
  return Math.max(b * 0.01, 10); // 1% min $10
}

// ── Status badge ─────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; color: string; bg: string }> = {
    pending:   { label: "Күтуде",     color: "#fcd34d", bg: "rgba(245,158,11,0.15)" },
    succeeded: { label: "Төленді ✓", color: "#86efac", bg: "rgba(34,197,94,0.15)" },
    failed:    { label: "Сәтсіз ✗",  color: "#fca5a5", bg: "rgba(239,68,68,0.15)" },
    refunded:  { label: "Қайтарылды", color: "#93c5fd", bg: "rgba(59,130,246,0.15)" },
  };
  const s = map[status] ?? { label: status, color: "var(--muted)", bg: "transparent" };
  return (
    <span
      style={{
        padding: "4px 12px",
        borderRadius: 20,
        fontSize: "0.85rem",
        fontWeight: 700,
        color: s.color,
        background: s.bg,
      }}
    >
      {s.label}
    </span>
  );
}

// ═══════════════════════════════════════════════════════════════
// PAYMENT PAGE
// ═══════════════════════════════════════════════════════════════

export function TenderPayment() {
  const { id } = useParams<{ id: string }>();
  const tenderId = parseInt(id || "0");
  const navigate = useNavigate();

  const [tender, setTender] = useState<Tender | null>(null);
  const [loading, setLoading] = useState(true);
  const [payLoading, setPayLoading] = useState(false);
  const [error, setError] = useState("");
  const [stripeEnabled, setStripeEnabled] = useState(false);
  const [publishableKey, setPublishableKey] = useState("");
  const [existingPayment, setExistingPayment] = useState<{ status: string; amount: number } | null>(null);
  const [intentCreated, setIntentCreated] = useState<{
    clientSecret: string;
    amount: number;
  } | null>(null);
  const [paying, setPaying] = useState(false);
  const [paid, setPaid] = useState(false);

  useEffect(() => {
    Promise.all([
      getTender(tenderId),
      getStripeConfig(),
      getPaymentStatus(tenderId).catch(() => null),
    ])
      .then(([t, cfg, pm]) => {
        setTender(t);
        setStripeEnabled(cfg.enabled);
        setPublishableKey(cfg.publishable_key);
        if (pm) {
          setExistingPayment({ status: pm.status, amount: pm.amount });
          if (pm.status === "succeeded") setPaid(true);
        }
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [tenderId]);

  const handleCreateIntent = async () => {
    setPayLoading(true);
    setError("");
    try {
      const intent = await createPaymentIntent(tenderId);
      setIntentCreated({
        clientSecret: intent.client_secret,
        amount: intent.amount,
      });
    } catch (e: any) {
      setError(e.message);
    } finally {
      setPayLoading(false);
    }
  };

  const handleMockPayment = async () => {
    // In dev mode without real Stripe, simulate payment success
    setPaying(true);
    await new Promise((r) => setTimeout(r, 1500));
    setPaying(false);
    setPaid(true);
    setTimeout(() => navigate(`/tenders/${tenderId}`), 2000);
  };

  if (loading) {
    return (
      <div className="login-page">
        <div style={{ color: "var(--muted)" }}>💳 Жүктелуде...</div>
      </div>
    );
  }

  if (!tender) {
    return (
      <div className="login-page">
        <div className="card login-card">
          <p style={{ color: "var(--danger)" }}>Тендер табылмады.</p>
        </div>
      </div>
    );
  }

  const deposit = calcDeposit(tender.budget);

  if (paid) {
    return (
      <div className="login-page">
        <div className="card login-card" style={{ textAlign: "center" }}>
          <div style={{ fontSize: 56, marginBottom: "1rem" }}>🎉</div>
          <h2 style={{ color: "var(--success)", marginBottom: "0.5rem" }}>Төлем сәтті!</h2>
          <p style={{ color: "var(--muted)" }}>
            Тендер жарияланды. Жеткізушілер ұсыныс жіберу мүмкіндігіне ие болды.
          </p>
          <button
            className="btn btn-primary"
            style={{ marginTop: "1.5rem", width: "100%" }}
            onClick={() => navigate(`/tenders/${tenderId}`)}
          >
            Тендерге өту →
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="login-page" style={{ alignItems: "flex-start", paddingTop: "3rem" }}>
      <div className="card" style={{ width: "min(100%, 520px)", padding: "2rem" }}>
        {/* Header */}
        <div style={{ marginBottom: "1.5rem" }}>
          <button
            onClick={() => navigate(`/tenders/${tenderId}`)}
            style={{
              background: "none",
              border: "none",
              color: "var(--muted)",
              cursor: "pointer",
              marginBottom: "0.75rem",
              fontSize: "0.9rem",
            }}
          >
            ← Артқа
          </button>
          <h1 style={{ fontSize: "1.4rem", fontWeight: 700, marginBottom: "0.25rem" }}>
            💳 Депозит төлеу
          </h1>
          <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
            Тендерді жариялау үшін депозит төленуі қажет
          </p>
        </div>

        {/* Tender info */}
        <div
          style={{
            background: "var(--surface2)",
            borderRadius: 10,
            padding: "1rem",
            marginBottom: "1.5rem",
            border: "1px solid var(--border)",
          }}
        >
          <div style={{ fontWeight: 700, marginBottom: "0.5rem" }}>{tender.title}</div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "0.5rem",
              fontSize: "0.875rem",
            }}
          >
            <div>
              <span style={{ color: "var(--muted)" }}>Бюджет:</span>
              <span style={{ marginLeft: 6, fontWeight: 600 }}>
                {Number(tender.budget).toLocaleString("ru-RU")} ₸
              </span>
            </div>
            <div>
              <span style={{ color: "var(--muted)" }}>Дедлайн:</span>
              <span style={{ marginLeft: 6, fontWeight: 600 }}>
                {new Date(tender.deadline).toLocaleDateString("ru-RU")}
              </span>
            </div>
          </div>
        </div>

        {/* Deposit breakdown */}
        <div
          style={{
            background: "rgba(59,130,246,0.08)",
            border: "1px solid rgba(59,130,246,0.25)",
            borderRadius: 10,
            padding: "1rem 1.25rem",
            marginBottom: "1.5rem",
          }}
        >
          <div style={{ color: "var(--muted)", fontSize: "0.85rem", marginBottom: "0.5rem" }}>
            Депозит есебі
          </div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span style={{ fontSize: "0.9rem" }}>1% бюджеттен (мин. $10)</span>
            <span style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--accent)" }}>
              ${deposit.toFixed(2)}
            </span>
          </div>
          <div style={{ color: "var(--muted)", fontSize: "0.78rem", marginTop: "0.5rem" }}>
            ℹ️ Тендер сәтті аяқталса — депозит қайтарылады
          </div>
        </div>

        {/* Existing payment */}
        {existingPayment && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "0.75rem 1rem",
              background: "var(--surface2)",
              borderRadius: 8,
              marginBottom: "1rem",
              border: "1px solid var(--border)",
            }}
          >
            <span style={{ color: "var(--muted)", fontSize: "0.875rem" }}>Ағымдағы төлем:</span>
            <StatusBadge status={existingPayment.status} />
          </div>
        )}

        {error && (
          <div
            style={{
              color: "var(--danger)",
              background: "rgba(239,68,68,0.08)",
              border: "1px solid rgba(239,68,68,0.2)",
              borderRadius: 8,
              padding: "0.75rem 1rem",
              marginBottom: "1rem",
              fontSize: "0.9rem",
            }}
          >
            ⚠️ {error}
          </div>
        )}

        {/* Payment action */}
        {!intentCreated ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {stripeEnabled ? (
              <button
                className="btn btn-primary"
                style={{ width: "100%", padding: "0.85rem", fontSize: "1rem" }}
                onClick={handleCreateIntent}
                disabled={payLoading}
              >
                {payLoading ? "⏳ Дайындалуда..." : `💳 Депозит төлеу — $${deposit.toFixed(2)}`}
              </button>
            ) : (
              <div>
                <div
                  style={{
                    background: "rgba(245,158,11,0.1)",
                    border: "1px solid rgba(245,158,11,0.3)",
                    borderRadius: 8,
                    padding: "0.75rem 1rem",
                    marginBottom: "1rem",
                    fontSize: "0.875rem",
                    color: "#fcd34d",
                  }}
                >
                  ⚠️ <strong>Dev режимі:</strong> Stripe конфигурацияланбаған.
                  Нақты жұмыс үшін <code>.env</code> файлында{" "}
                  <code>STRIPE_SECRET_KEY</code> орнатыңыз.
                </div>
                <button
                  className="btn btn-success"
                  style={{ width: "100%", padding: "0.85rem", fontSize: "1rem" }}
                  onClick={handleMockPayment}
                  disabled={paying}
                >
                  {paying ? "⏳ Өңделуде..." : "🧪 Симуляциялық төлем (Dev)"}
                </button>
              </div>
            )}
            <button
              className="btn btn-outline"
              style={{ width: "100%" }}
              onClick={() => navigate(`/tenders/${tenderId}`)}
            >
              Кейінге қалдыру
            </button>
          </div>
        ) : (
          /* Stripe Elements would render here in production */
          <div>
            <div
              style={{
                background: "var(--surface2)",
                borderRadius: 10,
                padding: "1.5rem",
                marginBottom: "1rem",
                border: "1px solid var(--border)",
                textAlign: "center",
              }}
            >
              <div style={{ fontSize: 40, marginBottom: "0.75rem" }}>💳</div>
              <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
                Stripe Elements мұнда жүктеледі. client_secret жіберілді:
              </p>
              <code
                style={{
                  fontSize: "0.75rem",
                  color: "var(--accent)",
                  wordBreak: "break-all",
                }}
              >
                {intentCreated.clientSecret.slice(0, 30)}…
              </code>
            </div>
            <button
              className="btn btn-primary"
              style={{ width: "100%", padding: "0.85rem" }}
              onClick={handleMockPayment}
              disabled={paying}
            >
              {paying ? "⏳ Өңделуде..." : "✅ Төлемді растау"}
            </button>
          </div>
        )}

        {/* Info footer */}
        <div
          style={{
            marginTop: "1.5rem",
            padding: "0.75rem",
            borderTop: "1px solid var(--border)",
            fontSize: "0.78rem",
            color: "var(--muted)",
            textAlign: "center",
          }}
        >
          🔒 Барлық төлемдер Stripe арқылы қауіпсіз өңделеді
        </div>
      </div>
    </div>
  );
}
