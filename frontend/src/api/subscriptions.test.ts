import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  listSubscriptions,
  getSubscriptionSummary,
  createSubscription,
  updateSubscription,
  deleteSubscription,
} from './subscriptions';
import { api } from './client';

vi.mock('./client', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockSub = {
  id: 'sub-1',
  owner_id: 'owner-1',
  name: 'Netflix',
  provider: 'Netflix Inc.',
  category: { id: 'cat-1', name: 'Entertainment', slug: 'entertainment' },
  status: 'active',
  cost: 15.99,
  currency: 'USD',
  payment_mode: 'auto_debit',
  billing_cycle: 'monthly',
  billing_cycle_days: null,
  started_on: '2023-01-01',
  next_billing_date: '2025-05-01',
  trial_ends_on: null,
  cancelled_on: null,
  auto_renews: true,
  url: 'https://netflix.com',
  notes: null,
  asset_id: null,
  tags: [],
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
};

const mockSummary = {
  total_active: 5,
  monthly_cost_by_currency: { USD: 45.97 },
  upcoming_renewals: [],
  cost_by_category: [],
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe('listSubscriptions', () => {
  it('calls GET /subscriptions with no params', async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [mockSub], total: 1, skip: 0, limit: 25 });
    const result = await listSubscriptions();
    expect(api.get).toHaveBeenCalledWith('/subscriptions');
    expect(result.items[0].name).toBe('Netflix');
  });

  it('appends status filter', async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [], total: 0, skip: 0, limit: 25 });
    await listSubscriptions({ status: 'active' });
    expect(api.get).toHaveBeenCalledWith('/subscriptions?status=active');
  });

  it('appends category filter', async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [], total: 0, skip: 0, limit: 25 });
    await listSubscriptions({ category: 'entertainment' });
    expect(api.get).toHaveBeenCalledWith('/subscriptions?category=entertainment');
  });

  it('appends billing_cycle filter', async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [], total: 0, skip: 0, limit: 25 });
    await listSubscriptions({ billing_cycle: 'monthly' });
    expect(api.get).toHaveBeenCalledWith('/subscriptions?billing_cycle=monthly');
  });

  it('appends multiple filters together', async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [], total: 0, skip: 0, limit: 25 });
    await listSubscriptions({ status: 'active', billing_cycle: 'monthly', skip: 0, limit: 10 });
    const url = vi.mocked(api.get).mock.calls[0][0] as string;
    expect(url).toContain('status=active');
    expect(url).toContain('billing_cycle=monthly');
    expect(url).toContain('skip=0');
    expect(url).toContain('limit=10');
  });
});

describe('getSubscriptionSummary', () => {
  it('calls GET /subscriptions/summary', async () => {
    vi.mocked(api.get).mockResolvedValue(mockSummary);
    const result = await getSubscriptionSummary();
    expect(api.get).toHaveBeenCalledWith('/subscriptions/summary');
    expect(result.total_active).toBe(5);
    expect(result.monthly_cost_by_currency['USD']).toBe(45.97);
  });
});

describe('createSubscription', () => {
  it('calls POST /subscriptions with required fields', async () => {
    vi.mocked(api.post).mockResolvedValue(mockSub);
    const result = await createSubscription({ name: 'Netflix', cost: 15.99 });
    expect(api.post).toHaveBeenCalledWith('/subscriptions', { name: 'Netflix', cost: 15.99 });
    expect(result.name).toBe('Netflix');
  });
});

describe('updateSubscription', () => {
  it('calls PATCH /subscriptions/{id}', async () => {
    vi.mocked(api.patch).mockResolvedValue({ ...mockSub, status: 'paused' });
    const result = await updateSubscription('sub-1', { status: 'paused' });
    expect(api.patch).toHaveBeenCalledWith('/subscriptions/sub-1', { status: 'paused' });
    expect(result.status).toBe('paused');
  });
});

describe('deleteSubscription', () => {
  it('calls DELETE /subscriptions/{id}', async () => {
    vi.mocked(api.delete).mockResolvedValue(undefined);
    await deleteSubscription('sub-1');
    expect(api.delete).toHaveBeenCalledWith('/subscriptions/sub-1');
  });
});
