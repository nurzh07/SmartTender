export type UserRole =
  | "superadmin"
  | "buyer"
  | "department_head"
  | "employee"
  | "supplier";

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  role: UserRole;
  is_active: boolean;
  is_verified?: boolean;
  department_id: number | null;
  created_at: string;
}

export type TenderStatus = "draft" | "published" | "evaluation" | "awarded" | "closed";

export interface Tender {
  id: number;
  title: string;
  description: string | null;
  budget: string;
  deadline: string;
  status: TenderStatus;
  category_id: number | null;
  created_by: number;
  approval_status?: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface Proposal {
  id: number;
  tender_id: number;
  supplier_id: number;
  supplier_name?: string | null;
  price: string;
  delivery_days: number;
  file_url: string | null;
  score: number;
  status: string;
  comment: string | null;
}

export interface Notification {
  id: number;
  type: string;
  message: string;
  is_read: boolean;
  channel: string;
  sent_at: string;
}

export type ReportType =
  | "monthly_tenders_pdf"
  | "supplier_ratings_excel"
  | "budget_analytics";

export interface Report {
  id: number;
  report_type: ReportType;
  period: string;
  file_url: string | null;
  generated_by: number | null;
  created_at: string;
}

export interface ApprovalStep {
  id: number;
  tender_id: number;
  step: number;
  status: string;
  comment: string | null;
  approver_id: number | null;
  approved_at: string | null;
}
