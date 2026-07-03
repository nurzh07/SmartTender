import type {
  AdminDashboard,
  ApprovalStep,
  BuyerDashboard,
  MonthlyBar,
  Notification,
  PaymentIntent,
  PaymentStatus,
  Proposal,
  Report,
  ReportType,
  SupplierDashboard,
  Tender,
  TelegramConnectCode,
  TelegramStatus,
  TopSupplier,
  User,
} from "./types";

const API = "/api";

function parseApiError(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) =>
        typeof item === "object" && item && "msg" in item ? String(item.msg) : String(item)
      )
      .join(", ");
  }
  return "Сұрау сәтсіз аяқталды";
}

function getToken(): string | null {
  return localStorage.getItem("access_token");
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API}${path}`, { ...options, headers });
  if (res.status === 401) {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(parseApiError(err.detail));
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// ── Auth ─────────────────────────────────────────────────────

export async function login(email: string, password: string) {
  const data = await api<{ access_token: string; refresh_token: string }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("refresh_token", data.refresh_token);
  return data;
}

export function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

export const getMe = () => api<User>("/users/me");

export const register = (body: {
  email: string;
  password: string;
  full_name?: string;
  role: "buyer" | "supplier";
  bin?: string;
  company_official_name?: string;
}) =>
  api<{ message: string; user: User }>("/auth/register", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const forgotPassword = (email: string) =>
  api<{ message: string; reset_link?: string }>("/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
  });

export const resetPassword = (token: string, newPassword: string) =>
  api<{ message: string }>("/auth/reset-password", {
    method: "POST",
    body: JSON.stringify({ token, new_password: newPassword }),
  });

export const verifyEmail = (token: string) =>
  api<User>("/auth/verify-email", {
    method: "POST",
    body: JSON.stringify({ token }),
  });

// ── Users ────────────────────────────────────────────────────

export const getUsers = () => api<User[]>("/users");

export const updateUser = (
  id: number,
  body: Partial<Pick<User, "full_name" | "is_active"> & { role?: User["role"] }>
) => api<User>(`/users/${id}`, { method: "PATCH", body: JSON.stringify(body) });

export const deleteUser = (id: number) => api<void>(`/users/${id}`, { method: "DELETE" });

// ── Tenders ──────────────────────────────────────────────────

export const getTenders = (page = 1, status?: string) => {
  const q = new URLSearchParams({ page: String(page), limit: "50" });
  if (status) q.set("status", status);
  return api<Tender[]>(`/tenders?${q}`);
};

export const getTender = (id: number) => api<Tender>(`/tenders/${id}`);

export const createTender = (body: object) =>
  api<Tender>("/tenders", { method: "POST", body: JSON.stringify(body) });

export const updateTenderStatus = (id: number, status: string) =>
  api<Tender>(`/tenders/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });

export const publishTender = (id: number) => updateTenderStatus(id, "published");

export const deleteTender = (id: number) => api<void>(`/tenders/${id}`, { method: "DELETE" });

// ── Approval ─────────────────────────────────────────────────

export const submitTender = (id: number) =>
  api<ApprovalStep[]>(`/tenders/${id}/submit`, { method: "POST" });

export const approveTender = (id: number, comment?: string) =>
  api<ApprovalStep>(`/tenders/${id}/approve`, {
    method: "POST",
    body: JSON.stringify({ comment: comment || null }),
  });

export const rejectTender = (id: number, comment?: string) =>
  api<ApprovalStep>(`/tenders/${id}/reject`, {
    method: "POST",
    body: JSON.stringify({ comment: comment || null }),
  });

export const getApproval = (id: number) => api<ApprovalStep[]>(`/tenders/${id}/approval`);

// ── Proposals ────────────────────────────────────────────────

export const getProposals = (tenderId: number) =>
  api<Proposal[]>(`/tenders/${tenderId}/proposals`);

export const createProposal = (
  tenderId: number,
  body: { price: number; delivery_days: number; comment?: string }
) =>
  api<Proposal>(`/tenders/${tenderId}/proposals`, {
    method: "POST",
    body: JSON.stringify(body),
  });

// ── Notifications ────────────────────────────────────────────

export const getNotifications = () => api<Notification[]>("/notifications?unread_only=false");

export const markNotificationRead = (id: number) =>
  api<Notification>(`/notifications/${id}/read`, { method: "PATCH" });

// ── Reports ──────────────────────────────────────────────────

export const getReports = () => api<Report[]>("/reports");

export const generateReport = (report_type: ReportType, period: string) =>
  api<{ task_id: string; status: string; report_type: string }>("/reports/generate", {
    method: "POST",
    body: JSON.stringify({ report_type, period }),
  });

// ── Analytics ────────────────────────────────────────────────

export const getBuyerDashboard = () => api<BuyerDashboard>("/analytics/buyer/dashboard");

export const getSupplierDashboard = () => api<SupplierDashboard>("/analytics/supplier/dashboard");

export const getAdminDashboard = () => api<AdminDashboard>("/analytics/admin/dashboard");

export const getMonthlyTenders = (year: number) =>
  api<MonthlyBar[]>(`/analytics/tenders/monthly?year=${year}`);

export const getTopSuppliers = () => api<TopSupplier[]>("/analytics/suppliers/top10");

// ── Payments ─────────────────────────────────────────────────

export const getStripeConfig = () =>
  api<{ publishable_key: string; enabled: boolean }>("/payments/config");

export const createPaymentIntent = (tender_id: number, currency = "usd") =>
  api<PaymentIntent>("/payments/create-intent", {
    method: "POST",
    body: JSON.stringify({ tender_id, currency }),
  });

export const getPaymentStatus = (tender_id: number) =>
  api<PaymentStatus>(`/payments/tender/${tender_id}`);

// ── Telegram ─────────────────────────────────────────────────

export const getTelegramStatus = () => api<TelegramStatus>("/telegram/status");

export const getTelegramConnectCode = () => api<TelegramConnectCode>("/telegram/connect-code");

export const disconnectTelegram = () =>
  api<{ message: string }>("/telegram/disconnect", { method: "DELETE" });
