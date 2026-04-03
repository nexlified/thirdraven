import { useEffect, useMemo, useState } from "react";
import { AppLayout } from "../components/AppLayout";
import { listPersons } from "../api/persons";
import type { PersonSlim } from "../api/persons";
import { listTerms } from "../api/vocabularies";
import type { TermPublic } from "../api/vocabularies";
import {
  createNote,
  deleteNote,
  getNoteStatistics,
  listNotes,
  updateNote,
} from "../api/notes";
import type { NotePublicRead, NoteStatistics } from "../api/notes";

const PAGE_SIZE = 25;

interface NoteFormState {
  title: string;
  body: string;
  pinned: boolean;
  person_id: string;
  tags: string[];
}

const EMPTY_FORM: NoteFormState = {
  title: "",
  body: "",
  pinned: false,
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

function toForm(note: NotePublicRead): NoteFormState {
  return {
    title: note.title,
    body: note.body ?? "",
    pinned: note.pinned,
    person_id: note.person_id ?? "",
    tags: note.tags.map((t) => t.slug),
  };
}

function normalizePayload(form: NoteFormState) {
  return {
    title: form.title.trim(),
    body: form.body.trim() || null,
    pinned: form.pinned,
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
  if (terms.length === 0) return null;
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

export function Notes() {
  const [notes, setNotes] = useState<NotePublicRead[]>([]);
  const [total, setTotal] = useState(0);
  const [stats, setStats] = useState<NoteStatistics | null>(null);
  const [people, setPeople] = useState<PersonSlim[]>([]);
  const [tagTerms, setTagTerms] = useState<TermPublic[]>([]);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [page, setPage] = useState(0);
  const [reloadKey, setReloadKey] = useState(0);

  const [search, setSearch] = useState("");
  const [pinnedFilter, setPinnedFilter] = useState<"" | "true" | "false">("");

  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState<NoteFormState>(EMPTY_FORM);

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<NoteFormState>(EMPTY_FORM);

  useEffect(() => {
    Promise.all([
      listPersons({ skip: 0, limit: 500 }),
      listTerms("note-tags", { limit: 200 }),
      getNoteStatistics(),
    ])
      .then(([personRes, tagRes, statsRes]) => {
        setPeople(personRes.items);
        setTagTerms(tagRes);
        setStats(statsRes);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load metadata");
      });
  }, []);

  useEffect(() => {
    setLoading(true);
    setError(null);
    listNotes({
      skip: page * PAGE_SIZE,
      limit: PAGE_SIZE,
      pinned: pinnedFilter === "" ? undefined : pinnedFilter === "true",
    })
      .then((res) => {
        setNotes(res.items);
        setTotal(res.total);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load notes");
      })
      .finally(() => setLoading(false));
  }, [page, pinnedFilter, reloadKey]);

  useEffect(() => {
    getNoteStatistics()
      .then((res) => setStats(res))
      .catch(() => {});
  }, [reloadKey]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return notes;
    return notes.filter((n) =>
      `${n.title} ${n.body ?? ""}`.toLowerCase().includes(q)
    );
  }, [search, notes]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  const peopleMap = useMemo(
    () => new Map(people.map((p) => [p.id, `${p.first_name} ${p.last_name ?? ""}`.trim()])),
    [people]
  );

  function toggleTag(form: NoteFormState, slug: string): NoteFormState {
    const tags = form.tags.includes(slug)
      ? form.tags.filter((s) => s !== slug)
      : [...form.tags, slug];
    return { ...form, tags };
  }

  async function handleCreateSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!createForm.title.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await createNote(normalizePayload(createForm));
      setShowCreate(false);
      setCreateForm(EMPTY_FORM);
      setPage(0);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create note");
    } finally {
      setSubmitting(false);
    }
  }

  function startEdit(note: NotePublicRead) {
    setEditingId(note.id);
    setEditForm(toForm(note));
    setShowCreate(false);
  }

  function cancelEdit() {
    setEditingId(null);
    setEditForm(EMPTY_FORM);
  }

  async function handleEditSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!editingId || !editForm.title.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await updateNote(editingId, normalizePayload(editForm));
      cancelEdit();
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update note");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    if (!window.confirm("Delete this note?")) return;
    setSubmitting(true);
    setError(null);
    try {
      await deleteNote(id);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete note");
    } finally {
      setSubmitting(false);
    }
  }

  function NoteForm({
    form,
    onChange,
    onSubmit,
    onCancel,
    title,
    submitLabel,
  }: {
    form: NoteFormState;
    onChange: (f: NoteFormState) => void;
    onSubmit: (e: React.FormEvent) => void;
    onCancel: () => void;
    title: string;
    submitLabel: string;
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
              placeholder="Meeting notes"
              required
            />
          </div>
          <div className="field" style={{ flexShrink: 1, maxWidth: 200 }}>
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
        </div>

        <div className="field">
          <label>Body</label>
          <textarea
            value={form.body}
            onChange={(e) => onChange({ ...form, body: e.target.value })}
            placeholder="Note content..."
            rows={4}
          />
        </div>

        <div className="field">
          <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={form.pinned}
              onChange={(e) => onChange({ ...form, pinned: e.target.checked })}
            />
            Pin this note
          </label>
        </div>

        {tagTerms.length > 0 && (
          <div className="field">
            <label>Tags</label>
            <TagSelector
              terms={tagTerms}
              selected={form.tags}
              onToggle={(slug) => onChange(toggleTag(form, slug))}
            />
          </div>
        )}

        <div className="section-actions">
          <button type="button" className="btn-secondary" onClick={onCancel}>
            Cancel
          </button>
          <button
            type="submit"
            className="btn-primary"
            disabled={submitting || !form.title.trim()}
          >
            {submitting ? "Saving..." : submitLabel}
          </button>
        </div>
      </form>
    );
  }

  return (
    <AppLayout
      title="Notes"
      subtitle={stats ? `${stats.total} total, ${stats.pinned} pinned` : undefined}
      headerRight={
        <button
          className="btn-primary"
          onClick={() => {
            setShowCreate((v) => !v);
            if (!showCreate) cancelEdit();
          }}
        >
          {showCreate ? "Close" : "+ New Note"}
        </button>
      }
    >
      {stats && (
        <div className="task-summary-grid">
          <div className="stat-card">
            <span className="stat-icon">○</span>
            <div className="stat-body">
              <span className="stat-value">{stats.total}</span>
              <span className="stat-label">Total</span>
            </div>
          </div>
          <div className="stat-card">
            <span className="stat-icon">◈</span>
            <div className="stat-body">
              <span className="stat-value">{stats.pinned}</span>
              <span className="stat-label">Pinned</span>
            </div>
          </div>
        </div>
      )}

      {showCreate && (
        <NoteForm
          form={createForm}
          onChange={setCreateForm}
          onSubmit={handleCreateSubmit}
          onCancel={() => { setShowCreate(false); setCreateForm(EMPTY_FORM); }}
          title="Create Note"
          submitLabel="Create Note"
        />
      )}

      {editingId && (
        <NoteForm
          form={editForm}
          onChange={setEditForm}
          onSubmit={handleEditSubmit}
          onCancel={cancelEdit}
          title="Edit Note"
          submitLabel="Save Changes"
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
          value={pinnedFilter}
          onChange={(e) => { setPinnedFilter(e.target.value as "" | "true" | "false"); setPage(0); }}
        >
          <option value="">All notes</option>
          <option value="true">Pinned only</option>
          <option value="false">Unpinned only</option>
        </select>
      </div>

      {error && <div className="form-error" style={{ marginBottom: 14 }}>{error}</div>}

      {loading ? (
        <div className="splash"><div className="spinner" /></div>
      ) : filtered.length === 0 ? (
        <div className="empty-state" style={{ paddingTop: 80 }}>
          <span className="empty-icon">○</span>
          <p>{total === 0 ? "No notes yet. Create your first note." : "No notes match your search."}</p>
        </div>
      ) : (
        <table className="people-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Pinned</th>
              <th>Person</th>
              <th>Tags</th>
              <th>Created</th>
              <th style={{ width: 110 }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((note) => (
              <tr key={note.id}>
                <td>
                  <div className="person-name">{note.title}</div>
                  {note.body && (
                    <div className="person-nickname">
                      {note.body.length > 80 ? `${note.body.slice(0, 80)}…` : note.body}
                    </div>
                  )}
                </td>
                <td className="person-contact">{note.pinned ? "◈" : "-"}</td>
                <td className="person-contact">
                  {note.person_id ? (peopleMap.get(note.person_id) ?? "Unknown") : "-"}
                </td>
                <td>
                  <div className="people-tags">
                    {note.tags.length === 0 ? (
                      <span className="person-contact">-</span>
                    ) : (
                      note.tags.slice(0, 3).map((tag) => (
                        <span key={tag.id} className="tag-pill">{tag.name}</span>
                      ))
                    )}
                    {note.tags.length > 3 && <span className="tag-pill">+{note.tags.length - 3}</span>}
                  </div>
                </td>
                <td className="person-date">{formatDate(note.created_at)}</td>
                <td>
                  <div className="task-actions">
                    <button className="btn-icon" title="Edit" onClick={() => startEdit(note)}>
                      ✎
                    </button>
                    <button
                      className="btn-icon btn-danger-ghost"
                      title="Delete"
                      onClick={() => handleDelete(note.id)}
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
