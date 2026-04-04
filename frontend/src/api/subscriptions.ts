import { api } from "./client";
import type { Paginated, TermSlim } from "./types";

export interface SubscriptionPublicRead {
  id: string;
  owner_id: string;
  name: string;
  provider: string | null;
  category: TermSlim | null;
  status: string;
  cost: number;
  currency: string;
  payment_mode: string;
  billing_cycle: string;
  billing_cycle_days: number | null;
  started_on: string | null;
  next_billing_date: string | null;
  trial_ends_on: string | null;
  cancelled_on: string | null;
  auto_renews: boolean;
  url: string | null;
  notes: string | null;
  asset_id: string | null;
  tags: TermSlim[];
  created_at: string;
  updated_at: string;
}

export interface UpcomingRenewal {
  id: string;
  name: string;
  cost: number;
  currency: string;
  next_billing_date: string;
}

export interface CategorySpend {
  category: string;
  monthly_cost: number;
}

export interface SubscriptionSummary {
  total_active: number;
  monthly_cost_by_currency: Record<string, number>;
  upcoming_renewals: UpcomingRenewal[];
  cost_by_category: CategorySpend[];
}

export interface SubscriptionCreatePayload {
  name: string;
  provider?: string | null;
  category?: string | null;
  status?: string;
  cost: number;
  currency?: string;
  payment_mode?: string;
  billing_cycle?: string;
  billing_cycle_days?: number | null;
  started_on?: string | null;
  next_billing_date?: string | null;
  trial_ends_on?: string | null;
  auto_renews?: boolean;
  url?: string | null;
  notes?: string | null;
  asset_id?: string | null;
  tags?: string[];
}

export type SubscriptionUpdatePayload = Partial<SubscriptionCreatePayload> & {
  cancelled_on?: string | null;
};

export function listSubscriptions(params: {
  skip?: number;
  limit?: number;
  status?: string;
  category?: string;
  billing_cycle?: string;
} = {}): Promise<Paginated<SubscriptionPublicRead>> {
  const q = new URLSearchParams();
  if (params.skip !== undefined) q.set("skip", String(params.skip));
  if (params.limit !== undefined) q.set("limit", String(params.limit));
  if (params.status) q.set("status", params.status);
  if (params.category) q.set("category", params.category);
  if (params.billing_cycle) q.set("billing_cycle", params.billing_cycle);
  const qs = q.toString();
  return api.get<Paginated<SubscriptionPublicRead>>(`/subscriptions${qs ? `?${qs}` : ""}`);
}

export function getSubscriptionSummary(): Promise<SubscriptionSummary> {
  return api.get<SubscriptionSummary>("/subscriptions/summary");
}

export function getSubscription(id: string): Promise<SubscriptionPublicRead> {
  return api.get<SubscriptionPublicRead>(`/subscriptions/${id}`);
}

export function createSubscription(data: SubscriptionCreatePayload): Promise<SubscriptionPublicRead> {
  return api.post<SubscriptionPublicRead>("/subscriptions", data);
}

export function updateSubscription(id: string, data: SubscriptionUpdatePayload): Promise<SubscriptionPublicRead> {
  return api.patch<SubscriptionPublicRead>(`/subscriptions/${id}`, data);
}

export function deleteSubscription(id: string): Promise<void> {
  return api.delete(`/subscriptions/${id}`);
}
