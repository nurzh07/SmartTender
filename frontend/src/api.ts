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

// ── Monitoring API ───────────────────────────────────────────
export const getExternalTenders = (params?: {
  category?: string;
  region?: string;
  min_price?: number;
  max_price?: number;
}) => api<any>("/monitoring/external-tenders", { method: "GET" });

export const addToWatchlist = (tenderId: string, source: string) =>
  api<any>("/monitoring/watchlist", {
    method: "POST",
    body: JSON.stringify({ tender_id: tenderId, source }),
  });

export const getWatchlist = () => api<any>("/monitoring/watchlist");

export const removeFromWatchlist = (watchlistId: number) =>
  api<void>(`/monitoring/watchlist/${watchlistId}`, { method: "DELETE" });

export const getMonitoringCategories = () => api<any>("/monitoring/categories");

export const getMonitoringRegions = () => api<any>("/monitoring/regions");

// ── Ratings API ─────────────────────────────────────────────
export const createRating = (data: {
  tender_id: number;
  supplier_id: number;
  quality_score: number;
  delivery_score: number;
  communication_score: number;
  price_score: number;
  review?: string;
}) => api<any>("/ratings/ratings", {
  method: "POST",
  body: JSON.stringify(data),
});

export const getSupplierRatings = (supplierId: number) =>
  api<any>(`/ratings/ratings/supplier/${supplierId}`);

export const getSupplierAverageRating = (supplierId: number) =>
  api<any>(`/ratings/ratings/supplier/${supplierId}/average`);

export const createPortfolio = (data: {
  project_name: string;
  project_description?: string;
  project_value?: number;
  completion_date?: string;
  client_name?: string;
  client_contact?: string;
  documents?: string;
}) => api<any>("/ratings/portfolio", {
  method: "POST",
  body: JSON.stringify(data),
});

export const getMyPortfolio = () => api<any>("/ratings/portfolio/my");

export const updatePortfolio = (portfolioId: number, data: any) =>
  api<any>(`/ratings/portfolio/${portfolioId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });

export const deletePortfolio = (portfolioId: number) =>
  api<void>(`/ratings/portfolio/${portfolioId}`, { method: "DELETE" });

export const createCertification = (data: {
  certification_name: string;
  issuing_organization: string;
  certificate_number?: string;
  issue_date?: string;
  expiry_date?: string;
  document_url?: string;
}) => api<any>("/ratings/certifications", {
  method: "POST",
  body: JSON.stringify(data),
});

export const getMyCertifications = () => api<any>("/ratings/certifications/my");

export const deleteCertification = (certificationId: number) =>
  api<void>(`/ratings/certifications/${certificationId}`, { method: "DELETE" });

// ── Permissions API ─────────────────────────────────────────
export const getMyPermissions = () => api<any>("/permissions/my");

export const checkPermission = (permissionName: string) =>
  api<any>(`/permissions/check/${permissionName}`);

export const initializePermissions = () =>
  api<any>("/permissions/initialize", { method: "POST" });

export const grantRolePermission = (role: string, permissionName: string) =>
  api<any>("/permissions/role/grant", {
    method: "POST",
    body: JSON.stringify({ role, permission_name: permissionName }),
  });

export const revokeRolePermission = (role: string, permissionName: string) =>
  api<any>("/permissions/role/revoke", {
    method: "POST",
    body: JSON.stringify({ role, permission_name: permissionName }),
  });

export const getRolePermissions = (role: string) =>
  api<any>(`/permissions/role/${role}`);

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

export const generateReport = (type: ReportType, title?: string) => {
  const defaultTitle = (t: ReportType) => {
    switch (t) {
      case "monthly_tender_pdf": return "Айлық тендер PDF";
      case "supplier_ratings_excel": return "Жеткізуші рейтингтері Excel";
      case "budget_analytics": return "Бюджет аналитикасы";
      case "tender_summary": return "Тендер қорытамасы";
      case "supplier_performance": return "Жеткізуші өнімділігі";
      case "procurement_report": return "Сатып алу есебі";
      default: return "Есеп";
    }
  };
  return api<Report>("/reports/generate", {
    method: "POST",
    body: JSON.stringify({ type, title: title || defaultTitle(type) }),
  });
};

export const downloadReport = async (reportId: number) => {
  const token = localStorage.getItem("access_token");
  const res = await fetch(`/api/reports/${reportId}/download`, {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
  if (!res.ok) throw new Error("Жүктеу сәтсіз");
  const blob = await res.blob();
  const contentDisposition = res.headers.get("Content-Disposition");
  const filename = contentDisposition
    ? contentDisposition.split("filename=")[1].replace(/"/g, "")
    : `report-${reportId}`;
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
};

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
