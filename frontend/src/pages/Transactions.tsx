import { useEffect, useState } from "react";
import { AppLayout } from "../components/AppLayout";
import QuickAddTransaction from "../components/QuickAddTransaction";
import { listTerms } from "../api/vocabularies";
import type { TermPublic } from "../api/vocabularies";
import {
  bulkCreateTransactions,
  createTransaction,
  deleteTransaction,
  getTransactionSummary,
  listTransactions,
  updateTransaction,
} from "../api/transactions";
import type {
  TransactionCreatePayload,
  TransactionPublic,
  TransactionSummary,
} from "../api/transactions";
import type { TermSlim } from "../api/types";

const PAGE_SIZE = 50;

interface TxFormState {
  transaction_type: "expense" | "income";
  amount: string;
  currency: string;
  transacted_on: string;
  description: string;
  category: string;
  payment_method: string;
  merchant: string;
  notes: string;
}

const EMPTY_FORM: TxFormState = {
  transaction_type: "expense",
  amount: "",
  currency: "INR",
  transacted_on: new Date().toISOString().split("T")[0],
  description: "",
  category: "",
  payment_method: "",
  merchant: "",
  notes: "",
};

function formatAmount(tx: TransactionPublic): string {
  const sign = tx.transaction_type === "income" ? "+" : "−";
  return `${sign}${new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: tx.currency,
    maximumFractionDigits: 0,
  }).format(tx.amount)}`;
}

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString("en-IN", {
    month: "short",
    day: "numeric",
  });
}

function formatSummaryAmount(amount: number, currency = "INR"): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(amount);
}

function parseImportLine(line: string): TransactionCreatePayload | null {
  const parts = line.split("|").map((s) => s.trim());
  if (parts.length < 4) return null;
  const [dateStr, description, amountStr, typeStr] = parts;
  const amount = parseFloat(amountStr);
  if (isNaN(amount)) return null;
  return {
    transacted_on: dateStr,
    description,
    amount,
    transaction_type: typeStr.toLowerCase().includes("credit") ? "income" : "expense",
    currency: "INR",
  };
}

function toForm(tx: TransactionPublic): TxFormState {
  return {
    transaction_type: tx.transaction_type,
    amount: String(tx.amount),
    currency: tx.currency,
    transacted_on: tx.transacted_on,
    description: tx.description,
    category: tx.category?.slug ?? "",
    payment_method: tx.payment_method?.slug ?? "",
    merchant: tx.merchant ?? "",
    notes: tx.notes ?? "",
  };
}

function normalizePayload(form: TxFormState): TransactionCreatePayload {
  return {
    transaction_type: form.transaction_type,
    amount: parseFloat(form.amount) || 0,
    currency: form.currency.toUpperCase() || "INR",
    transacted_on: form.transacted_on,
    description: form.description.trim(),
    category: form.category || null,
    payment_method: form.payment_method || null,
    merchant: form.merchant.trim() || null,
    notes: form.notes.trim() || null,
  };
}

