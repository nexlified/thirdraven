import { api } from "./client";
import type { Paginated } from "./types";

export interface ReminderPublic {
  id: string;
  owner_id: string;
  title: string;
  body: string | null;
  due_at: string;
  remind_at: string | null;
  recurrence: string | null;
  is_done: boolean;
  done_at: string | null;
  person_id: string | null;
  asset_id: string | null;
  subscription_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReminderCreatePayload {
  title: string;
  body?: string | null;
  due_at: string;
  remind_at?: string | null;
  recurrence?: string | null;
  person_id?: string | null;
  asset_id?: string | null;
  subscription_id?: string | null;
}

export interface ReminderUpdatePayload {
  title?: string;
  body?: string | null;
  due_at?: string;
  remind_at?: string | null;
  recurrence?: string | null;
  is_done?: boolean;
}

export function listReminders(params: {
  skip?: number;
  limit?: number;
  is_done?: boolean;
} = {}): Promise<Paginated<ReminderPublic>> {
  const q = new URLSearchParams();
  if (params.skip !== undefined) q.set("skip", String(params.skip));
  if (params.limit !== undefined) q.set("limit", String(params.limit));
  if (params.is_done !== undefined) q.set("is_done", String(params.is_done));
  const qs = q.toString();
  return api.get<Paginated<ReminderPublic>>(`/reminders${qs ? `?${qs}` : ""}`);
}

export function getReminder(id: string): Promise<ReminderPublic> {
  return api.get<ReminderPublic>(`/reminders/${id}`);
}

export function createReminder(data: ReminderCreatePayload): Promise<ReminderPublic> {
  return api.post<ReminderPublic>("/reminders", data);
}

export function updateReminder(id: string, data: ReminderUpdatePayload): Promise<ReminderPublic> {
  return api.patch<ReminderPublic>(`/reminders/${id}`, data);
}

export function deleteReminder(id: string): Promise<void> {
  return api.delete(`/reminders/${id}`);
}
