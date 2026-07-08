export type UserRole =
  | "superadmin"
  | "buyer"
  | "department_head"
  | "employee"
  | "supplier"
  | "procurement_manager";

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  role: UserRole;
  is_active: boolean;
  is_verified?: boolean;
  department_id: number | null;
  created_at: string;
  // BIN verification
  bin?: string | null;
  bin_verified?: boolean;
  company_official_name?: string | null;
  company_registration_date?: string | null;
  company_status?: string | null;
  bin_verified_at?: string | null;
}

export type TenderStatus =
  | "draft"
  | "payment_pending"
  | "published"
  | "evaluation"
  | "awarded"
  | "closed";

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
  | "tender_summary"
  | "supplier_performance"
  | "procurement_report"
  | "monthly_tender_pdf"
  | "supplier_ratings_excel"
  | "budget_analytics";

export type ReportStatus = "pending" | "generating" | "completed" | "failed";

export interface Report {
  id: number;
  title: string;
  type: ReportType;
  status: ReportStatus;
  file_path: string | null;
  file_type: string | null;
  created_by_id: number;
  created_at: string;
  updated_at: string;
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

// ── Analytics types ──────────────────────────────────────────

export interface MonthlyBar {
  month: string;
  month_label: string;
  count: number;
  budget?: number;
}

export interface StatusPie {
  status: string;
  count: number;
  label: string;
}

export interface TopSupplier {
  supplier_id: number;
  supplier_name: string;
  supplier_email: string;
  total_proposals: number;
  wins: number;
  win_rate: number;
}

export interface TopBuyer {
  buyer_id: number;
  buyer_name: string;
  buyer_email: string;
  total_tenders: number;
  total_budget: number;
}

export interface BuyerDashboard {
  total_tenders_this_month: number;
  total_tenders_last_month: number;
  total_budget_awarded: number;
  avg_proposals_per_tender: number;
  top_suppliers: TopSupplier[];
  status_distribution: StatusPie[];
  monthly_activity: MonthlyBar[];
}

export interface SupplierDashboard {
  total_proposals: number;
  win_rate: number;
  avg_own_price: number;
  avg_market_price: number;
  monthly_activity: MonthlyBar[];
  wins_losses: StatusPie[];
}

export interface AdminDashboard {
  total_users: number;
  total_buyers: number;
  total_suppliers: number;
  total_tenders: number;
  total_transaction_volume: number;
  status_distribution: StatusPie[];
  monthly_activity: MonthlyBar[];
  top_buyers: TopBuyer[];
  top_suppliers: TopSupplier[];
}

// ── Payment types ────────────────────────────────────────────

export interface PaymentIntent {
  payment_id: number;
  tender_id: number;
  client_secret: string;
  payment_intent_id: string;
  amount: number;
  currency: string;
  status: string;
}

export interface PaymentStatus {
  payment_id: number;
  tender_id: number;
  amount: number;
  currency: string;
  status: string;
  stripe_payment_intent_id: string | null;
  created_at: string;
}

// ── Telegram types ───────────────────────────────────────────

export interface TelegramStatus {
  linked: boolean;
  telegram_chat_id: string | null;
}

export interface TelegramConnectCode {
  code: string;
  instructions: string;
  command: string;
  bot_link: string;
}
