import { useEffect, useState } from "react";
import { AppLayout } from "../components/AppLayout";
import {
  createBudget,
  deleteBudget,
  listBudgets,
  updateBudget,
} from "../api/budgets";
import type { BudgetWithSpend } from "../api/budgets";
import { listTerms } from "../api/vocabularies";
import type { TermPublic } from "../api/vocabularies";

const MONTH_NAMES = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

const FULL_MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

const CURRENCIES = ["INR", "USD", "EUR", "GBP", "JPY", "CAD", "AUD"];

function formatAmount(amount: number, currency: string): string {
  const symbol: Record<string, string> = {
    INR: "₹", USD: "$", EUR: "€", GBP: "£", JPY: "¥", CAD: "C$", AUD: "A$",
  };
  const s = symbol[currency] ?? currency + " ";
  return `${s}${amount.toLocaleString("en-IN")}`;
}

export function Budgets() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);

  const [budgets, setBudgets] = useState<BudgetWithSpend[]>([]);
  const [loading, setLoading] = useState(true);
  const [reloadKey, setReloadKey] = useState(0);

  // Create form
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({
    category: "",
    amount: "",
    currency: "INR",
    notes: "",
  });

  // Edit
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({ amount: "", notes: "" });

  // Vocabulary
  const [expenseTerms, setExpenseTerms] = useState<TermPublic[]>([]);

  // Copy from last month
  const [copying, setCopying] = useState(false);
  const [copyMessage, setCopyMessage] = useState<string | null>(null);

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Load expense-categories vocabulary
  useEffect(() => {
    listTerms("expense-categories", { limit: 200 })
      .then(setExpenseTerms)
      .catch((err) => {
        setError(
          err instanceof Error ? err.message : "Failed to load expense categories"
        );
      });
  }, []);

  // Load budgets when month/year changes
  useEffect(() => {
    setLoading(true);
    setError(null);
    listBudgets(year, month)
      .then(setBudgets)
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load budgets");
      })
      .finally(() => setLoading(false));
  }, [year, month, reloadKey]);

  // Month navigation
  const prevMonth = () => {
    if (month === 1) {
      setYear((y) => y - 1);
      setMonth(12);
    } else {
      setMonth((m) => m - 1);
    }
    setCopyMessage(null);
  };

  const nextMonth = () => {
    if (month === 12) {
      setYear((y) => y + 1);
      setMonth(1);
    } else {
      setMonth((m) => m + 1);
    }
    setCopyMessage(null);
  };

  const prevMonthLabel = () => {
    const m = month === 1 ? 12 : month - 1;
    return MONTH_NAMES[m - 1];
  };

  // Copy from last month
  const copyFromLastMonth = async () => {
    setCopying(true);
    setError(null);
    setCopyMessage(null);
    try {
      const prevY = month === 1 ? year - 1 : year;
      const prevM = month === 1 ? 12 : month - 1;
      const lastMonthBudgets = await listBudgets(prevY, prevM);
      const existingCategories = new Set(budgets.map((b) => b.category.slug));

      const toCreate = lastMonthBudgets
        .filter((b) => !existingCategories.has(b.category.slug))
        .map((b) => ({
          category: b.category.slug,
          year,
          month,
          amount: b.amount,
          currency: b.currency,
        }));

      if (toCreate.length === 0) {
        setCopyMessage("Nothing new to copy — all categories are already set.");
        return;
      }

      await Promise.all(toCreate.map(createBudget));
      setReloadKey((k) => k + 1);
      setCopyMessage(
        `Copied ${toCreate.length} budget${toCreate.length !== 1 ? "s" : ""} from ${MONTH_NAMES[prevM - 1]} ${prevY}.`
      );
    } catch {
      setError("Failed to copy budgets from last month.");
    } finally {
      setCopying(false);
    }
  };

  // Create budget
  async function handleCreateSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!createForm.category || !createForm.amount) return;

    setSubmitting(true);
    setError(null);
    try {
      await createBudget({
        category: createForm.category,
        year,
        month,
        amount: parseFloat(createForm.amount),
        currency: createForm.currency,
        notes: createForm.notes.trim() || null,
      });
      setShowCreate(false);
      setCreateForm({ category: "", amount: "", currency: "INR", notes: "" });
      setReloadKey((k) => k + 1);
    } catch (err) {
      const msg =
        err instanceof Error ? err.message : "Failed to create budget";
      if (msg.includes("409") || msg.toLowerCase().includes("already exists") || msg.toLowerCase().includes("conflict")) {
        setError(
          "A budget for this category already exists this month. Edit the existing row below."
        );
      } else {
        setError(msg);
      }
    } finally {
      setSubmitting(false);
    }
  }

  // Start editing
  function startEdit(b: BudgetWithSpend) {
    setEditingId(b.id);
    setEditForm({ amount: String(b.amount), notes: b.notes ?? "" });
  }

  function cancelEdit() {
    setEditingId(null);
    setEditForm({ amount: "", notes: "" });
  }

  // Save edit
  async function handleEditSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!editingId || !editForm.amount) return;

    setSubmitting(true);
    setError(null);
    try {
      await updateBudget(editingId, {
        amount: parseFloat(editForm.amount),
        notes: editForm.notes.trim() || null,
      });
      cancelEdit();
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update budget");
    } finally {
      setSubmitting(false);
    }
  }

  // Delete budget
  async function handleDelete(id: string) {
    const confirmed = window.confirm("Delete this budget?");
    if (!confirmed) return;

    setSubmitting(true);
    setError(null);
    try {
      await deleteBudget(id);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete budget");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AppLayout
      title="Budgets"
      subtitle="Monthly spending targets"
      headerRight={
        <button
          className="btn-primary"
          onClick={() => {
            setShowCreate((v) => !v);
            if (!showCreate) cancelEdit();
          }}
        >
          {showCreate ? "Close" : "+ Add Budget"}
        </button>
      }
    >
      {/* Month navigation */}
      <div className="budget-month-nav">
        <button className="btn-secondary" onClick={prevMonth}>
          ←
        </button>
        <span className="budget-month-label">
          {FULL_MONTH_NAMES[month - 1]} {year}
        </span>
        <button className="btn-secondary" onClick={nextMonth}>
          →
        </button>
        <button
          className="btn-secondary"
          onClick={copyFromLastMonth}
          disabled={copying}
        >
          {copying ? "Copying…" : `Copy from ${prevMonthLabel()}`}
        </button>
      </div>

      {copyMessage && (
        <div className="budget-copy-message">{copyMessage}</div>
      )}

      {/* Create form */}
      {showCreate && (
        <form className="task-form-panel" onSubmit={handleCreateSubmit}>
          <h3>Add Budget</h3>
          <div className="form-row">
            <div className="field">
              <label>Category</label>
              <select
                value={createForm.category}
                onChange={(e) =>
                  setCreateForm((f) => ({ ...f, category: e.target.value }))
                }
                required
              >
                <option value="">Select category</option>
                {expenseTerms.map((t) => (
                  <option key={t.id} value={t.slug}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Currency</label>
              <select
                value={createForm.currency}
                onChange={(e) =>
                  setCreateForm((f) => ({ ...f, currency: e.target.value }))
                }
              >
                {CURRENCIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="form-row">
            <div className="field">
              <label>Monthly Budget</label>
              <input
                type="number"
                value={createForm.amount}
                onChange={(e) =>
                  setCreateForm((f) => ({ ...f, amount: e.target.value }))
                }
                min="0"
                step="100"
                placeholder="10000"
                required
              />
            </div>
            <div className="field">
              <label>Notes</label>
              <input
                type="text"
                value={createForm.notes}
                onChange={(e) =>
                  setCreateForm((f) => ({ ...f, notes: e.target.value }))
                }
                placeholder="Optional notes"
              />
            </div>
          </div>
          {error && <div className="form-error">{error}</div>}
          <div className="section-actions">
            <button
              type="button"
              className="btn-secondary"
              onClick={() => {
                setShowCreate(false);
                setError(null);
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={
                submitting || !createForm.category || !createForm.amount
              }
            >
              {submitting ? "Saving…" : "Save Budget"}
            </button>
          </div>
        </form>
      )}

      {/* General error (outside create form) */}
      {error && !showCreate && (
        <div className="form-error" style={{ marginBottom: 14 }}>
          {error}
        </div>
      )}

      {/* Budget table */}
      {loading ? (
        <div className="splash">
          <div className="spinner" />
        </div>
      ) : budgets.length === 0 ? (
        <div className="empty-state" style={{ paddingTop: 80 }}>
          <span className="empty-icon">◈</span>
          <p>
            No budgets set for {FULL_MONTH_NAMES[month - 1]} {year}. Add one
            to start tracking.
          </p>
        </div>
      ) : (
        <table className="people-table budget-table">
          <thead>
            <tr>
              <th>Category</th>
              <th>Progress</th>
              <th>Spent / Budget</th>
              <th>Remaining</th>
              <th style={{ width: 110 }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {budgets.map((b) => {
              const pct = Math.min(b.utilization * 100, 100);
              const over = b.utilization > 1;

              if (editingId === b.id) {
                return (
                  <tr key={b.id}>
                    <td colSpan={5}>
                      <form
                        className="budget-inline-edit"
                        onSubmit={handleEditSubmit}
                      >
                        <span className="budget-inline-category">
                          {b.category.name}
                        </span>
                        <div className="field" style={{ flex: 1 }}>
                          <label>Amount</label>
                          <input
                            type="number"
                            value={editForm.amount}
                            onChange={(e) =>
                              setEditForm((f) => ({
                                ...f,
                                amount: e.target.value,
                              }))
                            }
                            min="0"
                            step="100"
                            required
                          />
                        </div>
                        <div className="field" style={{ flex: 2 }}>
                          <label>Notes</label>
                          <input
                            type="text"
                            value={editForm.notes}
                            onChange={(e) =>
                              setEditForm((f) => ({
                                ...f,
                                notes: e.target.value,
                              }))
                            }
                            placeholder="Optional notes"
                          />
                        </div>
                        <div className="task-actions">
                          <button
                            type="submit"
                            className="btn-primary"
                            disabled={submitting || !editForm.amount}
                          >
                            {submitting ? "…" : "Save"}
                          </button>
                          <button
                            type="button"
                            className="btn-secondary"
                            onClick={cancelEdit}
                          >
                            Cancel
                          </button>
                        </div>
                      </form>
                    </td>
                  </tr>
                );
              }

              return (
                <tr key={b.id}>
                  <td>
                    <div className="person-name">{b.category.name}</div>
                    {b.notes && (
                      <div className="person-nickname">{b.notes}</div>
                    )}
                  </td>
                  <td style={{ minWidth: 160 }}>
                    <div className="budget-track">
                      <div
                        className={`budget-fill${over ? " budget-fill--over" : ""}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </td>
                  <td className="budget-amounts">
                    {formatAmount(b.spent, b.currency)} /{" "}
                    {formatAmount(b.amount, b.currency)}
                  </td>
                  <td>
                    {over ? (
                      <span className="text-danger">
                        {formatAmount(Math.abs(b.remaining), b.currency)} over ⚠
                      </span>
                    ) : (
                      <span className="text-muted">
                        {formatAmount(b.remaining, b.currency)}
                      </span>
                    )}
                  </td>
                  <td>
                    <div className="task-actions">
                      <button
                        className="btn-icon"
                        title="Edit"
                        onClick={() => startEdit(b)}
                      >
                        ✎
                      </button>
                      <button
                        className="btn-icon btn-danger-ghost"
                        title="Delete"
                        onClick={() => handleDelete(b.id)}
                      >
                        ✕
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </AppLayout>
  );
}
