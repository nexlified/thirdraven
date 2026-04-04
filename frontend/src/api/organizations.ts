import { api } from "./client";
import type { Paginated, TermSlim } from "./types";

export interface CountrySlim {
  id: string;
  name: string;
  alpha2: string;
}

export interface OrgPublic {
  id: string;
  owner_id: string;
  name: string;
  type: TermSlim | null;
  description: string | null;
  website: string | null;
  email: string | null;
  phone: string | null;
  industry: TermSlim | null;
  founded_year: number | null;
  headquarters_city: string | null;
  country: CountrySlim | null;
  linkedin_url: string | null;
  notes: string | null;
  visibility: string;
  household_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface OrgSlim {
  id: string;
  name: string;
  type: TermSlim | null;
  headquarters_city: string | null;
  country: CountrySlim | null;
}

export interface OrgCreatePayload {
  name: string;
  type?: string | null;
  description?: string | null;
  website?: string | null;
  email?: string | null;
  phone?: string | null;
  industry?: string | null;
  founded_year?: number | null;
  headquarters_city?: string | null;
  country?: string | null;
  linkedin_url?: string | null;
  notes?: string | null;
  visibility?: string;
}

export type OrgUpdatePayload = Partial<OrgCreatePayload>;

export function listOrganizations(params: {
  skip?: number;
  limit?: number;
} = {}): Promise<Paginated<OrgPublic>> {
  const q = new URLSearchParams();
  if (params.skip !== undefined) q.set("skip", String(params.skip));
  if (params.limit !== undefined) q.set("limit", String(params.limit));
  const qs = q.toString();
  return api.get<Paginated<OrgPublic>>(`/organizations${qs ? `?${qs}` : ""}`);
}

export function getOrganization(orgId: string): Promise<OrgPublic> {
  return api.get<OrgPublic>(`/organizations/${orgId}`);
}

export function createOrganization(data: OrgCreatePayload): Promise<OrgPublic> {
  return api.post<OrgPublic>("/organizations", data);
}

export function updateOrganization(orgId: string, data: OrgUpdatePayload): Promise<OrgPublic> {
  return api.patch<OrgPublic>(`/organizations/${orgId}`, data);
}

export function deleteOrganization(orgId: string): Promise<void> {
  return api.delete(`/organizations/${orgId}`);
}

