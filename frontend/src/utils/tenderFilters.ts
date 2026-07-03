import type { ApprovalStep, Tender, User, UserRole } from "../types";

export function isPendingApproval(tender: Tender) {
  const status = tender.approval_status || "draft";
  return status === "pending_approval" || status.startsWith("pending_step_");
}

export function filterTendersForRole(tenders: Tender[], role: UserRole, userId: number): Tender[] {
  switch (role) {
    case "supplier":
      return tenders.filter((t) => t.status === "published");
    case "employee":
      return tenders.filter((t) => t.created_by === userId);
    case "department_head":
      return tenders.filter(
        (t) =>
          isPendingApproval(t) &&
          (t.approval_status === "pending_approval" || t.approval_status === "pending_step_1")
      );
    case "buyer":
      return tenders.filter(
        (t) =>
          t.created_by === userId ||
          t.approval_status === "approved" ||
          t.approval_status === "pending_step_2" ||
          t.status !== "draft" ||
          isPendingApproval(t)
      );
    default:
      return tenders;
  }
}

export function getPendingStepForRole(steps: ApprovalStep[], role: UserRole): ApprovalStep | undefined {
  const pending = steps.find((s) => s.status === "pending");
  if (!pending) return undefined;
  if (role === "department_head" && pending.step === 1) return pending;
  if (role === "buyer" && pending.step === 2) return pending;
  return undefined;
}

export function tendersNeedingAction(tenders: Tender[], role: UserRole, userId: number): Tender[] {
  if (role === "employee") {
    return tenders.filter(
      (t) =>
        t.created_by === userId &&
        t.status === "draft" &&
        !isPendingApproval(t) &&
        (t.approval_status || "draft") === "draft"
    );
  }
  if (role === "department_head") {
    return tenders.filter((t) => t.approval_status === "pending_approval");
  }
  if (role === "buyer") {
    return tenders.filter(
      (t) =>
        t.approval_status === "pending_step_2" ||
        (t.approval_status === "approved" && t.status === "draft") ||
        t.status === "published" ||
        t.status === "evaluation"
    );
  }
  if (role === "supplier") {
    return tenders.filter((t) => t.status === "published");
  }
  return tenders;
}

export function rolePageTitle(role: UserRole): string {
  const titles: Record<UserRole, string> = {
    supplier: "Ашық тендерлер",
    buyer: "Тендерлер",
    employee: "Менің өтінімдерім",
    department_head: "Бекіту кезегі",
    superadmin: "Барлық тендерлер",
  };
  return titles[role];
}

export function rolePageSubtitle(role: UserRole): string {
  const subs: Record<UserRole, string> = {
    supplier: "Жарияланған лоттарға ұсыныс жіберіңіз",
    buyer: "Жасау, жариялау, бағалау және жеңімпаз таңдау",
    employee: "Сатып алу өтінімдеріңіз",
    department_head: "Қызметкерлерден келген өтінімдер",
    superadmin: "Платформадағы барлық тендерлер",
  };
  return subs[role];
}

export function canCreateTender(role: UserRole): boolean {
  return role === "employee" || role === "buyer" || role === "superadmin";
}

export function defaultStatusFilter(role: UserRole): string {
  if (role === "supplier") return "published";
  return "";
}
