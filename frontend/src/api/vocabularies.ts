import { api } from "./client";

export interface VocabularyPublic {
  id: string;
  name: string;
  machine_name: string;
  description: string | null;
  is_hierarchical: boolean;
  allows_new_terms: boolean;
  is_locked: boolean;
  source_type: string;
  external_provider: string | null;
  is_active: boolean;
  created_at: string;
}

export interface TermPublic {
  id: string;
  vocabulary_id: string;
  name: string;
  slug: string;
  description: string | null;
  parent_id: string | null;
  weight: number;
  external_id: string | null;
  is_active: boolean;
  created_at: string;
}

export interface TermCreate {
  name: string;
  slug: string;
  description?: string;
  weight?: number;
}

export interface TermUpdate {
  name?: string;
  description?: string;
  weight?: number;
  is_active?: boolean;
}

export function listVocabularies(): Promise<VocabularyPublic[]> {
  return api.get<VocabularyPublic[]>("/vocabularies");
}

export function listTerms(
  machineName: string,
  params: { search?: string; skip?: number; limit?: number } = {}
): Promise<TermPublic[]> {
  const q = new URLSearchParams();
  if (params.search) q.set("search", params.search);
  if (params.skip !== undefined) q.set("skip", String(params.skip));
  if (params.limit !== undefined) q.set("limit", String(params.limit));
  const qs = q.toString();
  return api.get<TermPublic[]>(`/vocabularies/${machineName}/terms${qs ? `?${qs}` : ""}`);
}

export function createTerm(machineName: string, data: TermCreate): Promise<TermPublic> {
  return api.post<TermPublic>(`/vocabularies/${machineName}/terms`, data);
}

export function updateTerm(machineName: string, slug: string, data: TermUpdate): Promise<TermPublic> {
  return api.patch<TermPublic>(`/vocabularies/${machineName}/terms/${slug}`, data);
}

export function deleteTerm(machineName: string, slug: string): Promise<void> {
  return api.delete(`/vocabularies/${machineName}/terms/${slug}`);
}
