import { api, buildQuery } from "./client";
import type { TermSlim } from "./types";

export interface BudgetPublic {
  id: string;
  owner_id: string;
  category: TermSlim;
  year: number;
  month: number;
  amount: number;
  currency: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface BudgetWithSpend extends BudgetPublic {
  spent: number;
  remaining: number;
  utilization: number;
}

export interface BudgetCreatePayload {
  category: string;
  year: number;
  month: number;
  amount: number;
  currency?: string;
  notes?: string | null;
}

export interface BudgetUpdatePayload {
  amount?: number;
  notes?: string | null;
}

export function listBudgets(year: number, month: number): Promise<BudgetWithSpend[]> {
  const qs = buildQuery({ year, month });
  return api.get<BudgetWithSpend[]>(`/budgets${qs ? `?${qs}` : ""}`);
}

export function createBudget(data: BudgetCreatePayload): Promise<BudgetPublic> {
  return api.post<BudgetPublic>("/budgets", data);
}

export function updateBudget(id: string, data: BudgetUpdatePayload): Promise<BudgetPublic> {
  return api.patch<BudgetPublic>(`/budgets/${id}`, data);
}

export function deleteBudget(id: string): Promise<void> {
  return api.delete(`/budgets/${id}`);
}

