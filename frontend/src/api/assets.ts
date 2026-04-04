import { api } from "./client";
import type { Paginated, TermSlim } from "./types";

export interface AssetPublicRead {
  id: string;
  owner_id: string;
  name: string;
  category: TermSlim;
  status: TermSlim;
  description: string | null;
  vendor: string | null;
  purchase_date: string | null;
  purchase_price: number | null;
  purchase_price_currency: string | null;
  current_value: number | null;
  tags: TermSlim[];
  location_note: string | null;
  image_url: string | null;
  purchase_url: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface AssetCreatePayload {
  name: string;
  category: string;
  status?: string;
  description?: string | null;
  vendor?: string | null;
  purchase_date?: string | null;
  purchase_price?: number | null;
  purchase_price_currency?: string | null;
  current_value?: number | null;
  tags?: string[];
  location_note?: string | null;
  image_url?: string | null;
  purchase_url?: string | null;
  notes?: string | null;
}

export type AssetUpdatePayload = Partial<AssetCreatePayload>;

export function listAssets(params: {
  skip?: number;
  limit?: number;
  category?: string;
  status?: string;
} = {}): Promise<Paginated<AssetPublicRead>> {
  const q = new URLSearchParams();
  if (params.skip !== undefined) q.set("skip", String(params.skip));
  if (params.limit !== undefined) q.set("limit", String(params.limit));
  if (params.category) q.set("category", params.category);
  if (params.status) q.set("status", params.status);
  const qs = q.toString();
  return api.get<Paginated<AssetPublicRead>>(`/assets${qs ? `?${qs}` : ""}`);
}

export function getAsset(assetId: string, include?: string): Promise<AssetPublicRead> {
  const qs = include ? `?include=${include}` : "";
  return api.get<AssetPublicRead>(`/assets/${assetId}${qs}`);
}

export function createAsset(data: AssetCreatePayload): Promise<AssetPublicRead> {
  return api.post<AssetPublicRead>("/assets", data);
}

export function updateAsset(assetId: string, data: AssetUpdatePayload): Promise<AssetPublicRead> {
  return api.patch<AssetPublicRead>(`/assets/${assetId}`, data);
}

export function deleteAsset(assetId: string): Promise<void> {
  return api.delete(`/assets/${assetId}`);
}
