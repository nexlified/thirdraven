import { useEffect, useMemo, useState } from "react";
import { AppLayout } from "../components/AppLayout";
import { listCountries } from "../api/reference";
import { listTerms } from "../api/vocabularies";
import type { CountryPublic } from "../api/reference";
import type { TermPublic } from "../api/vocabularies";
import {
  createOrganization,
  deleteOrganization,
  listOrganizations,
  updateOrganization,
} from "../api/organizations";
import type { OrgPublic } from "../api/organizations";

const PAGE_SIZE = 25;

interface OrgFormState {
  name: string;
  type: string;
  description: string;
  website: string;
  email: string;
  phone: string;
  industry: string;
  founded_year: string;
  headquarters_city: string;
  country: string;
  linkedin_url: string;
  notes: string;
  visibility: string;
}

const EMPTY_FORM: OrgFormState = {
  name: "",
  type: "",
  description: "",
  website: "",
  email: "",
  phone: "",
  industry: "",
  founded_year: "",
  headquarters_city: "",
  country: "",
  linkedin_url: "",
  notes: "",
  visibility: "private",
};

function toForm(org: OrgPublic): OrgFormState {
  return {
    name: org.name,
    type: org.type?.slug ?? "",
    description: org.description ?? "",
    website: org.website ?? "",
    email: org.email ?? "",
    phone: org.phone ?? "",
    industry: org.industry?.slug ?? "",
    founded_year: org.founded_year?.toString() ?? "",
    headquarters_city: org.headquarters_city ?? "",
    country: org.country?.alpha2 ?? "",
    linkedin_url: org.linkedin_url ?? "",
    notes: org.notes ?? "",
    visibility: org.visibility ?? "private",
  };
}

function normalizeCreatePayload(form: OrgFormState) {
  return {
    name: form.name.trim(),
    type: form.type || null,
    description: form.description.trim() || null,
    website: form.website.trim() || null,
    email: form.email.trim() || null,
    phone: form.phone.trim() || null,
    industry: form.industry || null,
    founded_year: form.founded_year ? parseInt(form.founded_year, 10) : null,
    headquarters_city: form.headquarters_city.trim() || null,
    country: form.country || null,
    linkedin_url: form.linkedin_url.trim() || null,
    notes: form.notes.trim() || null,
    visibility: form.visibility,
  };
}

function normalizeUpdatePayload(form: OrgFormState) {
  return {
    name: form.name.trim() || undefined,
    type: form.type || null,
    description: form.description.trim() || null,
    website: form.website.trim() || null,
    email: form.email.trim() || null,
    phone: form.phone.trim() || null,
    industry: form.industry || null,
    founded_year: form.founded_year ? parseInt(form.founded_year, 10) : null,
    headquarters_city: form.headquarters_city.trim() || null,
    country: form.country || null,
    linkedin_url: form.linkedin_url.trim() || null,
    notes: form.notes.trim() || null,
    visibility: form.visibility,
  };
}

