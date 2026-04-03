import { api } from "./client";
import type { Paginated, TermSlim } from "./persons";

export interface NotePublicRead {
  id: string;
  owner_id: string;
  title: string;
  body: string | null;
  pinned: boolean;
  person_id: string | null;
  asset_id: string | null;
  subscription_id: string | null;
  event_id: string | null;
  tags: TermSlim[];
  created_at: string;
  updated_at: string;
}

export interface NoteStatistics {
  total: number;
  pinned: number;
  by_attachment: Record<string, number>;
}

export interface NoteCreatePayload {
  title: string;
  body?: string | null;
  pinned?: boolean;
  person_id?: string | null;
  asset_id?: string | null;
  subscription_id?: string | null;
  event_id?: string | null;
  tags?: string[];
}

export type NoteUpdatePayload = Partial<NoteCreatePayload>;

export function listNotes(params: {
  skip?: number;
  limit?: number;
  q?: string;
  pinned?: boolean;
  person_id?: string;
} = {}): Promise<Paginated<NotePublicRead>> {
  const q = new URLSearchParams();
  if (params.skip !== undefined) q.set("skip", String(params.skip));
  if (params.limit !== undefined) q.set("limit", String(params.limit));
  if (params.q) q.set("q", params.q);
  if (params.pinned !== undefined) q.set("pinned", String(params.pinned));
  if (params.person_id) q.set("person_id", params.person_id);
  const qs = q.toString();
  return api.get<Paginated<NotePublicRead>>(`/notes${qs ? `?${qs}` : ""}`);
}

export function getNoteStatistics(): Promise<NoteStatistics> {
  return api.get<NoteStatistics>("/notes/statistics");
}

export function getNote(noteId: string): Promise<NotePublicRead> {
  return api.get<NotePublicRead>(`/notes/${noteId}`);
}

export function createNote(data: NoteCreatePayload): Promise<NotePublicRead> {
  return api.post<NotePublicRead>("/notes", data);
}

export function updateNote(noteId: string, data: NoteUpdatePayload): Promise<NotePublicRead> {
  return api.patch<NotePublicRead>(`/notes/${noteId}`, data);
}

export function deleteNote(noteId: string): Promise<void> {
  return api.delete(`/notes/${noteId}`);
}
