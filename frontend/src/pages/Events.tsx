import { useEffect, useMemo, useState } from "react";
import { AppLayout } from "../components/AppLayout";
import { listPersons } from "../api/persons";
import type { PersonSlim } from "../api/persons";
import { listTerms } from "../api/vocabularies";
import type { TermPublic } from "../api/vocabularies";
import {
  addEventPerson,
  createEvent,
  deleteEvent,
  listEventPersons,
  listEvents,
  removeEventPerson,
  updateEvent,
} from "../api/events";
import type { EventPersonPublic, EventPublic } from "../api/events";

const PAGE_SIZE = 25;

interface EventFormState {
  title: string;
  event_type: string;
  description: string;
  occurred_on: string;
  location: string;
  notes: string;
}

const EMPTY_FORM: EventFormState = {
  title: "",
  event_type: "",
  description: "",
  occurred_on: "",
  location: "",
  notes: "",
};

function toForm(event: EventPublic): EventFormState {
  return {
    title: event.title,
    event_type: event.event_type?.slug ?? "",
    description: event.description ?? "",
    occurred_on: event.occurred_on ?? "",
    location: event.location ?? "",
    notes: event.notes ?? "",
  };
}

function normalizePayload(form: EventFormState) {
  return {
    title: form.title.trim(),
    event_type: form.event_type || null,
    description: form.description.trim() || null,
    occurred_on: form.occurred_on || null,
    location: form.location.trim() || null,
    notes: form.notes.trim() || null,
  };
}

