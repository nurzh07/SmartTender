import type { UserRole } from "./types";

export type NavItem = {
  to: string;
  label: string;
  end?: boolean;
};

export type RoleConfig = {
  label: string;
  subtitle: string;
  tasks: string[];
  nav: NavItem[];
  accent: string;
};

export const ROLE_CONFIG: Record<UserRole, RoleConfig> = {
  supplier: {
    label: "Жеткізуші",
    subtitle: "Жарияланған тендерлерге ұсыныс жіберу",
    accent: "#22c55e",
    tasks: [
      "Жарияланған тендерлерді көру",
      "Коммерциялық ұсыныс жіберу",
      "Нәтиже мен статусты бақылау",
    ],
    nav: [
      { to: "/", label: "Басты бет", end: true },
      { to: "/tenders", label: "Ашық тендерлер" },
    ],
  },
  buyer: {
    label: "Сатып алушы (Buyer)",
    subtitle: "Тендер жариялау, ұсыныстарды бағалау, жеңімпаз таңдау",
    accent: "#3b82f6",
    tasks: [
      "Тендер жасау және жариялау",
      "Қызметкер өтінімін бекіту (2-қадам)",
      "Ұсыныстарды қарау және жеңімпаз таңдау",
      "Есептерді генерациялау",
    ],
    nav: [
      { to: "/", label: "Басты бет", end: true },
      { to: "/tenders", label: "Тендерлер" },
      { to: "/reports", label: "Есептер" },
    ],
  },
  employee: {
    label: "Қызметкер",
    subtitle: "Сатып алу өтінімін жасау және бекітуге жіберу",
    accent: "#a78bfa",
    tasks: [
      "Жаңа сатып алу өтінімі жасау",
      "Бекітуге жіберу",
      "Статус пен workflow бақылау",
    ],
    nav: [
      { to: "/", label: "Басты бет", end: true },
      { to: "/tenders", label: "Менің өтінімдерім" },
    ],
  },
  department_head: {
    label: "Бөлім басшысы",
    subtitle: "Қызметкер өтінімдерін бекіту немесе қабылдамау",
    accent: "#f59e0b",
    tasks: [
      "Кезектегі өтінімдерді қарау",
      "Бекіту немесе қабылдамау (1-қадам)",
      "Бекіту тарихын бақылау",
    ],
    nav: [
      { to: "/", label: "Басты бет", end: true },
      { to: "/approvals", label: "Бекіту кезегі" },
    ],
  },
  procurement_manager: {
    label: "Сатып алу менеджері",
    subtitle: "Бекітілген тендерлерді жариялау",
    accent: "#8b5cf6",
    tasks: [
      "Бекітілген тендерлерді қарау",
      "Тендерлерді жариялау (2-қадам)",
      "Ұсыныстарды бағалау",
    ],
    nav: [
      { to: "/", label: "Басты бет", end: true },
      { to: "/tenders", label: "Тендерлер" },
      { to: "/approvals", label: "Жариялау кезегі" },
    ],
  },
  superadmin: {
    label: "Әкімші",
    subtitle: "Платформаны толық басқару",
    accent: "#ef4444",
    tasks: [
      "Пайдаланушыларды басқару (блок/рөл)",
      "Барлық тендерлер мен өтінімдер",
      "Есептер мен хабарламалар",
    ],
    nav: [
      { to: "/", label: "Басты бет", end: true },
      { to: "/users", label: "Пайдаланушылар" },
      { to: "/tenders", label: "Тендерлер" },
      { to: "/reports", label: "Есептер" },
      { to: "/notifications", label: "Хабарламалар" },
    ],
  },
};

export function getRoleConfig(role: UserRole | undefined): RoleConfig | null {
  if (!role) return null;
  return ROLE_CONFIG[role];
}
