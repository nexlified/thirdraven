import { api, buildQuery } from "./client";
import type { Paginated, TermSlim } from "./types";

export interface TransactionPublic {
  id: string;
  owner_id: string;
  transaction_type: "expense" | "income";
  amount: number;
  currency: string;
  transacted_on: string;
  description: string;
  category: TermSlim | null;
  payment_method: TermSlim | null;
  asset_id: string | null;
  subscription_id: string | null;
  merchant: string | null;
  reference: string | null;
  tags: string[];
  import_batch_id: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface CategoryBreakdown {
  category_slug: string;
  category_name: string;
  total: number;
  count: number;
  percentage: number;
}

export interface DailyTotal {
  date: string;
  income: number;
  expense: number;
}

export interface TransactionSummary {
  period_from: string;
  period_to: string;
  total_income: number;
  total_expense: number;
  net: number;
  savings_rate: number | null;
  expense_by_category: CategoryBreakdown[];
  income_by_category: CategoryBreakdown[];
  daily_totals: DailyTotal[];
  currency: string;
}

export interface TransactionCreatePayload {
  transaction_type: "expense" | "income";
  amount: number;
  currency?: string;
  transacted_on: string;
  description: string;
  category?: string | null;
  payment_method?: string | null;
  asset_id?: string | null;
  merchant?: string | null;
  reference?: string | null;
  tags?: string[];
  import_batch_id?: string | null;
  notes?: string | null;
}

export type TransactionUpdatePayload = Partial<TransactionCreatePayload>;

export interface QuickParseRequest {
  input: string;
  currency?: string;
}

export function listTransactions(params: {
  skip?: number;
  limit?: number;
  transaction_type?: "expense" | "income";
  category?: string;
  payment_method?: string;
  date_from?: string;
  date_to?: string;
  search?: string;
} = {}): Promise<Paginated<TransactionPublic>> {
  const qs = buildQuery(params);
  return api.get<Paginated<TransactionPublic>>(`/transactions${qs ? `?${qs}` : ""}`);
}

export function getTransactionSummary(params: {
  date_from?: string;
  date_to?: string;
  currency?: string;
} = {}): Promise<TransactionSummary> {
  const qs = buildQuery(params);
  return api.get<TransactionSummary>(`/transactions/summary${qs ? `?${qs}` : ""}`);
}

export function createTransaction(data: TransactionCreatePayload): Promise<TransactionPublic> {
  return api.post<TransactionPublic>("/transactions", data);
}

export function updateTransaction(id: string, data: TransactionUpdatePayload): Promise<TransactionPublic> {
  return api.patch<TransactionPublic>(`/transactions/${id}`, data);
}

export function deleteTransaction(id: string): Promise<void> {
  return api.delete(`/transactions/${id}`);
}

export function bulkCreateTransactions(items: TransactionCreatePayload[]): Promise<TransactionPublic[]> {
  return api.post<TransactionPublic[]>("/transactions/bulk", items);
}

export function parseTransactionInput(input: string, currency = "INR"): Promise<TransactionCreatePayload> {
  return api.post<TransactionCreatePayload>("/transactions/parse", { input, currency });
}

export function quickAddTransaction(input: string, currency = "INR"): Promise<TransactionPublic> {
  return api.post<TransactionPublic>("/transactions/quick-add", { input, currency });
}

