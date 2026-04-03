import { describe, it, expect, vi, beforeEach } from 'vitest';
import { listNotes, getNoteStatistics, createNote, updateNote, deleteNote } from './notes';
import { api } from './client';

vi.mock('./client', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockNote = {
  id: 'note-1',
  owner_id: 'owner-1',
  title: 'Meeting notes',
  body: 'Discussed Q2 plans',
  pinned: false,
  person_id: null,
  asset_id: null,
  subscription_id: null,
  event_id: null,
  tags: [],
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe('listNotes', () => {
  it('calls GET /notes with no params', async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [mockNote], total: 1, skip: 0, limit: 25 });
    const result = await listNotes();
    expect(api.get).toHaveBeenCalledWith('/notes');
    expect(result.items[0].title).toBe('Meeting notes');
  });

  it('appends pinned=true filter', async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [], total: 0, skip: 0, limit: 25 });
    await listNotes({ pinned: true });
    expect(api.get).toHaveBeenCalledWith('/notes?pinned=true');
  });

  it('appends pinned=false filter', async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [], total: 0, skip: 0, limit: 25 });
    await listNotes({ pinned: false });
    expect(api.get).toHaveBeenCalledWith('/notes?pinned=false');
  });

  it('appends q (search) param', async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [], total: 0, skip: 0, limit: 25 });
    await listNotes({ q: 'meeting' });
    expect(api.get).toHaveBeenCalledWith('/notes?q=meeting');
  });

  it('appends person_id filter', async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [], total: 0, skip: 0, limit: 25 });
    await listNotes({ person_id: 'person-abc' });
    expect(api.get).toHaveBeenCalledWith('/notes?person_id=person-abc');
  });
});

describe('getNoteStatistics', () => {
  it('calls GET /notes/statistics', async () => {
    vi.mocked(api.get).mockResolvedValue({ total: 10, pinned: 3, by_attachment: {} });
    const stats = await getNoteStatistics();
    expect(api.get).toHaveBeenCalledWith('/notes/statistics');
    expect(stats.total).toBe(10);
    expect(stats.pinned).toBe(3);
  });
});

describe('createNote', () => {
  it('calls POST /notes with payload', async () => {
    vi.mocked(api.post).mockResolvedValue(mockNote);
    const result = await createNote({ title: 'Meeting notes', body: 'Discussed Q2 plans' });
    expect(api.post).toHaveBeenCalledWith('/notes', {
      title: 'Meeting notes',
      body: 'Discussed Q2 plans',
    });
    expect(result.title).toBe('Meeting notes');
  });

  it('creates pinned note', async () => {
    vi.mocked(api.post).mockResolvedValue({ ...mockNote, pinned: true });
    const result = await createNote({ title: 'Important', pinned: true });
    expect(result.pinned).toBe(true);
  });
});

describe('updateNote', () => {
  it('calls PATCH /notes/{id}', async () => {
    vi.mocked(api.patch).mockResolvedValue({ ...mockNote, pinned: true });
    const result = await updateNote('note-1', { pinned: true });
    expect(api.patch).toHaveBeenCalledWith('/notes/note-1', { pinned: true });
    expect(result.pinned).toBe(true);
  });
});

describe('deleteNote', () => {
  it('calls DELETE /notes/{id}', async () => {
    vi.mocked(api.delete).mockResolvedValue(undefined);
    await deleteNote('note-1');
    expect(api.delete).toHaveBeenCalledWith('/notes/note-1');
  });
});
