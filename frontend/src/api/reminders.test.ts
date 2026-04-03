import { describe, it, expect, vi, beforeEach } from 'vitest';
import { listReminders, getReminder, createReminder, updateReminder, deleteReminder } from './reminders';
import { api } from './client';

vi.mock('./client', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockReminder = {
  id: 'rem-1',
  owner_id: 'owner-1',
  title: 'Call dentist',
  body: null,
  due_at: '2025-06-01T09:00:00Z',
  remind_at: null,
  recurrence: null,
  is_done: false,
  done_at: null,
  person_id: null,
  asset_id: null,
  subscription_id: null,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe('listReminders', () => {
  it('calls GET /reminders with no params', async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [mockReminder], total: 1, skip: 0, limit: 25 });
    const result = await listReminders();
    expect(api.get).toHaveBeenCalledWith('/reminders');
    expect(result.items[0].title).toBe('Call dentist');
  });

  it('appends is_done=false to filter pending', async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [], total: 0, skip: 0, limit: 25 });
    await listReminders({ is_done: false });
    expect(api.get).toHaveBeenCalledWith('/reminders?is_done=false');
  });

  it('appends is_done=true to filter completed', async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [], total: 0, skip: 0, limit: 25 });
    await listReminders({ is_done: true });
    expect(api.get).toHaveBeenCalledWith('/reminders?is_done=true');
  });

  it('appends pagination params', async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [], total: 0, skip: 0, limit: 25 });
    await listReminders({ skip: 0, limit: 10 });
    expect(api.get).toHaveBeenCalledWith('/reminders?skip=0&limit=10');
  });
});

describe('getReminder', () => {
  it('calls GET /reminders/{id}', async () => {
    vi.mocked(api.get).mockResolvedValue(mockReminder);
    const result = await getReminder('rem-1');
    expect(api.get).toHaveBeenCalledWith('/reminders/rem-1');
    expect(result.is_done).toBe(false);
  });
});

describe('createReminder', () => {
  it('calls POST /reminders with required fields', async () => {
    vi.mocked(api.post).mockResolvedValue(mockReminder);
    const result = await createReminder({
      title: 'Call dentist',
      due_at: '2025-06-01T09:00:00Z',
    });
    expect(api.post).toHaveBeenCalledWith('/reminders', {
      title: 'Call dentist',
      due_at: '2025-06-01T09:00:00Z',
    });
    expect(result.title).toBe('Call dentist');
  });

  it('creates recurring reminder', async () => {
    const recurring = { ...mockReminder, recurrence: 'weekly' };
    vi.mocked(api.post).mockResolvedValue(recurring);
    const result = await createReminder({
      title: 'Weekly review',
      due_at: '2025-06-01T09:00:00Z',
      recurrence: 'weekly',
    });
    expect(result.recurrence).toBe('weekly');
  });

  it('creates reminder linked to person', async () => {
    const linked = { ...mockReminder, person_id: 'person-1' };
    vi.mocked(api.post).mockResolvedValue(linked);
    const result = await createReminder({
      title: 'Follow up',
      due_at: '2025-06-01T09:00:00Z',
      person_id: 'person-1',
    });
    expect(result.person_id).toBe('person-1');
  });
});

describe('updateReminder', () => {
  it('calls PATCH /reminders/{id} to mark done', async () => {
    vi.mocked(api.patch).mockResolvedValue({ ...mockReminder, is_done: true, done_at: '2025-05-01T10:00:00Z' });
    const result = await updateReminder('rem-1', { is_done: true });
    expect(api.patch).toHaveBeenCalledWith('/reminders/rem-1', { is_done: true });
    expect(result.is_done).toBe(true);
  });

  it('calls PATCH to update title', async () => {
    vi.mocked(api.patch).mockResolvedValue({ ...mockReminder, title: 'Call doctor' });
    const result = await updateReminder('rem-1', { title: 'Call doctor' });
    expect(result.title).toBe('Call doctor');
  });
});

describe('deleteReminder', () => {
  it('calls DELETE /reminders/{id}', async () => {
    vi.mocked(api.delete).mockResolvedValue(undefined);
    await deleteReminder('rem-1');
    expect(api.delete).toHaveBeenCalledWith('/reminders/rem-1');
  });
});
