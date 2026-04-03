import { useEffect, useMemo, useState } from "react";
import { AppLayout } from "../components/AppLayout";
import { listPersons } from "../api/persons";
import type { PersonSlim } from "../api/persons";
import {
  createLoan,
  deleteLoan,
  listLoans,
  updateLoan,
} from "../api/loans";
import type { LoanPublic } from "../api/loans";

const PAGE_SIZE = 25;

const DIRECTION_OPTIONS = ["lent", "borrowed"];
const LOAN_TYPE_OPTIONS = ["money", "item"];
const STATUS_OPTIONS = ["outstanding", "returned", "forgiven", "disputed"];

interface LoanFormState {
  person_id: string;
  direction: string;
  loan_type: string;
  description: string;
  amount: string;
  currency: string;
  item_name: string;
  loaned_on: string;
  due_on: string;
  returned_on: string;
  status: string;
  notes: string;
}

const EMPTY_FORM: LoanFormState = {
  person_id: "",
  direction: "lent",
  loan_type: "money",
  description: "",
  amount: "",
  currency: "USD",
  item_name: "",
  loaned_on: "",
  due_on: "",
  returned_on: "",
  status: "outstanding",
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

function toForm(loan: LoanPublic): LoanFormState {
  return {
    person_id: loan.person_id,
    direction: loan.direction,
    loan_type: loan.loan_type,
    description: loan.description,
    amount: loan.amount != null ? String(loan.amount) : "",
    currency: loan.currency ?? "USD",
    item_name: loan.item_name ?? "",
    loaned_on: loan.loaned_on ?? "",
    due_on: loan.due_on ?? "",
    returned_on: loan.returned_on ?? "",
    status: loan.status,
    notes: loan.notes ?? "",
  };
}

function normalizeCreatePayload(form: LoanFormState) {
  return {
    person_id: form.person_id,
    direction: form.direction,
    loan_type: form.loan_type,
    description: form.description.trim(),
    amount: form.loan_type === "money" && form.amount ? parseFloat(form.amount) : null,
    currency: form.loan_type === "money" ? (form.currency.toUpperCase() || null) : null,
    item_name: form.loan_type === "item" ? (form.item_name.trim() || null) : null,
    loaned_on: form.loaned_on || null,
    due_on: form.due_on || null,
    notes: form.notes.trim() || null,
  };
}

function normalizeUpdatePayload(form: LoanFormState) {
  return {
    description: form.description.trim() || undefined,
    amount: form.loan_type === "money" && form.amount ? parseFloat(form.amount) : null,
    currency: form.loan_type === "money" ? (form.currency.toUpperCase() || null) : null,
    item_name: form.loan_type === "item" ? (form.item_name.trim() || null) : null,
    loaned_on: form.loaned_on || null,
    due_on: form.due_on || null,
    returned_on: form.returned_on || null,
    status: form.status,
    notes: form.notes.trim() || null,
  };
}

export function Loans() {
  const [loans, setLoans] = useState<LoanPublic[]>([]);
  const [total, setTotal] = useState(0);
  const [people, setPeople] = useState<PersonSlim[]>([]);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [page, setPage] = useState(0);
  const [reloadKey, setReloadKey] = useState(0);

  const [search, setSearch] = useState("");
  const [directionFilter, setDirectionFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState<LoanFormState>(EMPTY_FORM);

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<LoanFormState>(EMPTY_FORM);

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
    listLoans({
      skip: page * PAGE_SIZE,
      limit: PAGE_SIZE,
      direction: directionFilter || undefined,
      status_filter: statusFilter || undefined,
    })
      .then((res) => {
        setLoans(res.items);
        setTotal(res.total);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load loans");
      })
      .finally(() => setLoading(false));
  }, [page, directionFilter, statusFilter, reloadKey]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return loans;
    return loans.filter((l) =>
      `${l.description} ${l.item_name ?? ""}`.toLowerCase().includes(q)
    );
  }, [search, loans]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  const peopleMap = useMemo(
    () => new Map(people.map((p) => [p.id, `${p.first_name} ${p.last_name ?? ""}`.trim()])),
    [people]
  );

  async function handleCreateSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!createForm.person_id || !createForm.description.trim()) return;
    if (createForm.loan_type === "item" && !createForm.item_name.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await createLoan(normalizeCreatePayload(createForm));
      setShowCreate(false);
      setCreateForm(EMPTY_FORM);
      setPage(0);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create loan");
    } finally {
      setSubmitting(false);
    }
  }

  function startEdit(loan: LoanPublic) {
    setEditingId(loan.id);
    setEditForm(toForm(loan));
    setShowCreate(false);
  }

  function cancelEdit() {
    setEditingId(null);
    setEditForm(EMPTY_FORM);
  }

  async function handleEditSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!editingId || !editForm.description.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await updateLoan(editingId, normalizeUpdatePayload(editForm));
      cancelEdit();
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update loan");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    if (!window.confirm("Delete this loan?")) return;
    setSubmitting(true);
    setError(null);
    try {
      await deleteLoan(id);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete loan");
    } finally {
      setSubmitting(false);
    }
  }

  function LoanForm({
    form,
    onChange,
    onSubmit,
    onCancel,
    title,
    submitLabel,
    isEdit,
  }: {
    form: LoanFormState;
    onChange: (f: LoanFormState) => void;
    onSubmit: (e: React.FormEvent) => void;
    onCancel: () => void;
    title: string;
    submitLabel: string;
    isEdit?: boolean;
  }) {
    const isMoneyLoan = form.loan_type === "money";
    const isItemLoan = form.loan_type === "item";
    const canSubmit =
      form.person_id &&
      form.description.trim() &&
      (!isItemLoan || form.item_name.trim());

    return (
      <form className="task-form-panel" onSubmit={onSubmit}>
        <h3>{title}</h3>

        <div className="form-row">
          <div className="field">
            <label>Person *</label>
            <select
              value={form.person_id}
              onChange={(e) => onChange({ ...form, person_id: e.target.value })}
              required
              disabled={isEdit}
            >
              <option value="">- select person -</option>
              {people.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.first_name} {p.last_name ?? ""}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Direction *</label>
            <select
              value={form.direction}
              onChange={(e) => onChange({ ...form, direction: e.target.value })}
              disabled={isEdit}
            >
              {DIRECTION_OPTIONS.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Type *</label>
            <select
              value={form.loan_type}
              onChange={(e) => onChange({ ...form, loan_type: e.target.value })}
              disabled={isEdit}
            >
              {LOAN_TYPE_OPTIONS.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="field">
          <label>Description *</label>
          <input
            type="text"
            value={form.description}
            onChange={(e) => onChange({ ...form, description: e.target.value })}
            placeholder={isMoneyLoan ? "Lent for medical expenses" : "Lent my camera"}
            required
          />
        </div>

        {isMoneyLoan && (
          <div className="form-row">
            <div className="field">
              <label>Amount</label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={form.amount}
                onChange={(e) => onChange({ ...form, amount: e.target.value })}
                placeholder="500.00"
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
          </div>
        )}

        {isItemLoan && (
          <div className="field">
            <label>Item name *</label>
            <input
              type="text"
              value={form.item_name}
              onChange={(e) => onChange({ ...form, item_name: e.target.value })}
              placeholder="Canon EOS R5"
              required={isItemLoan}
            />
          </div>
        )}

        <div className="form-row">
          <div className="field">
            <label>Loaned on</label>
            <input
              type="date"
              value={form.loaned_on}
              onChange={(e) => onChange({ ...form, loaned_on: e.target.value })}
            />
          </div>
          <div className="field">
            <label>Due on</label>
            <input
              type="date"
              value={form.due_on}
              onChange={(e) => onChange({ ...form, due_on: e.target.value })}
            />
          </div>
          {isEdit && (
            <div className="field">
              <label>Returned on</label>
              <input
                type="date"
                value={form.returned_on}
                onChange={(e) => onChange({ ...form, returned_on: e.target.value })}
              />
            </div>
          )}
        </div>

        {isEdit && (
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
        )}

        <div className="field">
          <label>Notes</label>
          <textarea
            value={form.notes}
            onChange={(e) => onChange({ ...form, notes: e.target.value })}
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
            disabled={submitting || !canSubmit}
          >
            {submitting ? "Saving..." : submitLabel}
          </button>
        </div>
      </form>
    );
  }

  return (
    <AppLayout
      title="Loans"
      subtitle={total > 0 ? `${total} loan${total === 1 ? "" : "s"}` : undefined}
      headerRight={
        <button
          className="btn-primary"
          onClick={() => {
            setShowCreate((v) => !v);
            if (!showCreate) cancelEdit();
          }}
        >
          {showCreate ? "Close" : "+ New Loan"}
        </button>
      }
    >
      {showCreate && (
        <LoanForm
          form={createForm}
          onChange={setCreateForm}
          onSubmit={handleCreateSubmit}
          onCancel={() => { setShowCreate(false); setCreateForm(EMPTY_FORM); }}
          title="Create Loan"
          submitLabel="Create Loan"
        />
      )}

      {editingId && (
        <LoanForm
          form={editForm}
          onChange={setEditForm}
          onSubmit={handleEditSubmit}
          onCancel={cancelEdit}
          title="Edit Loan"
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
        <select value={directionFilter} onChange={(e) => { setDirectionFilter(e.target.value); setPage(0); }}>
          <option value="">All directions</option>
          {DIRECTION_OPTIONS.map((d) => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(0); }}>
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      {error && <div className="form-error" style={{ marginBottom: 14 }}>{error}</div>}

      {loading ? (
        <div className="splash"><div className="spinner" /></div>
      ) : filtered.length === 0 ? (
        <div className="empty-state" style={{ paddingTop: 80 }}>
          <span className="empty-icon">◎</span>
          <p>{total === 0 ? "No loans yet. Track your first loan." : "No loans match your search."}</p>
        </div>
      ) : (
        <table className="people-table">
          <thead>
            <tr>
              <th>Description</th>
              <th>Direction</th>
              <th>Type</th>
              <th>Person</th>
              <th>Amount / Item</th>
              <th>Loaned</th>
              <th>Due</th>
              <th>Status</th>
              <th style={{ width: 110 }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((loan) => (
              <tr key={loan.id}>
                <td>
                  <div className="person-name">{loan.description}</div>
                  {loan.notes && <div className="person-nickname">{loan.notes}</div>}
                </td>
                <td>
                  <span className="task-badge">{loan.direction}</span>
                </td>
                <td className="person-contact">{loan.loan_type}</td>
                <td className="person-contact">
                  {peopleMap.get(loan.person_id) ?? "Unknown"}
                </td>
                <td className="person-contact">
                  {loan.loan_type === "money"
                    ? loan.amount != null
                      ? new Intl.NumberFormat("en-US", {
                          style: "currency",
                          currency: loan.currency ?? "USD",
                        }).format(loan.amount)
                      : "-"
                    : loan.item_name ?? "-"}
                </td>
                <td className="person-date">{formatDate(loan.loaned_on)}</td>
                <td className="person-date">{formatDate(loan.due_on)}</td>
                <td>
                  <span className="task-badge">{loan.status}</span>
                </td>
                <td>
                  <div className="task-actions">
                    <button className="btn-icon" title="Edit" onClick={() => startEdit(loan)}>
                      ✎
                    </button>
                    <button
                      className="btn-icon btn-danger-ghost"
                      title="Delete"
                      onClick={() => handleDelete(loan.id)}
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
