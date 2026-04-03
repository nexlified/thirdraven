import { useEffect, useMemo, useState } from "react";
import { AppLayout } from "../components/AppLayout";
import { listTerms } from "../api/vocabularies";
import type { TermPublic } from "../api/vocabularies";
import {
  createSubscription,
  deleteSubscription,
  getSubscriptionSummary,
  listSubscriptions,
  updateSubscription,
} from "../api/subscriptions";
import type { SubscriptionPublicRead, SubscriptionSummary } from "../api/subscriptions";

const PAGE_SIZE = 25;

const STATUS_OPTIONS = ["active", "paused", "cancelled", "trial"];
const BILLING_CYCLE_OPTIONS = ["monthly", "yearly", "weekly", "quarterly", "one-time"];
const PAYMENT_MODE_OPTIONS = ["manual", "auto_debit"];

interface SubFormState {
  name: string;
  provider: string;
  category: string;
  status: string;
  cost: string;
  currency: string;
  payment_mode: string;
  billing_cycle: string;
  started_on: string;
  next_billing_date: string;
  trial_ends_on: string;
  auto_renews: boolean;
  url: string;
  notes: string;
  tags: string[];
}

const EMPTY_FORM: SubFormState = {
  name: "",
  provider: "",
  category: "",
  status: "active",
  cost: "",
  currency: "USD",
  payment_mode: "manual",
  billing_cycle: "monthly",
  started_on: "",
  next_billing_date: "",
  trial_ends_on: "",
  auto_renews: true,
  url: "",
  notes: "",
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

function formatCost(cost: number, currency: string): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(cost);
}

function toForm(sub: SubscriptionPublicRead): SubFormState {
  return {
    name: sub.name,
    provider: sub.provider ?? "",
    category: sub.category?.slug ?? "",
    status: sub.status,
    cost: String(sub.cost),
    currency: sub.currency,
    payment_mode: sub.payment_mode,
    billing_cycle: sub.billing_cycle,
    started_on: sub.started_on ?? "",
    next_billing_date: sub.next_billing_date ?? "",
    trial_ends_on: sub.trial_ends_on ?? "",
    auto_renews: sub.auto_renews,
    url: sub.url ?? "",
    notes: sub.notes ?? "",
    tags: sub.tags.map((t) => t.slug),
  };
}

