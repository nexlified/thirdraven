import { describe, it, expect, vi, beforeEach } from 'vitest';
import { listLoans, getLoan, createLoan, updateLoan, deleteLoan } from './loans';
import { api } from './client';

vi.mock('./client', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockLoan = {
  id: 'loan-1',
  owner_id: 'owner-1',
  person_id: 'person-1',
  direction: 'lent',
  loan_type: 'money',
  description: 'Medical expenses',
  amount: 500,
  currency: 'USD',
  item_name: null,
  loaned_on: '2025-01-10',
  due_on: '2025-03-10',
  returned_on: null,
  status: 'outstanding',
  notes: null,
  created_at: '2025-01-10T00:00:00Z',
  updated_at: '2025-01-10T00:00:00Z',
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe('listLoans', () => {
  it('calls GET /loans with no params', async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [mockLoan], total: 1, skip: 0, limit: 25 });
    const result = await listLoans();
    expect(api.get).toHaveBeenCalledWith('/loans');
    expect(result.items[0].direction).toBe('lent');
  });

  it('appends direction filter', async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [], total: 0, skip: 0, limit: 25 });
    await listLoans({ direction: 'borrowed' });
    expect(api.get).toHaveBeenCalledWith('/loans?direction=borrowed');
  });

  it('appends status_filter param', async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [], total: 0, skip: 0, limit: 25 });
    await listLoans({ status_filter: 'outstanding' });
    expect(api.get).toHaveBeenCalledWith('/loans?status_filter=outstanding');
  });

  it('appends pagination params', async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [], total: 0, skip: 25, limit: 25 });
    await listLoans({ skip: 25, limit: 25 });
    expect(api.get).toHaveBeenCalledWith('/loans?skip=25&limit=25');
  });
});

describe('getLoan', () => {
  it('calls GET /loans/{id}', async () => {
    vi.mocked(api.get).mockResolvedValue(mockLoan);
    const result = await getLoan('loan-1');
    expect(api.get).toHaveBeenCalledWith('/loans/loan-1');
    expect(result.amount).toBe(500);
  });
});

describe('createLoan', () => {
  it('calls POST /loans with money loan payload', async () => {
    vi.mocked(api.post).mockResolvedValue(mockLoan);
    const result = await createLoan({
      person_id: 'person-1',
      direction: 'lent',
      loan_type: 'money',
      description: 'Medical expenses',
      amount: 500,
      currency: 'USD',
    });
    expect(api.post).toHaveBeenCalledWith('/loans', expect.objectContaining({
      person_id: 'person-1',
      direction: 'lent',
      loan_type: 'money',
    }));
    expect(result.status).toBe('outstanding');
  });

  it('calls POST /loans with item loan payload', async () => {
    const itemLoan = { ...mockLoan, loan_type: 'item', amount: null, currency: null, item_name: 'Camera' };
    vi.mocked(api.post).mockResolvedValue(itemLoan);
    const result = await createLoan({
      person_id: 'person-1',
      direction: 'lent',
      loan_type: 'item',
      description: 'Lent camera',
      item_name: 'Camera',
    });
    expect(result.item_name).toBe('Camera');
  });
});

describe('updateLoan', () => {
  it('calls PATCH /loans/{id} to mark returned', async () => {
    vi.mocked(api.patch).mockResolvedValue({ ...mockLoan, status: 'returned', returned_on: '2025-03-05' });
    const result = await updateLoan('loan-1', { status: 'returned', returned_on: '2025-03-05' });
    expect(api.patch).toHaveBeenCalledWith('/loans/loan-1', {
      status: 'returned',
      returned_on: '2025-03-05',
    });
    expect(result.status).toBe('returned');
  });
});

describe('deleteLoan', () => {
  it('calls DELETE /loans/{id}', async () => {
    vi.mocked(api.delete).mockResolvedValue(undefined);
    await deleteLoan('loan-1');
    expect(api.delete).toHaveBeenCalledWith('/loans/loan-1');
  });
});
