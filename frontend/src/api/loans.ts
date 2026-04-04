import { api } from "./client";
import type { Paginated } from "./types";

export interface LoanPublic {
  id: string;
  owner_id: string;
  person_id: string;
  direction: string;
  loan_type: string;
  description: string;
  amount: number | null;
  currency: string | null;
  item_name: string | null;
  loaned_on: string | null;
  due_on: string | null;
  returned_on: string | null;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface LoanCreatePayload {
  person_id: string;
  direction: string;
  loan_type: string;
  description: string;
  amount?: number | null;
  currency?: string | null;
  item_name?: string | null;
  loaned_on?: string | null;
  due_on?: string | null;
  notes?: string | null;
}

export interface LoanUpdatePayload {
  description?: string;
  amount?: number | null;
  currency?: string | null;
  item_name?: string | null;
  loaned_on?: string | null;
  due_on?: string | null;
  returned_on?: string | null;
  status?: string;
  notes?: string | null;
}

export function listLoans(params: {
  skip?: number;
  limit?: number;
  direction?: string;
  status_filter?: string;
} = {}): Promise<Paginated<LoanPublic>> {
  const q = new URLSearchParams();
  if (params.skip !== undefined) q.set("skip", String(params.skip));
  if (params.limit !== undefined) q.set("limit", String(params.limit));
  if (params.direction) q.set("direction", params.direction);
  if (params.status_filter) q.set("status_filter", params.status_filter);
  const qs = q.toString();
  return api.get<Paginated<LoanPublic>>(`/loans${qs ? `?${qs}` : ""}`);
}

export function getLoan(id: string): Promise<LoanPublic> {
  return api.get<LoanPublic>(`/loans/${id}`);
}

export function createLoan(data: LoanCreatePayload): Promise<LoanPublic> {
  return api.post<LoanPublic>("/loans", data);
}

export function updateLoan(id: string, data: LoanUpdatePayload): Promise<LoanPublic> {
  return api.patch<LoanPublic>(`/loans/${id}`, data);
}

export function deleteLoan(id: string): Promise<void> {
  return api.delete(`/loans/${id}`);
}
