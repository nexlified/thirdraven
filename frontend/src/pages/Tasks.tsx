import { useEffect, useMemo, useState } from "react";
import { AppLayout } from "../components/AppLayout";
import { listPersons } from "../api/persons";
import type { PersonSlim } from "../api/persons";
import { listTerms } from "../api/vocabularies";
import type { TermPublic } from "../api/vocabularies";
import {
  createTask,
  deleteTask,
  getTaskSummary,
  listTasks,
  updateTask,
} from "../api/tasks";
import type { TaskPublicRead, TaskSummary } from "../api/tasks";

const PAGE_SIZE = 25;
const STATUS_OPTIONS = ["todo", "in-progress", "blocked", "done", "cancelled"];
const PRIORITY_OPTIONS = ["low", "normal", "high", "urgent"];

interface TaskFormState {
  title: string;
  description: string;
  status: string;
  priority: string;
  due_date: string;
  person_id: string;
  tags: string[];
}

const EMPTY_FORM: TaskFormState = {
  title: "",
  description: "",
  status: "todo",
  priority: "normal",
  due_date: "",
  person_id: "",
  tags: [],
};

function formatDate(value: string | null): string {
  if (!value) return "-";
  return new Date(value).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function toForm(task: TaskPublicRead): TaskFormState {
  return {
    title: task.title,
    description: task.description ?? "",
    status: task.status,
    priority: task.priority,
    due_date: task.due_date ?? "",
    person_id: task.person_id ?? "",
    tags: task.tags.map((t) => t.slug),
  };
}

function normalizeCreatePayload(form: TaskFormState) {
  return {
    title: form.title.trim(),
    description: form.description.trim() || undefined,
    status: form.status,
    priority: form.priority,
    due_date: form.due_date || null,
    person_id: form.person_id || null,
    tags: form.tags,
  };
}

function normalizeUpdatePayload(form: TaskFormState) {
  return {
    title: form.title.trim() || undefined,
    description: form.description.trim() || null,
    status: form.status,
    priority: form.priority,
    due_date: form.due_date || null,
    person_id: form.person_id || null,
    tags: form.tags,
  };
}

function TagSelector({
  terms,
  selected,
  onToggle,
}: {
  terms: TermPublic[];
  selected: string[];
  onToggle: (slug: string) => void;
}) {
  if (terms.length === 0) {
    return <p className="task-tags-empty">No `task-tags` vocabulary terms found.</p>;
  }

  return (
    <div className="task-tags-grid">
      {terms.map((term) => {
        const active = selected.includes(term.slug);
        return (
          <button
            key={term.slug}
            type="button"
            className={`task-tag-toggle${active ? " active" : ""}`}
            onClick={() => onToggle(term.slug)}
          >
            {term.name}
          </button>
        );
      })}
    </div>
  );
}

export function Tasks() {
  const [tasks, setTasks] = useState<TaskPublicRead[]>([]);
  const [total, setTotal] = useState(0);
  const [summary, setSummary] = useState<TaskSummary | null>(null);
  const [people, setPeople] = useState<PersonSlim[]>([]);
  const [tagTerms, setTagTerms] = useState<TermPublic[]>([]);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [page, setPage] = useState(0);
  const [reloadKey, setReloadKey] = useState(0);

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [personFilter, setPersonFilter] = useState("");

  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState<TaskFormState>(EMPTY_FORM);

  const [editingTaskId, setEditingTaskId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<TaskFormState>(EMPTY_FORM);

  useEffect(() => {
    Promise.all([
      listPersons({ skip: 0, limit: 500 }),
      listTerms("task-tags", { limit: 200 }),
      getTaskSummary(),
    ])
      .then(([personRes, tagRes, summaryRes]) => {
        setPeople(personRes.items);
        setTagTerms(tagRes);
        setSummary(summaryRes);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load task metadata");
      });
  }, []);

  useEffect(() => {
    setLoading(true);
    setError(null);
    listTasks({
      skip: page * PAGE_SIZE,
      limit: PAGE_SIZE,
      status: statusFilter || undefined,
      priority: priorityFilter || undefined,
      person_id: personFilter || undefined,
    })
      .then((res) => {
        setTasks(res.items);
        setTotal(res.total);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load tasks");
      })
      .finally(() => setLoading(false));
  }, [page, statusFilter, priorityFilter, personFilter, reloadKey]);

  useEffect(() => {
    getTaskSummary()
      .then((res) => setSummary(res))
      .catch(() => {});
  }, [reloadKey]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return tasks;
    return tasks.filter((task) => {
      const haystack = `${task.title} ${task.description ?? ""}`.toLowerCase();
      return haystack.includes(q);
    });
  }, [search, tasks]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  const peopleMap = useMemo(() => {
    return new Map(people.map((p) => [p.id, `${p.first_name} ${p.last_name ?? ""}`.trim()]));
  }, [people]);

  function resetCreateForm() {
    setCreateForm(EMPTY_FORM);
  }

  function toggleTag(form: TaskFormState, slug: string): TaskFormState {
    const selected = form.tags.includes(slug)
      ? form.tags.filter((s) => s !== slug)
      : [...form.tags, slug];
    return { ...form, tags: selected };
  }

  async function handleCreateSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!createForm.title.trim()) return;

    setSubmitting(true);
    setError(null);
    try {
      await createTask(normalizeCreatePayload(createForm));
      setShowCreate(false);
      resetCreateForm();
      setPage(0);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create task");
    } finally {
      setSubmitting(false);
    }
  }

  function startEdit(task: TaskPublicRead) {
    setEditingTaskId(task.id);
    setEditForm(toForm(task));
  }

  function cancelEdit() {
    setEditingTaskId(null);
    setEditForm(EMPTY_FORM);
  }

  async function handleEditSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!editingTaskId || !editForm.title.trim()) return;

    setSubmitting(true);
    setError(null);
    try {
      await updateTask(editingTaskId, normalizeUpdatePayload(editForm));
      cancelEdit();
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update task");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(taskId: string) {
    const confirmed = window.confirm("Delete this task?");
    if (!confirmed) return;

    setSubmitting(true);
    setError(null);
    try {
      await deleteTask(taskId);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete task");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AppLayout
      title="Tasks"
      subtitle={summary ? `${summary.total} total tasks, ${summary.overdue} overdue` : undefined}
      headerRight={
        <button
          className="btn-primary"
          onClick={() => {
            setShowCreate((v) => !v);
            if (!showCreate) cancelEdit();
          }}
        >
          {showCreate ? "Close" : "+ New Task"}
        </button>
      }
    >
      {summary && (
        <div className="task-summary-grid">
          <div className="stat-card">
            <span className="stat-icon">◫</span>
            <div className="stat-body">
              <span className="stat-value">{summary.total}</span>
              <span className="stat-label">Total</span>
            </div>
          </div>
          <div className="stat-card">
            <span className="stat-icon">⚠</span>
            <div className="stat-body">
              <span className="stat-value">{summary.overdue}</span>
              <span className="stat-label">Overdue</span>
            </div>
          </div>
          <div className="stat-card">
            <span className="stat-icon">◷</span>
            <div className="stat-body">
              <span className="stat-value">{summary.due_today}</span>
              <span className="stat-label">Due Today</span>
            </div>
          </div>
          <div className="stat-card">
            <span className="stat-icon">✓</span>
            <div className="stat-body">
              <span className="stat-value">{summary.by_status["done"] ?? 0}</span>
              <span className="stat-label">Done</span>
            </div>
          </div>
        </div>
      )}

      {showCreate && (
        <form className="task-form-panel" onSubmit={handleCreateSubmit}>
          <h3>Create Task</h3>
          <div className="form-row">
            <div className="field">
              <label>Title *</label>
              <input
                type="text"
                value={createForm.title}
                onChange={(e) => setCreateForm((f) => ({ ...f, title: e.target.value }))}
                placeholder="Prepare Q2 budget review"
                required
              />
            </div>
            <div className="field">
              <label>Due date</label>
              <input
                type="date"
                value={createForm.due_date}
                onChange={(e) => setCreateForm((f) => ({ ...f, due_date: e.target.value }))}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="field">
              <label>Status</label>
              <select
                value={createForm.status}
                onChange={(e) => setCreateForm((f) => ({ ...f, status: e.target.value }))}
              >
                {STATUS_OPTIONS.map((status) => (
                  <option key={status} value={status}>{status}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Priority</label>
              <select
                value={createForm.priority}
                onChange={(e) => setCreateForm((f) => ({ ...f, priority: e.target.value }))}
              >
                {PRIORITY_OPTIONS.map((priority) => (
                  <option key={priority} value={priority}>{priority}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="field">
            <label>Linked person</label>
            <select
              value={createForm.person_id}
              onChange={(e) => setCreateForm((f) => ({ ...f, person_id: e.target.value }))}
            >
              <option value="">- none -</option>
              {people.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.first_name} {p.last_name ?? ""}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Description</label>
            <textarea
              value={createForm.description}
              onChange={(e) => setCreateForm((f) => ({ ...f, description: e.target.value }))}
              placeholder="Optional notes"
            />
          </div>

          <div className="field">
            <label>Tags</label>
            <TagSelector
              terms={tagTerms}
              selected={createForm.tags}
              onToggle={(slug) => setCreateForm((f) => toggleTag(f, slug))}
            />
          </div>

          <div className="section-actions">
            <button type="button" className="btn-secondary" onClick={() => setShowCreate(false)}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={submitting || !createForm.title.trim()}>
              {submitting ? "Creating..." : "Create Task"}
            </button>
          </div>
        </form>
      )}

      {editingTaskId && (
        <form className="task-form-panel" onSubmit={handleEditSubmit}>
          <h3>Edit Task</h3>
          <div className="form-row">
            <div className="field">
              <label>Title *</label>
              <input
                type="text"
                value={editForm.title}
                onChange={(e) => setEditForm((f) => ({ ...f, title: e.target.value }))}
                required
              />
            </div>
            <div className="field">
              <label>Due date</label>
              <input
                type="date"
                value={editForm.due_date}
                onChange={(e) => setEditForm((f) => ({ ...f, due_date: e.target.value }))}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="field">
              <label>Status</label>
              <select
                value={editForm.status}
                onChange={(e) => setEditForm((f) => ({ ...f, status: e.target.value }))}
              >
                {STATUS_OPTIONS.map((status) => (
                  <option key={status} value={status}>{status}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Priority</label>
              <select
                value={editForm.priority}
                onChange={(e) => setEditForm((f) => ({ ...f, priority: e.target.value }))}
              >
                {PRIORITY_OPTIONS.map((priority) => (
                  <option key={priority} value={priority}>{priority}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="field">
            <label>Linked person</label>
            <select
              value={editForm.person_id}
              onChange={(e) => setEditForm((f) => ({ ...f, person_id: e.target.value }))}
            >
              <option value="">- none -</option>
              {people.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.first_name} {p.last_name ?? ""}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Description</label>
            <textarea
              value={editForm.description}
              onChange={(e) => setEditForm((f) => ({ ...f, description: e.target.value }))}
            />
          </div>

          <div className="field">
            <label>Tags</label>
            <TagSelector
              terms={tagTerms}
              selected={editForm.tags}
              onToggle={(slug) => setEditForm((f) => toggleTag(f, slug))}
            />
          </div>

          <div className="section-actions">
            <button type="button" className="btn-secondary" onClick={cancelEdit}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={submitting || !editForm.title.trim()}>
              {submitting ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </form>
      )}

      <div className="people-toolbar">
        <input
          className="search-input"
          type="search"
          placeholder="Search current page..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(0); }}>
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((status) => (
            <option key={status} value={status}>{status}</option>
          ))}
        </select>
        <select value={priorityFilter} onChange={(e) => { setPriorityFilter(e.target.value); setPage(0); }}>
          <option value="">All priorities</option>
          {PRIORITY_OPTIONS.map((priority) => (
            <option key={priority} value={priority}>{priority}</option>
          ))}
        </select>
        <select value={personFilter} onChange={(e) => { setPersonFilter(e.target.value); setPage(0); }}>
          <option value="">All people</option>
          {people.map((p) => (
            <option key={p.id} value={p.id}>
              {p.first_name} {p.last_name ?? ""}
            </option>
          ))}
        </select>
      </div>

      {error && <div className="form-error" style={{ marginBottom: 14 }}>{error}</div>}

      {loading ? (
        <div className="splash"><div className="spinner" /></div>
      ) : filtered.length === 0 ? (
        <div className="empty-state" style={{ paddingTop: 80 }}>
          <span className="empty-icon">◫</span>
          <p>{total === 0 ? "No tasks yet. Create your first task." : "No tasks match your search."}</p>
        </div>
      ) : (
        <table className="people-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Status</th>
              <th>Priority</th>
              <th>Due</th>
              <th>Person</th>
              <th>Tags</th>
              <th style={{ width: 110 }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((task) => (
              <tr key={task.id}>
                <td>
                  <div className="person-name">{task.title}</div>
                  {task.description && <div className="person-nickname">{task.description}</div>}
                </td>
                <td>
                  <span className="task-badge">{task.status}</span>
                </td>
                <td>
                  <span className="task-badge">{task.priority}</span>
                </td>
                <td className="person-date">{formatDate(task.due_date)}</td>
                <td className="person-contact">{task.person_id ? (peopleMap.get(task.person_id) ?? "Unknown") : "-"}</td>
                <td>
                  <div className="people-tags">
                    {task.tags.length === 0 ? (
                      <span className="person-contact">-</span>
                    ) : (
                      task.tags.slice(0, 3).map((tag) => (
                        <span key={tag.id} className="tag-pill">{tag.name}</span>
                      ))
                    )}
                    {task.tags.length > 3 && <span className="tag-pill">+{task.tags.length - 3}</span>}
                  </div>
                </td>
                <td>
                  <div className="task-actions">
                    <button className="btn-icon" title="Edit" onClick={() => startEdit(task)}>
                      ✎
                    </button>
                    <button className="btn-icon btn-danger-ghost" title="Delete" onClick={() => handleDelete(task.id)}>
                      ✕
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {totalPages > 1 && (
        <div className="pagination-bar">
          <button
            className="btn-secondary"
            onClick={() => setPage((p) => p - 1)}
            disabled={page === 0}
          >
            ← Prev
          </button>
          <span className="pagination-info">
            Page {page + 1} of {totalPages}
          </span>
          <button
            className="btn-secondary"
            onClick={() => setPage((p) => p + 1)}
            disabled={(page + 1) * PAGE_SIZE >= total}
          >
            Next →
          </button>
        </div>
      )}
    </AppLayout>
  );
}