export function Organizations() {
  const [orgs, setOrgs] = useState<OrgPublic[]>([]);
  const [total, setTotal] = useState(0);
  const [countries, setCountries] = useState<CountryPublic[]>([]);
  const [orgTypes, setOrgTypes] = useState<TermPublic[]>([]);
  const [industries, setIndustries] = useState<TermPublic[]>([]);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [page, setPage] = useState(0);
  const [reloadKey, setReloadKey] = useState(0);

  const [search, setSearch] = useState("");

  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState<OrgFormState>(EMPTY_FORM);

  const [editingOrgId, setEditingOrgId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<OrgFormState>(EMPTY_FORM);

  useEffect(() => {
    Promise.all([
      listCountries(),
      listTerms("org-types", { limit: 100 }),
      listTerms("industries", { limit: 200 }),
    ])
      .then(([countriesRes, typesRes, industriesRes]) => {
        setCountries(countriesRes);
        setOrgTypes(typesRes);
        setIndustries(industriesRes);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load reference data");
      });
  }, []);

  useEffect(() => {
    setLoading(true);
    setError(null);
    listOrganizations({
      skip: page * PAGE_SIZE,
      limit: PAGE_SIZE,
    })
      .then((res) => {
        setOrgs(res.items);
        setTotal(res.total);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load organizations");
      })
      .finally(() => setLoading(false));
  }, [page, reloadKey]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return orgs;
    return orgs.filter((org) => {
      const haystack = `${org.name} ${org.description ?? ""} ${org.headquarters_city ?? ""}`.toLowerCase();
      return haystack.includes(q);
    });
  }, [search, orgs]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  function resetCreateForm() {
    setCreateForm(EMPTY_FORM);
  }

  async function handleCreateSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!createForm.name.trim()) return;

    setSubmitting(true);
    setError(null);
    try {
      await createOrganization(normalizeCreatePayload(createForm));
      setShowCreate(false);
      resetCreateForm();
      setPage(0);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create organization");
    } finally {
      setSubmitting(false);
    }
  }

  function startEdit(org: OrgPublic) {
    setEditingOrgId(org.id);
    setEditForm(toForm(org));
  }

  function cancelEdit() {
    setEditingOrgId(null);
    setEditForm(EMPTY_FORM);
  }

  async function handleEditSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!editingOrgId || !editForm.name.trim()) return;

    setSubmitting(true);
    setError(null);
    try {
      await updateOrganization(editingOrgId, normalizeUpdatePayload(editForm));
      cancelEdit();
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update organization");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(orgId: string) {
    // eslint-disable-next-line no-alert
    const confirmed = window.confirm("Delete this organization?");
    if (!confirmed) return;

    setSubmitting(true);
    setError(null);
    try {
      await deleteOrganization(orgId);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete organization");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AppLayout
      title="Organizations"
      subtitle={total > 0 ? `${total} organization${total !== 1 ? "s" : ""} in your network` : undefined}
      headerRight={
        <button
          className="btn-primary"
          onClick={() => {
            setShowCreate((v) => !v);
            if (!showCreate) cancelEdit();
          }}
        >
          {showCreate ? "Close" : "+ New Organization"}
        </button>
      }
    >
      {showCreate && (
        <form className="task-form-panel" onSubmit={handleCreateSubmit}>
          <h3>Create Organization</h3>
          <div className="form-row">
            <div className="field">
              <label>Name *</label>
              <input
                type="text"
                value={createForm.name}
                onChange={(e) => setCreateForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="Acme Corp"
                required
              />
            </div>
            <div className="field">
              <label>Type</label>
              <select
                value={createForm.type}
                onChange={(e) => setCreateForm((f) => ({ ...f, type: e.target.value }))}
              >
                <option value="">- none -</option>
                {orgTypes.map((term) => (
                  <option key={term.slug} value={term.slug}>{term.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="field">
              <label>Industry</label>
              <select
                value={createForm.industry}
                onChange={(e) => setCreateForm((f) => ({ ...f, industry: e.target.value }))}
              >
                <option value="">- none -</option>
                {industries.map((term) => (
                  <option key={term.slug} value={term.slug}>{term.name}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Founded year</label>
              <input
                type="number"
                value={createForm.founded_year}
                onChange={(e) => setCreateForm((f) => ({ ...f, founded_year: e.target.value }))}
                placeholder="2020"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="field">
              <label>Headquarters city</label>
              <input
                type="text"
                value={createForm.headquarters_city}
                onChange={(e) => setCreateForm((f) => ({ ...f, headquarters_city: e.target.value }))}
                placeholder="San Francisco"
              />
            </div>
            <div className="field">
              <label>Country</label>
              <select
                value={createForm.country}
                onChange={(e) => setCreateForm((f) => ({ ...f, country: e.target.value }))}
              >
                <option value="">- none -</option>
                {countries.map((c) => (
                  <option key={c.alpha2} value={c.alpha2}>{c.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="field">
              <label>Website</label>
              <input
                type="url"
                value={createForm.website}
                onChange={(e) => setCreateForm((f) => ({ ...f, website: e.target.value }))}
                placeholder="https://acme.com"
              />
            </div>
            <div className="field">
              <label>LinkedIn URL</label>
              <input
                type="url"
                value={createForm.linkedin_url}
                onChange={(e) => setCreateForm((f) => ({ ...f, linkedin_url: e.target.value }))}
                placeholder="https://linkedin.com/company/acme"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="field">
              <label>Email</label>
              <input
                type="email"
                value={createForm.email}
                onChange={(e) => setCreateForm((f) => ({ ...f, email: e.target.value }))}
                placeholder="contact@acme.com"
              />
            </div>
            <div className="field">
              <label>Phone</label>
              <input
                type="tel"
                value={createForm.phone}
                onChange={(e) => setCreateForm((f) => ({ ...f, phone: e.target.value }))}
                placeholder="+1 555 0100"
              />
            </div>
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
            <label>Notes</label>
            <textarea
              value={createForm.notes}
              onChange={(e) => setCreateForm((f) => ({ ...f, notes: e.target.value }))}
              placeholder="Internal notes"
            />
          </div>

          <div className="field">
            <label>Visibility</label>
            <select
              value={createForm.visibility}
              onChange={(e) => setCreateForm((f) => ({ ...f, visibility: e.target.value }))}
            >
              <option value="private">Private</option>
              <option value="household">Household</option>
            </select>
          </div>

          <div className="section-actions">
            <button type="button" className="btn-secondary" onClick={() => setShowCreate(false)}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={submitting || !createForm.name.trim()}>
              {submitting ? "Creating..." : "Create Organization"}
            </button>
          </div>
        </form>
      )}

      {editingOrgId && (
        <form className="task-form-panel" onSubmit={handleEditSubmit}>
          <h3>Edit Organization</h3>
          <div className="form-row">
            <div className="field">
              <label>Name *</label>
              <input
                type="text"
                value={editForm.name}
                onChange={(e) => setEditForm((f) => ({ ...f, name: e.target.value }))}
                required
              />
            </div>
            <div className="field">
              <label>Type</label>
              <select
                value={editForm.type}
                onChange={(e) => setEditForm((f) => ({ ...f, type: e.target.value }))}
              >
                <option value="">- none -</option>
                {orgTypes.map((term) => (
                  <option key={term.slug} value={term.slug}>{term.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="field">
              <label>Industry</label>
              <select
                value={editForm.industry}
                onChange={(e) => setEditForm((f) => ({ ...f, industry: e.target.value }))}
              >
                <option value="">- none -</option>
                {industries.map((term) => (
                  <option key={term.slug} value={term.slug}>{term.name}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Founded year</label>
              <input
                type="number"
                value={editForm.founded_year}
                onChange={(e) => setEditForm((f) => ({ ...f, founded_year: e.target.value }))}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="field">
              <label>Headquarters city</label>
              <input
                type="text"
                value={editForm.headquarters_city}
                onChange={(e) => setEditForm((f) => ({ ...f, headquarters_city: e.target.value }))}
              />
            </div>
            <div className="field">
              <label>Country</label>
              <select
                value={editForm.country}
                onChange={(e) => setEditForm((f) => ({ ...f, country: e.target.value }))}
              >
                <option value="">- none -</option>
                {countries.map((c) => (
                  <option key={c.alpha2} value={c.alpha2}>{c.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="field">
              <label>Website</label>
              <input
                type="url"
                value={editForm.website}
                onChange={(e) => setEditForm((f) => ({ ...f, website: e.target.value }))}
              />
            </div>
            <div className="field">
              <label>LinkedIn URL</label>
              <input
                type="url"
                value={editForm.linkedin_url}
                onChange={(e) => setEditForm((f) => ({ ...f, linkedin_url: e.target.value }))}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="field">
              <label>Email</label>
              <input
                type="email"
                value={editForm.email}
                onChange={(e) => setEditForm((f) => ({ ...f, email: e.target.value }))}
              />
            </div>
            <div className="field">
              <label>Phone</label>
              <input
                type="tel"
                value={editForm.phone}
                onChange={(e) => setEditForm((f) => ({ ...f, phone: e.target.value }))}
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
            <label>Visibility</label>
            <select
              value={editForm.visibility}
              onChange={(e) => setEditForm((f) => ({ ...f, visibility: e.target.value }))}
            >
              <option value="private">Private</option>
              <option value="household">Household</option>
            </select>
          </div>

          <div className="section-actions">
            <button type="button" className="btn-secondary" onClick={cancelEdit}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={submitting || !editForm.name.trim()}>
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
          <span className="empty-icon">⬡</span>
          <p>{total === 0 ? "No organizations yet. Create your first organization." : "No organizations match your search."}</p>
        </div>
      ) : (
        <table className="people-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Industry</th>
              <th>City / Country</th>
              <th>Website</th>
              <th>Email</th>
              <th>Founded</th>
              <th style={{ width: 110 }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((org) => (
              <tr key={org.id}>
                <td>
                  <div className="person-name">{org.name}</div>
                  {org.description && <div className="person-nickname">{org.description}</div>}
                </td>
                <td className="person-contact">{org.type?.name ?? "-"}</td>
                <td className="person-contact">{org.industry?.name ?? "-"}</td>
                <td className="person-contact">
                  {org.headquarters_city && org.country
                    ? `${org.headquarters_city}, ${org.country.alpha2}`
                    : org.headquarters_city
                    ? org.headquarters_city
                    : org.country
                    ? org.country.alpha2
                    : "-"}
                </td>
                <td>
                  {org.website ? (
                    <a href={org.website} target="_blank" rel="noopener noreferrer" className="person-contact">
                      website
                    </a>
                  ) : (
                    <span className="person-contact">-</span>
                  )}
                </td>
                <td className="person-contact">{org.email ?? "-"}</td>
                <td className="person-date">{org.founded_year ?? "-"}</td>
                <td>
                  <div className="task-actions">
                    <button className="btn-icon" title="Edit" onClick={() => startEdit(org)}>
                      ✎
                    </button>
                    <button className="btn-icon btn-danger-ghost" title="Delete" onClick={() => handleDelete(org.id)}>
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