function TxForm({
  form,
  onChange,
  onSubmit,
  onCancel,
  title,
  submitLabel,
  submitting,
  expenseTerms,
  incomeTerms,
  paymentTerms,
}: {
  form: TxFormState;
  onChange: (f: TxFormState) => void;
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
  title: string;
  submitLabel: string;
  submitting: boolean;
  expenseTerms: TermSlim[];
  incomeTerms: TermSlim[];
  paymentTerms: TermSlim[];
}) {
  const categoryTerms = form.transaction_type === "income" ? incomeTerms : expenseTerms;

  return (
    <form className="task-form-panel" onSubmit={onSubmit}>
      <h3>{title}</h3>

      <div className="form-row">
        <div className="field">
          <label>Type *</label>
          <select
            value={form.transaction_type}
            onChange={(e) =>
              onChange({
                ...form,
                transaction_type: e.target.value as "expense" | "income",
                category: "",
              })
            }
          >
            <option value="expense">Expense</option>
            <option value="income">Income</option>
          </select>
        </div>
        <div className="field">
          <label>Amount *</label>
          <input
            type="number"
            step="0.01"
            min="0"
            value={form.amount}
            onChange={(e) => onChange({ ...form, amount: e.target.value })}
            placeholder="0.00"
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
            placeholder="INR"
          />
        </div>
      </div>

      <div className="form-row">
        <div className="field">
          <label>Date *</label>
          <input
            type="date"
            value={form.transacted_on}
            onChange={(e) => onChange({ ...form, transacted_on: e.target.value })}
            required
          />
        </div>
        <div className="field">
          <label>Description *</label>
          <input
            type="text"
            value={form.description}
            onChange={(e) => onChange({ ...form, description: e.target.value })}
            placeholder="Shell — fuel"
            required
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
              <option key={t.slug} value={t.slug}>
                {t.name}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>Payment method</label>
          <select
            value={form.payment_method}
            onChange={(e) => onChange({ ...form, payment_method: e.target.value })}
          >
            <option value="">- none -</option>
            {paymentTerms.map((t) => (
              <option key={t.slug} value={t.slug}>
                {t.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="form-row">
        <div className="field">
          <label>Merchant</label>
          <input
            type="text"
            value={form.merchant}
            onChange={(e) => onChange({ ...form, merchant: e.target.value })}
            placeholder="Shell, Zomato…"
          />
        </div>
      </div>

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
          disabled={submitting || !form.amount || !form.description.trim()}
        >
          {submitting ? "Saving..." : submitLabel}
        </button>
      </div>
    </form>
  );
}

export function Transactions() {
  // Data
  const [items, setItems] = useState<TransactionPublic[]>([]);
  const [total, setTotal] = useState(0);
  const [summary, setSummary] = useState<TransactionSummary | null>(null);
  const [page, setPage] = useState(0);

  // UI
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  // Filters
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState<"" | "expense" | "income">("");
  const [filterCategory, setFilterCategory] = useState("");
  const [filterDateFrom, setFilterDateFrom] = useState("");
  const [filterDateTo, setFilterDateTo] = useState("");

  // Forms
  const [showCreate, setShowCreate] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [createForm, setCreateForm] = useState<TxFormState>(EMPTY_FORM);
  const [editForm, setEditForm] = useState<TxFormState>(EMPTY_FORM);

  // Vocabulary terms
  const [expenseTerms, setExpenseTerms] = useState<TermSlim[]>([]);
  const [incomeTerms, setIncomeTerms] = useState<TermSlim[]>([]);
  const [paymentTerms, setPaymentTerms] = useState<TermSlim[]>([]);

  // Import
  const [showImport, setShowImport] = useState(false);
  const [importText, setImportText] = useState("");
  const [importPreview, setImportPreview] = useState<TransactionCreatePayload[] | null>(null);

  // Load vocabulary terms once on mount
  useEffect(() => {
    Promise.all([
      listTerms("expense-categories", { limit: 200 }),
      listTerms("income-categories", { limit: 200 }),
      listTerms("payment-methods", { limit: 200 }),
    ])
      .then(([expense, income, payment]: [TermPublic[], TermPublic[], TermPublic[]]) => {
        setExpenseTerms(expense.map((t) => ({ id: t.id, name: t.name, slug: t.slug })));
        setIncomeTerms(income.map((t) => ({ id: t.id, name: t.name, slug: t.slug })));
        setPaymentTerms(payment.map((t) => ({ id: t.id, name: t.name, slug: t.slug })));
      })
      .catch(() => {});
  }, []);

  // Load transactions and summary on filter/page change
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        const now = new Date();
        const monthStart = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-01`;
        const monthEnd = new Date(now.getFullYear(), now.getMonth() + 1, 0)
          .toISOString()
          .split("T")[0];

        const [txResult, summaryResult] = await Promise.all([
          listTransactions({
            skip: page * PAGE_SIZE,
            limit: PAGE_SIZE,
            transaction_type: filterType || undefined,
            category: filterCategory || undefined,
            date_from: filterDateFrom || undefined,
            date_to: filterDateTo || undefined,
            search: search || undefined,
          }),
          getTransactionSummary({
            currency: "INR",
            date_from: monthStart,
            date_to: monthEnd,
          }),
        ]);
        setItems(txResult.items);
        setTotal(txResult.total);
        setSummary(summaryResult);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load transactions");
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [page, filterType, filterCategory, filterDateFrom, filterDateTo, search, reloadKey]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  function handleFilterChange(
    key: "type" | "category" | "dateFrom" | "dateTo" | "search",
    value: string
  ) {
    setPage(0);
    switch (key) {
      case "type":
        setFilterType(value as "" | "expense" | "income");
        break;
      case "category":
        setFilterCategory(value);
        break;
      case "dateFrom":
        setFilterDateFrom(value);
        break;
      case "dateTo":
        setFilterDateTo(value);
        break;
      case "search":
        setSearch(value);
        break;
    }
  }

  async function handleCreateSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!createForm.amount || !createForm.description.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await createTransaction(normalizePayload(createForm));
      setShowCreate(false);
      setCreateForm(EMPTY_FORM);
      setPage(0);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create transaction");
    } finally {
      setSubmitting(false);
    }
  }

  function startEdit(tx: TransactionPublic) {
    setEditingId(tx.id);
    setEditForm(toForm(tx));
    setShowCreate(false);
  }

  function cancelEdit() {
    setEditingId(null);
    setEditForm(EMPTY_FORM);
  }

  async function handleEditSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!editingId || !editForm.amount || !editForm.description.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await updateTransaction(editingId, normalizePayload(editForm));
      cancelEdit();
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update transaction");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    if (!window.confirm("Delete this transaction?")) return;
    setSubmitting(true);
    setError(null);
    try {
      await deleteTransaction(id);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete transaction");
    } finally {
      setSubmitting(false);
    }
  }

  function handleImportParse() {
    const lines = importText.split("\n").filter((l) => l.trim());
    const parsed = lines.map(parseImportLine).filter((p): p is TransactionCreatePayload => p !== null);
    setImportPreview(parsed);
  }

  async function handleImportConfirm() {
    if (!importPreview || importPreview.length === 0) return;
    setSubmitting(true);
    setError(null);
    try {
      await bulkCreateTransactions(importPreview);
      setShowImport(false);
      setImportText("");
      setImportPreview(null);
      setPage(0);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to import transactions");
    } finally {
      setSubmitting(false);
    }
  }

  function cancelImport() {
    setShowImport(false);
    setImportText("");
    setImportPreview(null);
  }

  const allCategoryTerms = [...expenseTerms, ...incomeTerms].filter(
    (t, i, arr) => arr.findIndex((x) => x.slug === t.slug) === i
  );

  return (
    <AppLayout
      title="Transactions"
      subtitle="Track income & expenses"
      headerRight={
        <button
          className="btn-primary"
          onClick={() => {
            setShowCreate((v) => !v);
            if (!showCreate) cancelEdit();
          }}
        >
          {showCreate ? "Close" : "+ Add Transaction"}
        </button>
      }
    >
      {/* Stat cards */}
      {summary && (
        <div className="task-summary-grid">
          <div className="stat-card">
            <span className="stat-icon">↑</span>
            <div className="stat-body">
              <span className="stat-value" style={{ color: "var(--accent)" }}>
                {formatSummaryAmount(summary.total_income, summary.currency)}
              </span>
              <span className="stat-label">Income this month</span>
            </div>
          </div>
          <div className="stat-card">
            <span className="stat-icon">↓</span>
            <div className="stat-body">
              <span className="stat-value">
                {formatSummaryAmount(summary.total_expense, summary.currency)}
              </span>
              <span className="stat-label">Expenses this month</span>
            </div>
          </div>
          <div className="stat-card">
            <span className="stat-icon">≡</span>
            <div className="stat-body">
              <span
                className="stat-value"
                style={{ color: summary.net >= 0 ? "var(--accent)" : undefined }}
              >
                {formatSummaryAmount(summary.net, summary.currency)}
              </span>
              <span className="stat-label">Net this month</span>
            </div>
          </div>
        </div>
      )}

      {/* Quick add */}
      <div style={{ marginBottom: 16 }}>
        <QuickAddTransaction
          defaultCurrency="INR"
          onSuccess={() => setReloadKey((k) => k + 1)}
        />
      </div>

      {/* Filter toolbar */}
      <div className="people-toolbar">
        <input
          type="date"
          value={filterDateFrom}
          onChange={(e) => handleFilterChange("dateFrom", e.target.value)}
          title="From date"
        />
        <input
          type="date"
          value={filterDateTo}
          onChange={(e) => handleFilterChange("dateTo", e.target.value)}
          title="To date"
        />
        <select
          value={filterType}
          onChange={(e) => handleFilterChange("type", e.target.value)}
        >
          <option value="">All types</option>
          <option value="income">Income</option>
          <option value="expense">Expense</option>
        </select>
        <select
          value={filterCategory}
          onChange={(e) => handleFilterChange("category", e.target.value)}
        >
          <option value="">All categories</option>
          {allCategoryTerms.map((t) => (
            <option key={t.slug} value={t.slug}>
              {t.name}
            </option>
          ))}
        </select>
        <input
          className="search-input"
          type="search"
          placeholder="Search…"
          value={search}
          onChange={(e) => handleFilterChange("search", e.target.value)}
        />
        <button
          className="btn-secondary"
          onClick={() => {
            setShowImport((v) => !v);
            if (!showImport) {
              setImportText("");
              setImportPreview(null);
            }
          }}
        >
          Import
        </button>
      </div>

      {/* Create form */}
      {showCreate && (
        <TxForm
          form={createForm}
          onChange={setCreateForm}
          onSubmit={handleCreateSubmit}
          onCancel={() => {
            setShowCreate(false);
            setCreateForm(EMPTY_FORM);
          }}
          title="New Transaction"
          submitLabel="Create Transaction"
          submitting={submitting}
          expenseTerms={expenseTerms}
          incomeTerms={incomeTerms}
          paymentTerms={paymentTerms}
        />
      )}

      {/* Import panel */}
      {showImport && (
        <div className="task-form-panel">
          <h3>Import from statement</h3>
          <p className="page-subtitle" style={{ marginBottom: 8 }}>
            One transaction per line: <code>YYYY-MM-DD | description | amount | debit/credit</code>
          </p>
          <p className="page-subtitle" style={{ marginBottom: 12, fontSize: "0.8em", opacity: 0.7 }}>
            Example: <code>2026-04-01 | Shell Fuel | 500 | debit</code>
          </p>
          <textarea
            rows={8}
            style={{ width: "100%", fontFamily: "monospace", fontSize: "0.875rem" }}
            value={importText}
            onChange={(e) => {
              setImportText(e.target.value);
              setImportPreview(null);
            }}
            placeholder={"2026-04-01 | Shell Fuel | 500 | debit\n2026-04-01 | Salary April | 50000 | credit"}
          />
          {importPreview !== null && (
            <p style={{ marginTop: 8, fontWeight: 600 }}>
              {importPreview.length} transaction{importPreview.length !== 1 ? "s" : ""} detected
            </p>
          )}
          <div className="section-actions">
            <button type="button" className="btn-secondary" onClick={cancelImport}>
              Cancel
            </button>
            {importPreview === null ? (
              <button type="button" className="btn-primary" onClick={handleImportParse}>
                Preview
              </button>
            ) : (
              <button
                type="button"
                className="btn-primary"
                disabled={submitting || importPreview.length === 0}
                onClick={handleImportConfirm}
              >
                {submitting ? "Importing..." : `Confirm Import (${importPreview.length})`}
              </button>
            )}
          </div>
        </div>
      )}

      {error && <div className="form-error" style={{ marginBottom: 14 }}>{error}</div>}

      {loading ? (
        <div className="splash">
          <div className="spinner" />
        </div>
      ) : items.length === 0 ? (
        <div className="empty-state" style={{ paddingTop: 80 }}>
          <span className="empty-icon">◈</span>
          <p>
            {total === 0
              ? "No transactions yet. Add your first."
              : "No transactions match your filters."}
          </p>
        </div>
      ) : (
        <>
          <table className="people-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Type</th>
                <th>Description / Merchant</th>
                <th>Category</th>
                <th>Amount</th>
                <th style={{ width: 110 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((tx) => (
                <>
                  <tr key={tx.id}>
                    <td className="person-date">{formatDate(tx.transacted_on)}</td>
                    <td>
                      <span className="task-badge">{tx.transaction_type}</span>
                    </td>
                    <td>
                      <div className="person-name">{tx.description}</div>
                      {tx.merchant && (
                        <div className="person-nickname">{tx.merchant}</div>
                      )}
                    </td>
                    <td className="person-contact">{tx.category?.name ?? "-"}</td>
                    <td
                      className="person-contact"
                      style={{
                        color:
                          tx.transaction_type === "income" ? "var(--accent)" : undefined,
                        fontVariantNumeric: "tabular-nums",
                      }}
                    >
                      {formatAmount(tx)}
                    </td>
                    <td>
                      <div className="task-actions">
                        <button
                          className="btn-icon"
                          title="Edit"
                          onClick={() => startEdit(tx)}
                        >
                          ✎
                        </button>
                        <button
                          className="btn-icon btn-danger-ghost"
                          title="Delete"
                          onClick={() => handleDelete(tx.id)}
                        >
                          ✕
                        </button>
                      </div>
                    </td>
                  </tr>
                  {editingId === tx.id && (
                    <tr key={`${tx.id}-edit`}>
                      <td colSpan={6} style={{ padding: 0 }}>
                        <TxForm
                          form={editForm}
                          onChange={setEditForm}
                          onSubmit={handleEditSubmit}
                          onCancel={cancelEdit}
                          title="Edit Transaction"
                          submitLabel="Save Changes"
                          submitting={submitting}
                          expenseTerms={expenseTerms}
                          incomeTerms={incomeTerms}
                          paymentTerms={paymentTerms}
                        />
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>

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
        </>
      )}
    </AppLayout>
  );
}
