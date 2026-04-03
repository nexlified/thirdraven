import { describe, it, expect, vi, beforeEach } from 'vitest';
import { listAssets, getAsset, createAsset, updateAsset, deleteAsset } from './assets';
import { api } from './client';

vi.mock('./client', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockAsset = {
  id: 'asset-1',
  owner_id: 'owner-1',
  name: 'MacBook Pro',
  category: { id: 'cat-1', name: 'Hardware', slug: 'hardware' },
  status: { id: 'st-1', name: 'Active', slug: 'active' },
  description: null,
  vendor: 'Apple',
  purchase_date: '2023-06-15',
  purchase_price: 2499.0,
  purchase_price_currency: 'USD',
  current_value: 1800.0,
  tags: [],
  location_note: null,
  image_url: null,
  purchase_url: null,
  notes: null,
  created_at: '2023-06-15T00:00:00Z',
  updated_at: '2023-06-15T00:00:00Z',
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe('listAssets', () => {
  it('calls GET /assets with no params', async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [mockAsset], total: 1, skip: 0, limit: 25 });
    const result = await listAssets();
    expect(api.get).toHaveBeenCalledWith('/assets');
    expect(result.total).toBe(1);
  });

  it('appends category filter to query string', async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [], total: 0, skip: 0, limit: 25 });
    await listAssets({ category: 'hardware', skip: 0, limit: 25 });
    expect(api.get).toHaveBeenCalledWith('/assets?skip=0&limit=25&category=hardware');
  });

  it('appends status filter to query string', async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [], total: 0, skip: 0, limit: 25 });
    await listAssets({ status: 'active' });
    expect(api.get).toHaveBeenCalledWith('/assets?status=active');
  });
});

describe('getAsset', () => {
  it('calls GET /assets/{id}', async () => {
    vi.mocked(api.get).mockResolvedValue(mockAsset);
    const result = await getAsset('asset-1');
    expect(api.get).toHaveBeenCalledWith('/assets/asset-1');
    expect(result.name).toBe('MacBook Pro');
  });

  it('appends include param when provided', async () => {
    vi.mocked(api.get).mockResolvedValue(mockAsset);
    await getAsset('asset-1', 'physical,warranty');
    expect(api.get).toHaveBeenCalledWith('/assets/asset-1?include=physical,warranty');
  });
});

describe('createAsset', () => {
  it('calls POST /assets with payload', async () => {
    vi.mocked(api.post).mockResolvedValue(mockAsset);
    const result = await createAsset({ name: 'MacBook Pro', category: 'hardware' });
    expect(api.post).toHaveBeenCalledWith('/assets', { name: 'MacBook Pro', category: 'hardware' });
    expect(result.name).toBe('MacBook Pro');
  });
});

describe('updateAsset', () => {
  it('calls PATCH /assets/{id} with partial payload', async () => {
    vi.mocked(api.patch).mockResolvedValue({ ...mockAsset, name: 'MacBook Air' });
    const result = await updateAsset('asset-1', { name: 'MacBook Air' });
    expect(api.patch).toHaveBeenCalledWith('/assets/asset-1', { name: 'MacBook Air' });
    expect(result.name).toBe('MacBook Air');
  });
});

describe('deleteAsset', () => {
  it('calls DELETE /assets/{id}', async () => {
    vi.mocked(api.delete).mockResolvedValue(undefined);
    await deleteAsset('asset-1');
    expect(api.delete).toHaveBeenCalledWith('/assets/asset-1');
  });
});
