import { api } from "./client";
import type { CategoryBreakdown } from "./transactions";

export interface AssetSummaryItem {
  asset_id: string;
  name: string;
  account_type: string | null;
  institution: string | null;
  current_balance: number | null;
  currency: string | null;
}

export interface LoanSummaryItem {
  loan_id: string;
  direction: "lent" | "borrowed";
  person_name: string;
  amount: number | null;
  currency: string | null;
  status: string;
  due_on: string | null;
}

export interface FinanceOverview {
  financial_assets: AssetSummaryItem[];
  total_asset_value_by_currency: Record<string, number>;
  outstanding_loans: LoanSummaryItem[];
  total_lent_by_currency: Record<string, number>;
  total_borrowed_by_currency: Record<string, number>;
  current_month_income: number;
  current_month_expenses: number;
  current_month_net: number;
  current_month_savings_rate: number | null;
  current_month_currency: string;
  top_expense_categories: CategoryBreakdown[];
  monthly_subscription_cost_by_currency: Record<string, number>;
  as_of: string;
}

export function getFinanceOverview(currency = "INR"): Promise<FinanceOverview> {
  return api.get<FinanceOverview>(`/finances/overview?currency=${currency}`);
}