function formatDate(value: string | null): string {
  if (!value) return "-";
  return new Date(value).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function Events() {
  const [events, setEvents] = useState<EventPublic[]>([]);
  const [total, setTotal] = useState(0);
  const [eventTypes, setEventTypes] = useState<TermPublic[]>([]);
  const [people, setPeople] = useState<PersonSlim[]>([]);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [page, setPage] = useState(0);
  const [reloadKey, setReloadKey] = useState(0);
  const [search, setSearch] = useState("");

  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState<EventFormState>(EMPTY_FORM);

  const [editingEventId, setEditingEventId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<EventFormState>(EMPTY_FORM);

  const [attendees, setAttendees] = useState<EventPersonPublic[]>([]);
  const [attendeePersonId, setAttendeePersonId] = useState("");
  const [attendeeRole, setAttendeeRole] = useState("");
  const [loadingAttendees, setLoadingAttendees] = useState(false);

  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      listTerms("event-types", { limit: 100 }),
      listPersons({ skip: 0, limit: 500 }),
    ])
      .then(([typesRes, personRes]) => {
        setEventTypes(typesRes);
        setPeople(personRes.items);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load reference data");
      });
  }, []);

  useEffect(() => {
    setLoading(true);
    setError(null);
    listEvents({ skip: page * PAGE_SIZE, limit: PAGE_SIZE })
      .then((res) => {
        setEvents(res.items);
        setTotal(res.total);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load events");
      })
      .finally(() => setLoading(false));
  }, [page, reloadKey]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return events;
    return events.filter((event) => {
      const haystack = `${event.title} ${event.description ?? ""} ${event.location ?? ""}`.toLowerCase();
      return haystack.includes(q);
    });
  }, [events, search]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  function resetCreateForm() {
    setCreateForm(EMPTY_FORM);
  }

  function cancelEdit() {
    setEditingEventId(null);
    setEditForm(EMPTY_FORM);
    setAttendees([]);
    setAttendeePersonId("");
    setAttendeeRole("");
  }

  async function startEdit(event: EventPublic) {
    setEditingEventId(event.id);
    setEditForm(toForm(event));
    setLoadingAttendees(true);
    setAttendees([]);
    try {
      const rows = await listEventPersons(event.id);
      setAttendees(rows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load attendees");
    } finally {
      setLoadingAttendees(false);
    }
  }

  async function handleCreateSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!createForm.title.trim()) return;

    setSubmitting(true);
    setError(null);
    try {
      await createEvent(normalizePayload(createForm));
      setShowCreate(false);
      resetCreateForm();
      setPage(0);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create event");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleEditSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!editingEventId || !editForm.title.trim()) return;

    setSubmitting(true);
    setError(null);
    try {
      await updateEvent(editingEventId, normalizePayload(editForm));
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update event");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(eventId: string) {
    setSubmitting(true);
    setError(null);
    try {
      await deleteEvent(eventId);
      setConfirmDeleteId(null);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete event");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleAddAttendee() {
    if (!editingEventId || !attendeePersonId) return;

    setSubmitting(true);
    setError(null);
    try {
      await addEventPerson(editingEventId, {
        person_id: attendeePersonId,
        role: attendeeRole.trim() || null,
      });
      const rows = await listEventPersons(editingEventId);
      setAttendees(rows);
      setReloadKey((k) => k + 1);
      setAttendeePersonId("");
      setAttendeeRole("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add attendee");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRemoveAttendee(eventPersonId: string) {
    if (!editingEventId) return;

    setSubmitting(true);
    setError(null);
    try {
      await removeEventPerson(editingEventId, eventPersonId);
      setAttendees((prev) => prev.filter((row) => row.id !== eventPersonId));
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove attendee");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AppLayout
      title="Events"
      subtitle={total > 0 ? `${total} event${total !== 1 ? "s" : ""} recorded` : undefined}
      headerRight={
        <button
          className="btn-primary"
          onClick={() => {
            setShowCreate((v) => !v);
            if (!showCreate) cancelEdit();
          }}
        >
          {showCreate ? "Close" : "+ New Event"}
        </button>
      }
    >
      {showCreate && (
        <form className="task-form-panel" onSubmit={handleCreateSubmit}>
          <h3>Create Event</h3>
          <div className="form-row">
            <div className="field">
              <label>Title *</label>
              <input
                type="text"
                value={createForm.title}
                onChange={(e) => setCreateForm((f) => ({ ...f, title: e.target.value }))}
                placeholder="Quarterly planning dinner"
                required
              />
            </div>
            <div className="field">
              <label>Type</label>
              <select
                value={createForm.event_type}
                onChange={(e) => setCreateForm((f) => ({ ...f, event_type: e.target.value }))}
              >
                <option value="">- none -</option>
                {eventTypes.map((term) => (
                  <option key={term.slug} value={term.slug}>{term.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="field">
              <label>Occurred on</label>
              <input
                type="date"
                value={createForm.occurred_on}
                onChange={(e) => setCreateForm((f) => ({ ...f, occurred_on: e.target.value }))}
              />
            </div>
            <div className="field">
              <label>Location</label>
              <input
                type="text"
                value={createForm.location}
                onChange={(e) => setCreateForm((f) => ({ ...f, location: e.target.value }))}
                placeholder="New York"
              />
            </div>
          </div>

          <div className="field">
            <label>Description</label>
            <textarea
              value={createForm.description}
              onChange={(e) => setCreateForm((f) => ({ ...f, description: e.target.value }))}
              placeholder="Optional description"
            />
          </div>

          <div className="field">
            <label>Notes</label>
            <textarea
              value={createForm.notes}
              onChange={(e) => setCreateForm((f) => ({ ...f, notes: e.target.value }))}
              placeholder="Internal notes"
            />
          </div>

          <div className="section-actions">
            <button type="button" className="btn-secondary" onClick={() => setShowCreate(false)}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={submitting || !createForm.title.trim()}>
              {submitting ? "Creating..." : "Create Event"}
            </button>
          </div>
        </form>
      )}

      {editingEventId && (
        <form className="task-form-panel" onSubmit={handleEditSubmit}>
          <h3>Edit Event</h3>
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
              <label>Type</label>
              <select
                value={editForm.event_type}
                onChange={(e) => setEditForm((f) => ({ ...f, event_type: e.target.value }))}
              >
                <option value="">- none -</option>
                {eventTypes.map((term) => (
                  <option key={term.slug} value={term.slug}>{term.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="field">
              <label>Occurred on</label>
              <input
                type="date"
                value={editForm.occurred_on}
                onChange={(e) => setEditForm((f) => ({ ...f, occurred_on: e.target.value }))}
              />
            </div>
            <div className="field">
              <label>Location</label>
              <input
                type="text"
                value={editForm.location}
                onChange={(e) => setEditForm((f) => ({ ...f, location: e.target.value }))}
              />
            </div>
          </div>

          <div className="field">
            <label>Description</label>
            <textarea
              value={editForm.description}
              onChange={(e) => setEditForm((f) => ({ ...f, description: e.target.value }))}
            />
          </div>

          <div className="field">
            <label>Notes</label>
            <textarea
              value={editForm.notes}
              onChange={(e) => setEditForm((f) => ({ ...f, notes: e.target.value }))}
            />
          </div>

          <div className="field">
            <label>Attendees</label>
            <div className="form-row">
              <select
                value={attendeePersonId}
                onChange={(e) => setAttendeePersonId(e.target.value)}
              >
                <option value="">Select person...</option>
                {people.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.first_name} {p.last_name ?? ""}
                  </option>
                ))}
              </select>
              <input
                type="text"
                value={attendeeRole}
                onChange={(e) => setAttendeeRole(e.target.value)}
                placeholder="Role (optional)"
              />
            </div>
            <div style={{ marginTop: 8 }}>
              <button
                type="button"
                className="btn-secondary"
                onClick={handleAddAttendee}
                disabled={!attendeePersonId || submitting}
              >
                Add Attendee
              </button>
            </div>

            {loadingAttendees ? (
              <div className="person-contact" style={{ marginTop: 8 }}>Loading attendees...</div>
            ) : attendees.length === 0 ? (
              <div className="person-contact" style={{ marginTop: 8 }}>No attendees yet.</div>
            ) : (
              <div style={{ marginTop: 10, display: "flex", flexDirection: "column", gap: 8 }}>
                {attendees.map((row) => (
                  <div key={row.id} className="channel-row">
                    <div style={{ flex: 1 }}>
                      <div className="person-name">{row.person.first_name} {row.person.last_name ?? ""}</div>
                      <div className="person-contact">{row.role ?? "Attendee"}</div>
                    </div>
                    <button
                      type="button"
                      className="btn-icon btn-danger-ghost"
                      title="Remove attendee"
                      onClick={() => handleRemoveAttendee(row.id)}
                      disabled={submitting}
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="section-actions">
            <button type="button" className="btn-secondary" onClick={cancelEdit}>
              Close
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
      </div>

      {error && <div className="form-error" style={{ marginBottom: 14 }}>{error}</div>}

      {loading ? (
        <div className="splash"><div className="spinner" /></div>
      ) : filtered.length === 0 ? (
        <div className="empty-state" style={{ paddingTop: 80 }}>
          <span className="empty-icon">◷</span>
          <p>{total === 0 ? "No events yet. Create your first event." : "No events match your search."}</p>
        </div>
      ) : (
        <table className="people-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Type</th>
              <th>Date</th>
              <th>Location</th>
              <th>Attendees</th>
              <th style={{ width: 130 }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((event) => (
              <tr key={event.id}>
                <td>
                  <div className="person-name">{event.title}</div>
                  {event.description && <div className="person-nickname">{event.description}</div>}
                </td>
                <td className="person-contact">{event.event_type?.name ?? "-"}</td>
                <td className="person-date">{formatDate(event.occurred_on)}</td>
                <td className="person-contact">{event.location ?? "-"}</td>
                <td>
                  <div className="people-tags">
                    {event.persons.length === 0 ? (
                      <span className="person-contact">-</span>
                    ) : (
                      event.persons.slice(0, 2).map((person) => (
                        <span key={person.id} className="tag-pill">
                          {person.first_name}
                        </span>
                      ))
                    )}
                    {event.persons.length > 2 && <span className="tag-pill">+{event.persons.length - 2}</span>}
                  </div>
                </td>
                <td>
                  {confirmDeleteId === event.id ? (
                    <div className="inline-confirm">
                      <button
                        className="btn-icon btn-danger-ghost"
                        onClick={() => handleDelete(event.id)}
                        title="Confirm delete"
                        disabled={submitting}
                      >
                        ✓
                      </button>
                      <button
                        className="btn-icon"
                        onClick={() => setConfirmDeleteId(null)}
                        title="Cancel delete"
                      >
                        ✕
                      </button>
                    </div>
                  ) : (
                    <div className="task-actions">
                      <button className="btn-icon" title="Edit" onClick={() => startEdit(event)}>
                        ✎
                      </button>
                      <button
                        className="btn-icon btn-danger-ghost"
                        title="Delete"
                        onClick={() => setConfirmDeleteId(event.id)}
                      >
                        ✕
                      </button>
                    </div>
                  )}
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

