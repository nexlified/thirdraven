import { useEffect, useMemo, useState } from "react";
import { AppLayout } from "../components/AppLayout";
import { listPersons } from "../api/persons";
import type { PersonSlim } from "../api/persons";
import {
  createReminder,
  deleteReminder,
  listReminders,
  updateReminder,
} from "../api/reminders";
import type { ReminderPublic } from "../api/reminders";

const PAGE_SIZE = 25;
const RECURRENCE_OPTIONS = ["none", "daily", "weekly", "monthly", "annual"];

interface ReminderFormState {
  title: string;
  body: string;
  due_at: string;
  remind_at: string;
  recurrence: string;
  person_id: string;
  is_done: boolean;
}

const EMPTY_FORM: ReminderFormState = {
  title: "",
  body: "",
  due_at: "",
  remind_at: "",
  recurrence: "none",
  person_id: "",
  is_done: false,
};

function formatDateTime(value: string | null): string {
  if (!value) return "-";
  return new Date(value).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

/** Convert ISO datetime string to datetime-local input value (YYYY-MM-DDTHH:mm) */
function toDateTimeLocal(value: string | null): string {
  if (!value) return "";
  return value.slice(0, 16);
}

function toForm(reminder: ReminderPublic): ReminderFormState {
  return {
    title: reminder.title,
    body: reminder.body ?? "",
    due_at: toDateTimeLocal(reminder.due_at),
    remind_at: toDateTimeLocal(reminder.remind_at),
    recurrence: reminder.recurrence ?? "none",
    person_id: reminder.person_id ?? "",
    is_done: reminder.is_done,
  };
}

function normalizeCreatePayload(form: ReminderFormState) {
  return {
    title: form.title.trim(),
    body: form.body.trim() || null,
    due_at: form.due_at ? new Date(form.due_at).toISOString() : "",
    remind_at: form.remind_at ? new Date(form.remind_at).toISOString() : null,
    recurrence: form.recurrence === "none" ? null : form.recurrence,
    person_id: form.person_id || null,
  };
}

function normalizeUpdatePayload(form: ReminderFormState) {
  return {
    title: form.title.trim() || undefined,
    body: form.body.trim() || null,
    due_at: form.due_at ? new Date(form.due_at).toISOString() : undefined,
    remind_at: form.remind_at ? new Date(form.remind_at).toISOString() : null,
    recurrence: form.recurrence === "none" ? null : form.recurrence,
    is_done: form.is_done,
  };
}

export function Reminders() {
  const [reminders, setReminders] = useState<ReminderPublic[]>([]);
  const [total, setTotal] = useState(0);
  const [people, setPeople] = useState<PersonSlim[]>([]);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [page, setPage] = useState(0);
  const [reloadKey, setReloadKey] = useState(0);

  const [search, setSearch] = useState("");
  const [doneFilter, setDoneFilter] = useState<"" | "false" | "true">("");

  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState<ReminderFormState>(EMPTY_FORM);

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<ReminderFormState>(EMPTY_FORM);

  useEffect(() => {
    listPersons({ skip: 0, limit: 500 })
      .then((res) => setPeople(res.items))
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load people");
      });
  }, []);

  useEffect(() => {
    setLoading(true);
    setError(null);
    listReminders({
      skip: page * PAGE_SIZE,
      limit: PAGE_SIZE,
      is_done: doneFilter === "" ? undefined : doneFilter === "true",
    })
      .then((res) => {
        setReminders(res.items);
        setTotal(res.total);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load reminders");
      })
      .finally(() => setLoading(false));
  }, [page, doneFilter, reloadKey]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return reminders;
    return reminders.filter((r) =>
      `${r.title} ${r.body ?? ""}`.toLowerCase().includes(q)
    );
  }, [search, reminders]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  const peopleMap = useMemo(
    () => new Map(people.map((p) => [p.id, `${p.first_name} ${p.last_name ?? ""}`.trim()])),
    [people]
  );

  async function handleMarkDone(reminder: ReminderPublic) {
    setSubmitting(true);
    setError(null);
    try {
      await updateReminder(reminder.id, { is_done: true });
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update reminder");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCreateSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!createForm.title.trim() || !createForm.due_at) return;
    setSubmitting(true);
    setError(null);
    try {
      await createReminder(normalizeCreatePayload(createForm));
      setShowCreate(false);
      setCreateForm(EMPTY_FORM);
      setPage(0);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create reminder");
    } finally {
      setSubmitting(false);
    }
  }

  function startEdit(reminder: ReminderPublic) {
    setEditingId(reminder.id);
    setEditForm(toForm(reminder));
    setShowCreate(false);
  }

  function cancelEdit() {
    setEditingId(null);
    setEditForm(EMPTY_FORM);
  }

  async function handleEditSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!editingId || !editForm.title.trim() || !editForm.due_at) return;
    setSubmitting(true);
    setError(null);
    try {
      await updateReminder(editingId, normalizeUpdatePayload(editForm));
      cancelEdit();
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update reminder");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    if (!window.confirm("Delete this reminder?")) return;
    setSubmitting(true);
    setError(null);
    try {
      await deleteReminder(id);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete reminder");
    } finally {
      setSubmitting(false);
    }
  }

  function ReminderForm({
    form,
    onChange,
    onSubmit,
    onCancel,
    title,
    submitLabel,
    isEdit,
  }: {
    form: ReminderFormState;
    onChange: (f: ReminderFormState) => void;
    onSubmit: (e: React.FormEvent) => void;
    onCancel: () => void;
    title: string;
    submitLabel: string;
    isEdit?: boolean;
  }) {
    return (
      <form className="task-form-panel" onSubmit={onSubmit}>
        <h3>{title}</h3>

        <div className="form-row">
          <div className="field">
            <label>Title *</label>
            <input
              type="text"
              value={form.title}
              onChange={(e) => onChange({ ...form, title: e.target.value })}
              placeholder="Follow up with Alex"
              required
            />
          </div>
          <div className="field">
            <label>Due at *</label>
            <input
              type="datetime-local"
              value={form.due_at}
              onChange={(e) => onChange({ ...form, due_at: e.target.value })}
              required
            />
          </div>
        </div>

        <div className="form-row">
          <div className="field">
            <label>Remind at</label>
            <input
              type="datetime-local"
              value={form.remind_at}
              onChange={(e) => onChange({ ...form, remind_at: e.target.value })}
            />
          </div>
          <div className="field">
            <label>Recurrence</label>
            <select
              value={form.recurrence}
              onChange={(e) => onChange({ ...form, recurrence: e.target.value })}
            >
              {RECURRENCE_OPTIONS.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="field">
          <label>Linked person</label>
          <select
            value={form.person_id}
            onChange={(e) => onChange({ ...form, person_id: e.target.value })}
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
          <label>Body</label>
          <textarea
            value={form.body}
            onChange={(e) => onChange({ ...form, body: e.target.value })}
            placeholder="Optional details"
          />
        </div>

        {isEdit && (
          <div className="field">
            <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
              <input
                type="checkbox"
                checked={form.is_done}
                onChange={(e) => onChange({ ...form, is_done: e.target.checked })}
              />
              Mark as done
            </label>
          </div>
        )}

        <div className="section-actions">
          <button type="button" className="btn-secondary" onClick={onCancel}>
            Cancel
          </button>
          <button
            type="submit"
            className="btn-primary"
            disabled={submitting || !form.title.trim() || !form.due_at}
          >
            {submitting ? "Saving..." : submitLabel}
          </button>
        </div>
      </form>
    );
  }

  const pendingCount = reminders.filter((r) => !r.is_done).length;

  return (
    <AppLayout
      title="Reminders"
      subtitle={total > 0 ? `${total} total, ${pendingCount} pending` : undefined}
      headerRight={
        <button
          className="btn-primary"
          onClick={() => {
            setShowCreate((v) => !v);
            if (!showCreate) cancelEdit();
          }}
        >
          {showCreate ? "Close" : "+ New Reminder"}
        </button>
      }
    >
      {showCreate && (
        <ReminderForm
          form={createForm}
          onChange={setCreateForm}
          onSubmit={handleCreateSubmit}
          onCancel={() => { setShowCreate(false); setCreateForm(EMPTY_FORM); }}
          title="Create Reminder"
          submitLabel="Create Reminder"
        />
      )}

      {editingId && (
        <ReminderForm
          form={editForm}
          onChange={setEditForm}
          onSubmit={handleEditSubmit}
          onCancel={cancelEdit}
          title="Edit Reminder"
          submitLabel="Save Changes"
          isEdit
        />
      )}

      <div className="people-toolbar">
        <input
          className="search-input"
          type="search"
          placeholder="Search current page..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          value={doneFilter}
          onChange={(e) => { setDoneFilter(e.target.value as "" | "false" | "true"); setPage(0); }}
        >
          <option value="">All reminders</option>
          <option value="false">Pending only</option>
          <option value="true">Done only</option>
        </select>
      </div>

      {error && <div className="form-error" style={{ marginBottom: 14 }}>{error}</div>}

      {loading ? (
        <div className="splash"><div className="spinner" /></div>
      ) : filtered.length === 0 ? (
        <div className="empty-state" style={{ paddingTop: 80 }}>
          <span className="empty-icon">◷</span>
          <p>{total === 0 ? "No reminders yet. Create your first." : "No reminders match your search."}</p>
        </div>
      ) : (
        <table className="people-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Due</th>
              <th>Recurrence</th>
              <th>Linked to</th>
              <th>Done</th>
              <th style={{ width: 150 }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((reminder) => (
              <tr key={reminder.id}>
                <td>
                  <div className="person-name" style={reminder.is_done ? { opacity: 0.5 } : undefined}>
                    {reminder.title}
                  </div>
                  {reminder.body && (
                    <div className="person-nickname">
                      {reminder.body.length > 80 ? `${reminder.body.slice(0, 80)}…` : reminder.body}
                    </div>
                  )}
                </td>
                <td className="person-date">{formatDateTime(reminder.due_at)}</td>
                <td className="person-contact">{reminder.recurrence ?? "-"}</td>
                <td className="person-contact">
                  {reminder.person_id
                    ? (peopleMap.get(reminder.person_id) ?? "Unknown")
                    : "-"}
                </td>
                <td className="person-contact">{reminder.is_done ? "✓" : "-"}</td>
                <td>
                  <div className="task-actions">
                    {!reminder.is_done && (
                      <button
                        className="btn-icon"
                        title="Mark done"
                        onClick={() => handleMarkDone(reminder)}
                        disabled={submitting}
                      >
                        ✓
                      </button>
                    )}
                    <button className="btn-icon" title="Edit" onClick={() => startEdit(reminder)}>
                      ✎
                    </button>
                    <button
                      className="btn-icon btn-danger-ghost"
                      title="Delete"
                      onClick={() => handleDelete(reminder.id)}
                    >
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
          <button className="btn-secondary" onClick={() => setPage((p) => p - 1)} disabled={page === 0}>
            ← Prev
          </button>
          <span className="pagination-info">Page {page + 1} of {totalPages}</span>
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
