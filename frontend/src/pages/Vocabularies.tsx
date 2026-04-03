import { useEffect, useState } from "react";
import { AppLayout } from "../components/AppLayout";
import {
  listVocabularies,
  listTerms,
  createTerm,
  updateTerm,
  deleteTerm,
} from "../api/vocabularies";
import type { VocabularyPublic, TermPublic } from "../api/vocabularies";

function slugify(name: string): string {
  return name
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

export function Vocabularies() {
  const [vocabularies, setVocabularies] = useState<VocabularyPublic[]>([]);
  const [selectedVocab, setSelectedVocab] = useState<VocabularyPublic | null>(null);
  const [terms, setTerms] = useState<TermPublic[]>([]);
  const [termSearch, setTermSearch] = useState("");
  const [loadingVocabs, setLoadingVocabs] = useState(true);
  const [loadingTerms, setLoadingTerms] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Add form
  const [addingTerm, setAddingTerm] = useState(false);
  const [newTerm, setNewTerm] = useState({ name: "", slug: "", description: "", weight: "0", icon: "" });
  const [slugManuallyEdited, setSlugManuallyEdited] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);
  const [addBusy, setAddBusy] = useState(false);

  // Edit
  const [editingSlug, setEditingSlug] = useState<string | null>(null);
  const [editDraft, setEditDraft] = useState({ name: "", description: "", weight: "0", icon: "" });
  const [editBusy, setEditBusy] = useState(false);

  // Delete
  const [confirmDeleteSlug, setConfirmDeleteSlug] = useState<string | null>(null);
  const [deleteBusy, setDeleteBusy] = useState(false);

  useEffect(() => {
    listVocabularies()
      .then((vocs) => {
        setVocabularies(vocs);
        if (vocs.length > 0) selectVocab(vocs[0]);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load vocabularies"))
      .finally(() => setLoadingVocabs(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function selectVocab(vocab: VocabularyPublic) {
    setSelectedVocab(vocab);
    setTermSearch("");
    setAddingTerm(false);
    setEditingSlug(null);
    setConfirmDeleteSlug(null);
    setNewTerm({ name: "", slug: "", description: "", weight: "0", icon: "" });
    setLoadingTerms(true);
    try {
      const ts = await listTerms(vocab.machine_name, { limit: 200 });
      setTerms(ts);
    } catch {
      setTerms([]);
    } finally {
      setLoadingTerms(false);
    }
  }

  async function reloadTerms() {
    if (!selectedVocab) return;
    const ts = await listTerms(selectedVocab.machine_name, { limit: 200 });
    setTerms(ts);
  }

  function handleNewNameChange(name: string) {
    setNewTerm((t) => ({
      ...t,
      name,
      slug: slugManuallyEdited ? t.slug : slugify(name),
    }));
  }

  async function handleAddTerm() {
    if (!selectedVocab || !newTerm.name || !newTerm.slug) return;
    setAddBusy(true);
    setAddError(null);
    try {
      await createTerm(selectedVocab.machine_name, {
        name: newTerm.name,
        slug: newTerm.slug,
        description: newTerm.description || undefined,
        weight: parseInt(newTerm.weight) || 0,
        icon: newTerm.icon || null,
      });
      setAddingTerm(false);
      setNewTerm({ name: "", slug: "", description: "", weight: "0", icon: "" });
      setSlugManuallyEdited(false);
      await reloadTerms();
    } catch (err) {
      setAddError(err instanceof Error ? err.message : "Failed to create term");
    } finally {
      setAddBusy(false);
    }
  }

  function startEdit(term: TermPublic) {
    setEditingSlug(term.slug);
    setEditDraft({ name: term.name, description: term.description ?? "", weight: String(term.weight), icon: term.icon ?? "" });
    setConfirmDeleteSlug(null);
  }

  async function saveEdit(slug: string) {
    if (!selectedVocab) return;
    setEditBusy(true);
    try {
      await updateTerm(selectedVocab.machine_name, slug, {
        name: editDraft.name,
        description: editDraft.description || undefined,
        weight: parseInt(editDraft.weight) || 0,
        icon: editDraft.icon || null,
      });
      setEditingSlug(null);
      await reloadTerms();
    } finally {
      setEditBusy(false);
    }
  }

  async function handleDelete(slug: string) {
    if (!selectedVocab) return;
    setDeleteBusy(true);
    try {
      await deleteTerm(selectedVocab.machine_name, slug);
      setConfirmDeleteSlug(null);
      await reloadTerms();
    } finally {
      setDeleteBusy(false);
    }
  }

  const filteredTerms = termSearch.trim()
    ? terms.filter((t) => t.name.toLowerCase().includes(termSearch.toLowerCase()))
    : terms;

  const canAdd = selectedVocab && !selectedVocab.is_locked && selectedVocab.allows_new_terms;

  return (
    <AppLayout title="Vocabulary" subtitle="Manage dropdown options and term lists">
      {loadingVocabs ? (
        <div className="splash"><div className="spinner" /></div>
      ) : error ? (
        <div className="form-error">{error}</div>
      ) : (
        <div className="vocab-page">
          {/* Sidebar */}
          <div className="vocab-sidebar">
            {vocabularies.map((v) => (
              <div
                key={v.machine_name}
                className={`vocab-sidebar-item${selectedVocab?.machine_name === v.machine_name ? " active" : ""}`}
                onClick={() => selectVocab(v)}
              >
                <span className="vocab-sidebar-name">{v.name}</span>
                <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
                  {v.is_locked && <span className="locked-badge">🔒</span>}
                  {selectedVocab?.machine_name === v.machine_name && (
                    <span className="vocab-count">{terms.length}</span>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Content */}
          <div className="vocab-content">
            {!selectedVocab ? (
              <div className="vocab-empty">Select a vocabulary to manage its terms.</div>
            ) : (
              <>
                <div style={{ marginBottom: 12 }}>
                  <h3 style={{ fontSize: 16, marginBottom: 4 }}>{selectedVocab.name}</h3>
                  {selectedVocab.description && (
                    <p style={{ fontSize: 12, color: "var(--text-muted)" }}>{selectedVocab.description}</p>
                  )}
                </div>

                <div className="vocab-toolbar">
                  <input
                    className="search-input"
                    type="search"
                    placeholder="Search terms…"
                    value={termSearch}
                    onChange={(e) => setTermSearch(e.target.value)}
                  />
                  {canAdd && (
                    <button
                      className="btn-primary"
                      onClick={() => { setAddingTerm(true); setAddError(null); }}
                      disabled={addingTerm}
                    >
                      + Add Term
                    </button>
                  )}
                  {selectedVocab.is_locked && (
                    <span className="locked-badge" style={{ fontSize: 12 }}>🔒 Locked — read only</span>
                  )}
                </div>

                {loadingTerms ? (
                  <div className="splash" style={{ minHeight: 120 }}><div className="spinner" /></div>
                ) : (
                  <div className="term-list">
                    {filteredTerms.length === 0 && !addingTerm && (
                      <div className="vocab-empty">
                        {termSearch ? "No terms match your search." : "No terms yet."}
                      </div>
                    )}

                    {filteredTerms.map((term) => (
                      <div key={term.slug}>
                        {editingSlug === term.slug ? (
                          <div className="term-edit-row">
                            <div className="field" style={{ flex: 2 }}>
                              <label>Name</label>
                              <input
                                type="text"
                                value={editDraft.name}
                                onChange={(e) => setEditDraft((d) => ({ ...d, name: e.target.value }))}
                                autoFocus
                              />
                            </div>
                            <div className="field" style={{ flex: 2 }}>
                              <label>Description</label>
                              <input
                                type="text"
                                value={editDraft.description}
                                onChange={(e) => setEditDraft((d) => ({ ...d, description: e.target.value }))}
                                placeholder="Optional"
                              />
                            </div>
                            <div className="field" style={{ flex: 1 }}>
                              <label>Icon</label>
                              <input
                                type="text"
                                value={editDraft.icon}
                                onChange={(e) => setEditDraft((d) => ({ ...d, icon: e.target.value }))}
                                placeholder="e.g. star"
                              />
                            </div>
                            <div className="field" style={{ flex: "0 0 70px" }}>
                              <label>Weight</label>
                              <input
                                type="number"
                                value={editDraft.weight}
                                onChange={(e) => setEditDraft((d) => ({ ...d, weight: e.target.value }))}
                              />
                            </div>
                            <div style={{ display: "flex", gap: 6, alignItems: "flex-end", paddingBottom: 1 }}>
                              <button className="btn-primary" onClick={() => saveEdit(term.slug)} disabled={editBusy} style={{ padding: "9px 14px" }}>
                                {editBusy ? "…" : "Save"}
                              </button>
                              <button className="btn-secondary" onClick={() => setEditingSlug(null)} style={{ padding: "9px 14px" }}>
                                Cancel
                              </button>
                            </div>
                          </div>
                        ) : confirmDeleteSlug === term.slug ? (
                          <div className="term-row">
                            <div className="inline-confirm" style={{ flex: 1 }}>
                              <span>Delete "{term.name}"?</span>
                              <button
                                className="btn-icon btn-danger-ghost"
                                onClick={() => handleDelete(term.slug)}
                                disabled={deleteBusy}
                              >
                                {deleteBusy ? "…" : "Delete"}
                              </button>
                              <button className="btn-secondary" onClick={() => setConfirmDeleteSlug(null)} style={{ fontSize: 12, padding: "4px 8px" }}>
                                Cancel
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div className="term-row">
                            {term.icon && (
                              <span className="term-icon" title={term.icon}>{term.icon}</span>
                            )}
                            <span className="term-name">{term.name}</span>
                            <span className="term-slug">{term.slug}</span>
                            {term.description && (
                              <span className="term-description">{term.description}</span>
                            )}
                            <span className="term-weight">{term.weight !== 0 ? term.weight : ""}</span>
                            <button className="btn-icon" onClick={() => startEdit(term)} title="Edit">✎</button>
                            {!selectedVocab.is_locked && (
                              <button
                                className="btn-icon btn-danger-ghost"
                                onClick={() => { setConfirmDeleteSlug(term.slug); setEditingSlug(null); }}
                                title="Delete"
                              >
                                ✕
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                    ))}

                    {addingTerm && (
                      <div className="term-add-form">
                        <div className="field" style={{ flex: 2 }}>
                          <label>Name *</label>
                          <input
                            type="text"
                            value={newTerm.name}
                            onChange={(e) => handleNewNameChange(e.target.value)}
                            placeholder="Engineer"
                            autoFocus
                          />
                        </div>
                        <div className="field" style={{ flex: 1 }}>
                          <label>Slug *</label>
                          <input
                            type="text"
                            value={newTerm.slug}
                            onChange={(e) => { setNewTerm((t) => ({ ...t, slug: e.target.value })); setSlugManuallyEdited(true); }}
                            placeholder="engineer"
                          />
                        </div>
                        <div className="field" style={{ flex: 2 }}>
                          <label>Description</label>
                          <input
                            type="text"
                            value={newTerm.description}
                            onChange={(e) => setNewTerm((t) => ({ ...t, description: e.target.value }))}
                            placeholder="Optional"
                          />
                        </div>
                        <div className="field" style={{ flex: 1 }}>
                          <label>Icon</label>
                          <input
                            type="text"
                            value={newTerm.icon}
                            onChange={(e) => setNewTerm((t) => ({ ...t, icon: e.target.value }))}
                            placeholder="e.g. star"
                          />
                        </div>
                        <div className="field" style={{ flex: "0 0 70px" }}>
                          <label>Weight</label>
                          <input
                            type="number"
                            value={newTerm.weight}
                            onChange={(e) => setNewTerm((t) => ({ ...t, weight: e.target.value }))}
                          />
                        </div>
                        <div style={{ display: "flex", gap: 6, alignItems: "flex-end", paddingBottom: 1 }}>
                          <button
                            className="btn-primary"
                            onClick={handleAddTerm}
                            disabled={addBusy || !newTerm.name || !newTerm.slug}
                            style={{ padding: "9px 14px" }}
                          >
                            {addBusy ? "…" : "Add"}
                          </button>
                          <button className="btn-secondary" onClick={() => { setAddingTerm(false); setAddError(null); }} style={{ padding: "9px 14px" }}>
                            Cancel
                          </button>
                        </div>
                        {addError && <div className="form-error" style={{ width: "100%" }}>{addError}</div>}
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </AppLayout>
  );
}
