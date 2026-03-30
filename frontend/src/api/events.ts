import { api } from "./client";
import type { Paginated, PersonSlim, TermSlim } from "./persons";

export interface EventPublic {
  id: string;
  owner_id: string;
  title: string;
  event_type: TermSlim | null;
  description: string | null;
  occurred_on: string | null;
  location: string | null;
  notes: string | null;
  persons: PersonSlim[];
  created_at: string;
  updated_at: string;
}

export interface EventPersonPublic {
  id: string;
  event_id: string;
  person: PersonSlim;
  role: string | null;
  created_at: string;
}

export interface EventCreatePayload {
  title: string;
  event_type?: string | null;
  description?: string | null;
  occurred_on?: string | null;
  location?: string | null;
  notes?: string | null;
}

export type EventUpdatePayload = Partial<EventCreatePayload>;

export interface EventPersonCreatePayload {
  person_id: string;
  role?: string | null;
}

export function listEvents(params: {
  skip?: number;
  limit?: number;
} = {}): Promise<Paginated<EventPublic>> {
  const q = new URLSearchParams();
  if (params.skip !== undefined) q.set("skip", String(params.skip));
  if (params.limit !== undefined) q.set("limit", String(params.limit));
  const qs = q.toString();
  return api.get<Paginated<EventPublic>>(`/events${qs ? `?${qs}` : ""}`);
}

export function getEvent(eventId: string): Promise<EventPublic> {
  return api.get<EventPublic>(`/events/${eventId}`);
}

export function createEvent(data: EventCreatePayload): Promise<EventPublic> {
  return api.post<EventPublic>("/events", data);
}

export function updateEvent(eventId: string, data: EventUpdatePayload): Promise<EventPublic> {
  return api.patch<EventPublic>(`/events/${eventId}`, data);
}

export function deleteEvent(eventId: string): Promise<void> {
  return api.delete(`/events/${eventId}`);
}

export function listEventPersons(eventId: string): Promise<EventPersonPublic[]> {
  return api.get<EventPersonPublic[]>(`/events/${eventId}/persons`);
}

export function addEventPerson(eventId: string, data: EventPersonCreatePayload): Promise<EventPersonPublic> {
  return api.post<EventPersonPublic>(`/events/${eventId}/persons`, data);
}

export function removeEventPerson(eventId: string, eventPersonId: string): Promise<void> {
  return api.delete(`/events/${eventId}/persons/${eventPersonId}`);
}

