import type { ApprovalStep, Notification, Proposal, Report, ReportType, Tender, User } from "./types";

const API = "/api";

function parseApiError(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => (typeof item === "object" && item && "msg" in item ? String(item.msg) : String(item))).join(", ");
  }
  return "Сұрау сәтсіз аяқталды";
}

function getToken(): string | null {
  return localStorage.getItem("access_token");
}

export async function api<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
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

export async function login(email: string, password: string) {
  const data = await api<{ access_token: string; refresh_token: string }>(
    "/auth/login",
    { method: "POST", body: JSON.stringify({ email, password }) }
  );
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("refresh_token", data.refresh_token);
  return data;
}

export function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

export const getMe = () => api<User>("/users/me");

export const getTenders = (page = 1, status?: string) => {
  const q = new URLSearchParams({ page: String(page), limit: "50" });
  if (status) q.set("status", status);
  return api<Tender[]>(`/tenders?${q}`);
};

export const getTender = (id: number) => api<Tender>(`/tenders/${id}`);

export const createTender = (body: object) =>
  api<Tender>("/tenders", { method: "POST", body: JSON.stringify(body) });

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

export const getApproval = (id: number) =>
  api<ApprovalStep[]>(`/tenders/${id}/approval`);

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

export const getNotifications = () => api<Notification[]>("/notifications?unread_only=false");

export const markNotificationRead = (id: number) =>
  api<Notification>(`/notifications/${id}/read`, { method: "PATCH" });

export const publishTender = (id: number) =>
  api<Tender>(`/tenders/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status: "published" }),
  });

export const getReports = () => api<Report[]>("/reports");

export const generateReport = (report_type: ReportType, period: string) =>
  api<{ task_id: string; status: string; report_type: string }>("/reports/generate", {
    method: "POST",
    body: JSON.stringify({ report_type, period }),
  });

export const verifyEmail = (token: string) =>
  api<User>("/auth/verify-email", {
    method: "POST",
    body: JSON.stringify({ token }),
  });

export const register = (body: {
  email: string;
  password: string;
  full_name?: string;
  role: "buyer" | "supplier";
}) =>
  api<{ message: string; user: User }>("/auth/register", {
    method: "POST",
    body: JSON.stringify(body),
  });
