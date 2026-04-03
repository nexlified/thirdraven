import { useEffect, useMemo, useState } from "react";
import { AppLayout } from "../components/AppLayout";
import { listTerms } from "../api/vocabularies";
import type { TermPublic } from "../api/vocabularies";
import {
  createAsset,
  deleteAsset,
  listAssets,
  updateAsset,
} from "../api/assets";
import type { AssetPublicRead } from "../api/assets";

const PAGE_SIZE = 25;

interface AssetFormState {
  name: string;
  category: string;
  status: string;
  description: string;
  vendor: string;
  purchase_date: string;
  purchase_price: string;
  purchase_price_currency: string;
  current_value: string;
  location_note: string;
  notes: string;
}

const EMPTY_FORM: AssetFormState = {
  name: "",
  category: "",
  status: "active",
  description: "",
  vendor: "",
  purchase_date: "",
  purchase_price: "",
  purchase_price_currency: "USD",
  current_value: "",
  location_note: "",
  notes: "",
};

function formatDate(value: string | null): string {
  if (!value) return "-";
  return new Date(value).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatCurrency(amount: number | null, currency: string | null): string {
  if (amount == null) return "-";
  const cur = currency ?? "USD";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: cur }).format(amount);
}

function toForm(asset: AssetPublicRead): AssetFormState {
  return {
    name: asset.name,
    category: asset.category.slug,
    status: asset.status.slug,
    description: asset.description ?? "",
    vendor: asset.vendor ?? "",
    purchase_date: asset.purchase_date ?? "",
    purchase_price: asset.purchase_price != null ? String(asset.purchase_price) : "",
    purchase_price_currency: asset.purchase_price_currency ?? "USD",
    current_value: asset.current_value != null ? String(asset.current_value) : "",
    location_note: asset.location_note ?? "",
    notes: asset.notes ?? "",
  };
}

function normalizePayload(form: AssetFormState) {
  return {
    name: form.name.trim(),
    category: form.category,
    status: form.status,
    description: form.description.trim() || null,
    vendor: form.vendor.trim() || null,
    purchase_date: form.purchase_date || null,
    purchase_price: form.purchase_price ? parseFloat(form.purchase_price) : null,
    purchase_price_currency: form.purchase_price_currency || null,
    current_value: form.current_value ? parseFloat(form.current_value) : null,
    location_note: form.location_note.trim() || null,
    notes: form.notes.trim() || null,
  };
}