function normalizePayload(form: SubFormState) {
  return {
    name: form.name.trim(),
    provider: form.provider.trim() || null,
    category: form.category || null,
    status: form.status,
    cost: parseFloat(form.cost) || 0,
    currency: form.currency.toUpperCase() || "USD",
    payment_mode: form.payment_mode,
    billing_cycle: form.billing_cycle,
    started_on: form.started_on || null,
    next_billing_date: form.next_billing_date || null,
    trial_ends_on: form.trial_ends_on || null,
    auto_renews: form.auto_renews,
    url: form.url.trim() || null,
    notes: form.notes.trim() || null,
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

export function Subscriptions() {
  const [subs, setSubs] = useState<SubscriptionPublicRead[]>([]);
  const [total, setTotal] = useState(0);
  const [summary, setSummary] = useState<SubscriptionSummary | null>(null);
  const [categoryTerms, setCategoryTerms] = useState<TermPublic[]>([]);
  const [tagTerms, setTagTerms] = useState<TermPublic[]>([]);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [page, setPage] = useState(0);
  const [reloadKey, setReloadKey] = useState(0);

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [cycleFilter, setCycleFilter] = useState("");

  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState<SubFormState>(EMPTY_FORM);

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<SubFormState>(EMPTY_FORM);

  useEffect(() => {
    Promise.all([
      listTerms("subscription-categories", { limit: 200 }),
      listTerms("subscription-tags", { limit: 200 }),
      getSubscriptionSummary(),
    ])
      .then(([cats, tags, sumRes]) => {
        setCategoryTerms(cats);
        setTagTerms(tags);
        setSummary(sumRes);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load metadata");
      });
  }, []);

  useEffect(() => {
    setLoading(true);
    setError(null);
    listSubscriptions({
      skip: page * PAGE_SIZE,
      limit: PAGE_SIZE,
      status: statusFilter || undefined,
      category: categoryFilter || undefined,
      billing_cycle: cycleFilter || undefined,
    })
      .then((res) => {
        setSubs(res.items);
        setTotal(res.total);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load subscriptions");
      })
      .finally(() => setLoading(false));
  }, [page, statusFilter, categoryFilter, cycleFilter, reloadKey]);

  useEffect(() => {
    getSubscriptionSummary()
      .then((res) => setSummary(res))
      .catch(() => {});
  }, [reloadKey]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return subs;
    return subs.filter((s) =>
      `${s.name} ${s.provider ?? ""}`.toLowerCase().includes(q)
    );
  }, [search, subs]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  function toggleTag(form: SubFormState, slug: string): SubFormState {
    const tags = form.tags.includes(slug)
      ? form.tags.filter((s) => s !== slug)
      : [...form.tags, slug];
    return { ...form, tags };
  }

  async function handleCreateSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!createForm.name.trim() || !createForm.cost) return;
    setSubmitting(true);
    setError(null);
    try {
      await createSubscription(normalizePayload(createForm));
      setShowCreate(false);
      setCreateForm(EMPTY_FORM);
      setPage(0);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create subscription");
    } finally {
      setSubmitting(false);
    }
  }

  function startEdit(sub: SubscriptionPublicRead) {
    setEditingId(sub.id);
    setEditForm(toForm(sub));
    setShowCreate(false);
  }

  function cancelEdit() {
    setEditingId(null);
    setEditForm(EMPTY_FORM);
  }

  async function handleEditSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!editingId || !editForm.name.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await updateSubscription(editingId, normalizePayload(editForm));
      cancelEdit();
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update subscription");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    if (!window.confirm("Delete this subscription?")) return;
    setSubmitting(true);
    setError(null);
    try {
      await deleteSubscription(id);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete subscription");
    } finally {
      setSubmitting(false);
    }
  }

  function SubForm({
    form,
    onChange,
    onSubmit,
    onCancel,
    title,
    submitLabel,
  }: {
    form: SubFormState;
    onChange: (f: SubFormState) => void;
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
            <label>Name *</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => onChange({ ...form, name: e.target.value })}
              placeholder="Netflix"
              required
            />
          </div>
          <div className="field">
            <label>Provider</label>
            <input
              type="text"
              value={form.provider}
              onChange={(e) => onChange({ ...form, provider: e.target.value })}
              placeholder="Netflix Inc."
            />
          </div>
        </div>

        <div className="form-row">
          <div className="field">
            <label>Category</label>
            <select
              value={form.category}
              onChange={(e) => onChange({ ...form, category: e.target.value })}
            >
              <option value="">- none -</option>
              {categoryTerms.map((t) => (
                <option key={t.slug} value={t.slug}>{t.name}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Status</label>
            <select
              value={form.status}
              onChange={(e) => onChange({ ...form, status: e.target.value })}
            >
              {STATUS_OPTIONS.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-row">
          <div className="field">
            <label>Cost *</label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={form.cost}
              onChange={(e) => onChange({ ...form, cost: e.target.value })}
              placeholder="9.99"
              required
            />
          </div>
          <div className="field" style={{ maxWidth: 100 }}>
            <label>Currency</label>
            <input
              type="text"
              maxLength={3}
              value={form.currency}
              onChange={(e) => onChange({ ...form, currency: e.target.value.toUpperCase() })}
              placeholder="USD"
            />
          </div>
          <div className="field">
            <label>Billing cycle</label>
            <select
              value={form.billing_cycle}
              onChange={(e) => onChange({ ...form, billing_cycle: e.target.value })}
            >
              {BILLING_CYCLE_OPTIONS.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-row">
          <div className="field">
            <label>Payment mode</label>
            <select
              value={form.payment_mode}
              onChange={(e) => onChange({ ...form, payment_mode: e.target.value })}
            >
              {PAYMENT_MODE_OPTIONS.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Started on</label>
            <input
              type="date"
              value={form.started_on}
              onChange={(e) => onChange({ ...form, started_on: e.target.value })}
            />
          </div>
          <div className="field">
            <label>Next billing</label>
            <input
              type="date"
              value={form.next_billing_date}
              onChange={(e) => onChange({ ...form, next_billing_date: e.target.value })}
            />
          </div>
        </div>

        <div className="form-row">
          <div className="field">
            <label>Trial ends</label>
            <input
              type="date"
              value={form.trial_ends_on}
              onChange={(e) => onChange({ ...form, trial_ends_on: e.target.value })}
            />
          </div>
          <div className="field">
            <label>URL</label>
            <input
              type="url"
              value={form.url}
              onChange={(e) => onChange({ ...form, url: e.target.value })}
              placeholder="https://netflix.com"
            />
          </div>
        </div>

        <div className="field">
          <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={form.auto_renews}
              onChange={(e) => onChange({ ...form, auto_renews: e.target.checked })}
            />
            Auto-renews
          </label>
        </div>

        <div className="field">
          <label>Notes</label>
          <textarea
            value={form.notes}
            onChange={(e) => onChange({ ...form, notes: e.target.value })}
            placeholder="Optional notes"
          />
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
            disabled={submitting || !form.name.trim() || !form.cost}
          >
            {submitting ? "Saving..." : submitLabel}
          </button>
        </div>
      </form>
    );
  }

  const monthlyCostDisplay = summary
    ? Object.entries(summary.monthly_cost_by_currency)
        .map(([cur, amt]) => formatCost(amt, cur))
        .join(" + ") || "-"
    : "-";

  return (
    <AppLayout
      title="Subscriptions"
      subtitle={summary ? `${summary.total_active} active` : undefined}
      headerRight={
        <button
          className="btn-primary"
          onClick={() => {
            setShowCreate((v) => !v);
            if (!showCreate) cancelEdit();
          }}
        >
          {showCreate ? "Close" : "+ New Subscription"}
        </button>
      }
    >
      {summary && (
        <div className="task-summary-grid">
          <div className="stat-card">
            <span className="stat-icon">◈</span>
            <div className="stat-body">
              <span className="stat-value">{summary.total_active}</span>
              <span className="stat-label">Active</span>
            </div>
          </div>
          <div className="stat-card">
            <span className="stat-icon">◷</span>
            <div className="stat-body">
              <span className="stat-value">{summary.upcoming_renewals.length}</span>
              <span className="stat-label">Renewing soon</span>
            </div>
          </div>
          <div className="stat-card">
            <span className="stat-icon">$</span>
            <div className="stat-body">
              <span className="stat-value" style={{ fontSize: "0.95em" }}>{monthlyCostDisplay}</span>
              <span className="stat-label">Monthly</span>
            </div>
          </div>
        </div>
      )}

      {showCreate && (
        <SubForm
          form={createForm}
          onChange={setCreateForm}
          onSubmit={handleCreateSubmit}
          onCancel={() => { setShowCreate(false); setCreateForm(EMPTY_FORM); }}
          title="Create Subscription"
          submitLabel="Create Subscription"
        />
      )}

      {editingId && (
        <SubForm
          form={editForm}
          onChange={setEditForm}
          onSubmit={handleEditSubmit}
          onCancel={cancelEdit}
          title="Edit Subscription"
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
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(0); }}>
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <select value={categoryFilter} onChange={(e) => { setCategoryFilter(e.target.value); setPage(0); }}>
          <option value="">All categories</option>
          {categoryTerms.map((t) => (
            <option key={t.slug} value={t.slug}>{t.name}</option>
          ))}
        </select>
        <select value={cycleFilter} onChange={(e) => { setCycleFilter(e.target.value); setPage(0); }}>
          <option value="">All billing cycles</option>
          {BILLING_CYCLE_OPTIONS.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      {error && <div className="form-error" style={{ marginBottom: 14 }}>{error}</div>}

      {loading ? (
        <div className="splash"><div className="spinner" /></div>
      ) : filtered.length === 0 ? (
        <div className="empty-state" style={{ paddingTop: 80 }}>
          <span className="empty-icon">◈</span>
          <p>{total === 0 ? "No subscriptions yet. Add your first." : "No subscriptions match your search."}</p>
        </div>
      ) : (
        <table className="people-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Category</th>
              <th>Status</th>
              <th>Cost / cycle</th>
              <th>Next billing</th>
              <th>Provider</th>
              <th>Auto-renews</th>
              <th style={{ width: 110 }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((sub) => (
              <tr key={sub.id}>
                <td>
                  <div className="person-name">{sub.name}</div>
                  {sub.url && (
                    <div className="person-nickname">
                      <a href={sub.url} target="_blank" rel="noopener noreferrer">{sub.url}</a>
                    </div>
                  )}
                </td>
                <td className="person-contact">{sub.category?.name ?? "-"}</td>
                <td>
                  <span className="task-badge">{sub.status}</span>
                </td>
                <td className="person-contact">
                  {formatCost(sub.cost, sub.currency)} / {sub.billing_cycle}
                </td>
                <td className="person-date">{formatDate(sub.next_billing_date)}</td>
                <td className="person-contact">{sub.provider ?? "-"}</td>
                <td className="person-contact">{sub.auto_renews ? "Yes" : "No"}</td>
                <td>
                  <div className="task-actions">
                    <button className="btn-icon" title="Edit" onClick={() => startEdit(sub)}>
                      ✎
                    </button>
                    <button
                      className="btn-icon btn-danger-ghost"
                      title="Delete"
                      onClick={() => handleDelete(sub.id)}
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
