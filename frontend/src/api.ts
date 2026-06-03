import type { ApprovalStep, Notification, Proposal, Tender, User } from "./types";

const API = "/api";

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
    throw new Error(err.detail || "Request failed");
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