function AssetForm({
  form,
  onChange,
  onSubmit,
  onCancel,
  submitting,
  categoryTerms,
  statusTerms,
  title,
  submitLabel,
}: {
  form: AssetFormState;
  onChange: (f: AssetFormState) => void;
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
  submitting: boolean;
  categoryTerms: TermPublic[];
  statusTerms: TermPublic[];
  title: string;
  submitLabel: string;
}) {
  function set(key: keyof AssetFormState, value: string) {
    onChange({ ...form, [key]: value });
  }

  return (
    <form className="task-form-panel" onSubmit={onSubmit}>
      <h3>{title}</h3>

      <div className="form-row">
        <div className="field">
          <label>Name *</label>
          <input
            type="text"
            value={form.name}
            onChange={(e) => set("name", e.target.value)}
            placeholder="MacBook Pro 16-inch"
            required
          />
        </div>
        <div className="field">
          <label>Category *</label>
          <select
            value={form.category}
            onChange={(e) => set("category", e.target.value)}
            required
          >
            <option value="">- select -</option>
            {categoryTerms.map((t) => (
              <option key={t.slug} value={t.slug}>{t.name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="form-row">
        <div className="field">
          <label>Status</label>
          <select value={form.status} onChange={(e) => set("status", e.target.value)}>
            {statusTerms.map((t) => (
              <option key={t.slug} value={t.slug}>{t.name}</option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>Vendor</label>
          <input
            type="text"
            value={form.vendor}
            onChange={(e) => set("vendor", e.target.value)}
            placeholder="Apple"
          />
        </div>
      </div>

      <div className="form-row">
        <div className="field">
          <label>Purchase date</label>
          <input
            type="date"
            value={form.purchase_date}
            onChange={(e) => set("purchase_date", e.target.value)}
          />
        </div>
        <div className="field">
          <label>Purchase price</label>
          <input
            type="number"
            step="0.01"
            min="0"
            value={form.purchase_price}
            onChange={(e) => set("purchase_price", e.target.value)}
            placeholder="2499.00"
          />
        </div>
        <div className="field">
          <label>Currency</label>
          <input
            type="text"
            maxLength={3}
            value={form.purchase_price_currency}
            onChange={(e) => set("purchase_price_currency", e.target.value.toUpperCase())}
            placeholder="USD"
            style={{ width: 72 }}
          />
        </div>
      </div>

      <div className="form-row">
        <div className="field">
          <label>Current value</label>
          <input
            type="number"
            step="0.01"
            min="0"
            value={form.current_value}
            onChange={(e) => set("current_value", e.target.value)}
            placeholder="1800.00"
          />
        </div>
        <div className="field">
          <label>Location note</label>
          <input
            type="text"
            value={form.location_note}
            onChange={(e) => set("location_note", e.target.value)}
            placeholder="Home office desk"
          />
        </div>
      </div>

      <div className="field">
        <label>Description</label>
        <textarea
          value={form.description}
          onChange={(e) => set("description", e.target.value)}
          placeholder="Optional description"
        />
      </div>

      <div className="field">
        <label>Notes</label>
        <textarea
          value={form.notes}
          onChange={(e) => set("notes", e.target.value)}
          placeholder="Optional notes"
        />
      </div>

      <div className="section-actions">
        <button type="button" className="btn-secondary" onClick={onCancel}>
          Cancel
        </button>
        <button
          type="submit"
          className="btn-primary"
          disabled={submitting || !form.name.trim() || !form.category}
        >
          {submitting ? "Saving..." : submitLabel}
        </button>
      </div>
    </form>
  );
}

export function Assets() {
  const [assets, setAssets] = useState<AssetPublicRead[]>([]);
  const [total, setTotal] = useState(0);
  const [categoryTerms, setCategoryTerms] = useState<TermPublic[]>([]);
  const [statusTerms, setStatusTerms] = useState<TermPublic[]>([]);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [page, setPage] = useState(0);
  const [reloadKey, setReloadKey] = useState(0);

  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState<AssetFormState>(EMPTY_FORM);

  const [editingAssetId, setEditingAssetId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<AssetFormState>(EMPTY_FORM);

  useEffect(() => {
    Promise.all([
      listTerms("asset-categories", { limit: 200 }),
      listTerms("asset-statuses", { limit: 200 }),
    ])
      .then(([cats, statuses]) => {
        setCategoryTerms(cats);
        setStatusTerms(statuses);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load vocabulary");
      });
  }, []);

  useEffect(() => {
    setLoading(true);
    setError(null);
    listAssets({
      skip: page * PAGE_SIZE,
      limit: PAGE_SIZE,
      category: categoryFilter || undefined,
      status: statusFilter || undefined,
    })
      .then((res) => {
        setAssets(res.items);
        setTotal(res.total);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load assets");
      })
      .finally(() => setLoading(false));
  }, [page, categoryFilter, statusFilter, reloadKey]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return assets;
    return assets.filter((a) => {
      const haystack = `${a.name} ${a.vendor ?? ""} ${a.description ?? ""}`.toLowerCase();
      return haystack.includes(q);
    });
  }, [search, assets]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  async function handleCreateSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await createAsset(normalizePayload(createForm));
      setShowCreate(false);
      setCreateForm(EMPTY_FORM);
      setPage(0);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create asset");
    } finally {
      setSubmitting(false);
    }
  }

  function startEdit(asset: AssetPublicRead) {
    setEditingAssetId(asset.id);
    setEditForm(toForm(asset));
    setShowCreate(false);
  }

  function cancelEdit() {
    setEditingAssetId(null);
    setEditForm(EMPTY_FORM);
  }

  async function handleEditSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!editingAssetId) return;
    setSubmitting(true);
    setError(null);
    try {
      await updateAsset(editingAssetId, normalizePayload(editForm));
      cancelEdit();
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update asset");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(assetId: string) {
    if (!window.confirm("Delete this asset?")) return;
    setSubmitting(true);
    setError(null);
    try {
      await deleteAsset(assetId);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete asset");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AppLayout
      title="Assets"
      subtitle={total > 0 ? `${total} asset${total === 1 ? "" : "s"}` : undefined}
      headerRight={
        <button
          className="btn-primary"
          onClick={() => {
            setShowCreate((v) => !v);
            if (!showCreate) cancelEdit();
          }}
        >
          {showCreate ? "Close" : "+ New Asset"}
        </button>
      }
    >
      {showCreate && (
        <AssetForm
          form={createForm}
          onChange={setCreateForm}
          onSubmit={handleCreateSubmit}
          onCancel={() => { setShowCreate(false); setCreateForm(EMPTY_FORM); }}
          submitting={submitting}
          categoryTerms={categoryTerms}
          statusTerms={statusTerms}
          title="Create Asset"
          submitLabel="Create Asset"
        />
      )}

      {editingAssetId && (
        <AssetForm
          form={editForm}
          onChange={setEditForm}
          onSubmit={handleEditSubmit}
          onCancel={cancelEdit}
          submitting={submitting}
          categoryTerms={categoryTerms}
          statusTerms={statusTerms}
          title="Edit Asset"
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
          value={categoryFilter}
          onChange={(e) => { setCategoryFilter(e.target.value); setPage(0); }}
        >
          <option value="">All categories</option>
          {categoryTerms.map((t) => (
            <option key={t.slug} value={t.slug}>{t.name}</option>
          ))}
        </select>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(0); }}
        >
          <option value="">All statuses</option>
          {statusTerms.map((t) => (
            <option key={t.slug} value={t.slug}>{t.name}</option>
          ))}
        </select>
      </div>

      {error && <div className="form-error" style={{ marginBottom: 14 }}>{error}</div>}

      {loading ? (
        <div className="splash"><div className="spinner" /></div>
      ) : filtered.length === 0 ? (
        <div className="empty-state" style={{ paddingTop: 80 }}>
          <span className="empty-icon">◉</span>
          <p>{total === 0 ? "No assets yet. Add your first asset." : "No assets match your search."}</p>
        </div>
      ) : (
        <table className="people-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Category</th>
              <th>Status</th>
              <th>Vendor</th>
              <th>Purchase date</th>
              <th>Purchase price</th>
              <th>Current value</th>
              <th style={{ width: 110 }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((asset) => (
              <tr key={asset.id}>
                <td>
                  <div className="person-name">{asset.name}</div>
                  {asset.location_note && (
                    <div className="person-nickname">{asset.location_note}</div>
                  )}
                </td>
                <td>
                  <span className="task-badge">{asset.category.name}</span>
                </td>
                <td>
                  <span className="task-badge">{asset.status.name}</span>
                </td>
                <td className="person-contact">{asset.vendor ?? "-"}</td>
                <td className="person-date">{formatDate(asset.purchase_date)}</td>
                <td className="person-contact">
                  {formatCurrency(asset.purchase_price, asset.purchase_price_currency)}
                </td>
                <td className="person-contact">
                  {formatCurrency(asset.current_value, asset.purchase_price_currency)}
                </td>
                <td>
                  <div className="task-actions">
                    <button className="btn-icon" title="Edit" onClick={() => startEdit(asset)}>
                      ✎
                    </button>
                    <button
                      className="btn-icon btn-danger-ghost"
                      title="Delete"
                      onClick={() => handleDelete(asset.id)}
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
