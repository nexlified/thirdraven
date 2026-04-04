import { api } from "./client";
import type { Paginated, TermSlim } from "./types";

export interface TaskPublicRead {
  id: string;
  owner_id: string;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  due_date: string | null;
  completed_at: string | null;
  person_id: string | null;
  asset_id: string | null;
  subscription_id: string | null;
  tags: TermSlim[];
  created_at: string;
  updated_at: string;
}

export interface TaskSummary {
  total: number;
  by_status: Record<string, number>;
  overdue: number;
  due_today: number;
}

export interface TaskCreatePayload {
  title: string;
  description?: string | null;
  status?: string;
  priority?: string;
  due_date?: string | null;
  person_id?: string | null;
  asset_id?: string | null;
  subscription_id?: string | null;
  tags?: string[];
}

export type TaskUpdatePayload = Partial<TaskCreatePayload>;

export function listTasks(params: {
  skip?: number;
  limit?: number;
  status?: string;
  priority?: string;
  person_id?: string;
  asset_id?: string;
  subscription_id?: string;
} = {}): Promise<Paginated<TaskPublicRead>> {
  const q = new URLSearchParams();
  if (params.skip !== undefined) q.set("skip", String(params.skip));
  if (params.limit !== undefined) q.set("limit", String(params.limit));
  if (params.status) q.set("status", params.status);
  if (params.priority) q.set("priority", params.priority);
  if (params.person_id) q.set("person_id", params.person_id);
  if (params.asset_id) q.set("asset_id", params.asset_id);
  if (params.subscription_id) q.set("subscription_id", params.subscription_id);
  const qs = q.toString();
  return api.get<Paginated<TaskPublicRead>>(`/tasks${qs ? `?${qs}` : ""}`);
}

export function getTaskSummary(): Promise<TaskSummary> {
  return api.get<TaskSummary>("/tasks/summary");
}

export function getTask(taskId: string): Promise<TaskPublicRead> {
  return api.get<TaskPublicRead>(`/tasks/${taskId}`);
}

export function createTask(data: TaskCreatePayload): Promise<TaskPublicRead> {
  return api.post<TaskPublicRead>("/tasks", data);
}

export function updateTask(taskId: string, data: TaskUpdatePayload): Promise<TaskPublicRead> {
  return api.patch<TaskPublicRead>(`/tasks/${taskId}`, data);
}

export function deleteTask(taskId: string): Promise<void> {
  return api.delete(`/tasks/${taskId}`);
}

