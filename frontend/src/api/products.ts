import { api, buildQuery } from "./client";
import type { Paginated, TermSlim } from "./types";

export interface ProductPublic {
  id: string;
  owner_id: string;
  name: string;
  brand: string | null;
  category: TermSlim | null;
  unit: string | null;
  barcode: string | null;
  priceraven_product_id: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProductSlim {
  id: string;
  name: string;
  brand: string | null;
  unit: string | null;
}

export interface TransactionItemPublic {
  id: string;
  transaction_id: string;
  product_id: string | null;
  product: ProductSlim | null;
  raw_name: string;
  quantity: number;
  unit: string | null;
  unit_price: number;
  total_price: number;
  currency: string;
  discount: number;
  store_name: string | null;
  created_at: string;
}

export function listProducts(params: {
  skip?: number;
  limit?: number;
  category?: string;
  search?: string;
} = {}): Promise<Paginated<ProductPublic>> {
  const qs = buildQuery(params);
  return api.get<Paginated<ProductPublic>>(`/products${qs ? `?${qs}` : ""}`);
}

export function createProduct(data: object): Promise<ProductPublic> {
  return api.post<ProductPublic>("/products", data);
}

export function updateProduct(id: string, data: object): Promise<ProductPublic> {
  return api.patch<ProductPublic>(`/products/${id}`, data);
}

export function deleteProduct(id: string): Promise<void> {
  return api.delete(`/products/${id}`);
}

export function getProductItems(id: string, params: {
  skip?: number;
  limit?: number;
} = {}): Promise<Paginated<TransactionItemPublic>> {
  const qs = buildQuery(params);
  return api.get<Paginated<TransactionItemPublic>>(`/products/${id}/items${qs ? `?${qs}` : ""}`);
}

