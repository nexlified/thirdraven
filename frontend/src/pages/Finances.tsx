import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AppLayout } from "../components/AppLayout";
import { getFinanceOverview } from "../api/finances";
import { listBudgets } from "../api/budgets";
import type { FinanceOverview } from "../api/finances";
import type { BudgetWithSpend } from "../api/budgets";

export function Finances() {
  const [overview, setOverview] = useState<FinanceOverview | null>(null);
  const [budgets, setBudgets] = useState<BudgetWithSpend[]>([]);
  const [currency, setCurrency] = useState("INR");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const now = new Date();
  const [year] = useState(now.getFullYear());
  const [month] = useState(now.getMonth() + 1);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [ov, bud] = await Promise.all([
          getFinanceOverview(currency),
          listBudgets(year, month),
        ]);
        setOverview(ov);
        setBudgets(bud);
      } catch {
        setError("Failed to load financial overview");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [currency, year, month]);

  function fmt(amount: number, cur?: string): string {
    const c = cur ?? currency;
    try {
      return new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: c,
        maximumFractionDigits: 0,
      }).format(amount);
    } catch {
      return `${c} ${amount.toFixed(0)}`;
    }
  }

  function formatDueDate(dateStr: string | null): string {
    if (!dateStr) return "—";
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-IN", { month: "short", day: "numeric" });
  }

  const headerRight = (
    <select
      value={currency}
      onChange={(e) => setCurrency(e.target.value)}
      className="currency-select"
    >
      <option value="INR">INR</option>
      <option value="USD">USD</option>
      <option value="EUR">EUR</option>
    </select>
  );

  return (
    <AppLayout
      title="Finances"
      subtitle="Your financial picture"
      headerRight={headerRight}
    >
      {loading ? (
        <div className="splash">
          <div className="spinner" />
        </div>
      ) : error ? (
        <div className="form-error" style={{ marginBottom: 14 }}>
          {error}
        </div>
      ) : (
        <div className="finances-dashboard">
          {/* ── Section 1: Net Worth ── */}
          <section className="finance-section">
            <h3 className="finance-section-title">Net Worth</h3>
            {overview && overview.financial_assets.length > 0 ? (
              <div className="net-worth-scroll">
                {overview.financial_assets.map((asset) => (
                  <div key={asset.asset_id} className="asset-card">
                    <span className="asset-card-name">{asset.name}</span>
                    <span className="asset-card-balance">
                      {asset.current_balance !== null
                        ? fmt(asset.current_balance, asset.currency ?? currency)
                        : "—"}
                    </span>
                    <span className="asset-card-type">
                      {asset.account_type ?? "account"}
                    </span>
                  </div>
                ))}
                {Object.entries(overview.total_asset_value_by_currency).map(
                  ([cur, total]) => {
                    const matchingAssets = overview.financial_assets.filter(
                      (a) => (a.currency ?? currency) === cur,
                    );
                    return (
                      <div key={`total-${cur}`} className="asset-card asset-card-total">
                        <span className="asset-card-name">Total</span>
                        <span className="asset-card-balance">{fmt(total, cur)}</span>
                        <span className="asset-card-type">
                          across {matchingAssets.length} account
                          {matchingAssets.length !== 1 ? "s" : ""}
                        </span>
                      </div>
                    );
                  },
                )}
              </div>
            ) : (
              <div className="empty-state">
                <span className="empty-icon">◈</span>
                <p>No financial assets linked — add one in Assets</p>
              </div>
            )}
          </section>

          {/* ── Section 2: This Month ── */}
          <section className="finance-section">
            <h3 className="finance-section-title">This Month</h3>
            {overview ? (
              <>
                <div className="cashflow-grid">
                  <div className="cashflow-card">
                    <span className="cashflow-label">Income</span>
                    <span className="cashflow-value cashflow-income">
                      {fmt(overview.current_month_income)}
                    </span>
                  </div>
                  <div className="cashflow-card">
                    <span className="cashflow-label">Expenses</span>
                    <span className="cashflow-value cashflow-expense">
                      {fmt(overview.current_month_expenses)}
                    </span>
                  </div>
                  <div className="cashflow-card">
                    <span className="cashflow-label">Net</span>
                    <span
                      className={`cashflow-value ${
                        overview.current_month_net >= 0
                          ? "cashflow-positive"
                          : "cashflow-negative"
                      }`}
                    >
                      {overview.current_month_net >= 0 ? "+" : ""}
                      {fmt(overview.current_month_net)}
                    </span>
                  </div>
                </div>
                {overview.current_month_savings_rate !== null && (
                  <p className="savings-rate">
                    Savings rate:{" "}
                    <strong>
                      {(overview.current_month_savings_rate * 100).toFixed(1)}%
                    </strong>
                  </p>
                )}
              </>
            ) : (
              <div className="empty-state">
                <span className="empty-icon">₹</span>
                <p>No data for this month yet</p>
              </div>
            )}
          </section>

          {/* ── Section 3: Spending by Category ── */}
          {overview && overview.top_expense_categories.length > 0 && (
            <section className="finance-section">
              <h3 className="finance-section-title">Spending by Category</h3>
              <div className="category-bars">
                {overview.top_expense_categories.map((cat) => {
                  const maxPct = overview.top_expense_categories[0].percentage;
                  const barWidth = `${(cat.percentage / maxPct) * 100}%`;
                  return (
                    <div key={cat.category_slug} className="category-bar-row">
                      <span className="category-bar-label">{cat.category_name}</span>
                      <div className="category-bar-track">
                        <div
                          className="category-bar-fill"
                          style={{ width: barWidth }}
                        />
                      </div>
                      <span className="category-bar-amount">
                        {fmt(cat.total)} ({cat.percentage.toFixed(1)}%)
                      </span>
                    </div>
                  );
                })}
              </div>
            </section>
          )}

          {/* ── Section 4: Budget Progress ── */}
          {budgets.length > 0 && (
            <section className="finance-section">
              <h3 className="finance-section-title">Budget Progress</h3>
              <div className="budget-progress-list">
                {budgets.map((b) => {
                  const pct = Math.min(b.utilization * 100, 100);
                  const over = b.utilization > 1;
                  return (
                    <div
                      key={b.id}
                      className={`budget-progress-row${over ? " budget-over" : ""}`}
                    >
                      <span className="budget-category">{b.category.name}</span>
                      <div className="budget-track">
                        <div
                          className="budget-fill"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <span className="budget-amounts">
                        {fmt(b.spent)} of {fmt(b.amount)}
                      </span>
                      <span className={over ? "text-danger" : "text-muted"}>
                        {over
                          ? `${fmt(b.spent - b.amount)} over ⚠`
                          : `${fmt(b.remaining)} left`}
                      </span>
                    </div>
                  );
                })}
              </div>
            </section>
          )}

          {/* ── Section 5: Outstanding Loans ── */}
          <section className="finance-section">
            <h3 className="finance-section-title">Outstanding Loans</h3>
            {overview && overview.outstanding_loans.length > 0 ? (
              <>
                <table className="people-table finance-loans-table">
                  <thead>
                    <tr>
                      <th>Person</th>
                      <th>Direction</th>
                      <th>Amount</th>
                      <th>Due</th>
                    </tr>
                  </thead>
                  <tbody>
                    {overview.outstanding_loans.map((loan) => (
                      <tr key={loan.loan_id}>
                        <td>{loan.person_name}</td>
                        <td>
                          <span
                            className={`task-badge ${
                              loan.direction === "lent"
                                ? "badge-lent"
                                : "badge-borrowed"
                            }`}
                          >
                            {loan.direction === "lent" ? "Lent" : "Borrowed"}
                          </span>
                        </td>
                        <td>
                          {loan.amount !== null
                            ? fmt(loan.amount, loan.currency ?? currency)
                            : "—"}
                        </td>
                        <td>{formatDueDate(loan.due_on)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="finance-section-footer">
                  <Link to="/loans">View all loans →</Link>
                </div>
              </>
            ) : (
              <div className="empty-state">
                <span className="empty-icon">◎</span>
                <p>No outstanding loans</p>
              </div>
            )}
          </section>

          {/* ── Section 6: Monthly Subscriptions ── */}
          <section className="finance-section">
            <h3 className="finance-section-title">Monthly Subscriptions</h3>
            {overview &&
            Object.keys(overview.monthly_subscription_cost_by_currency).length > 0 ? (
              <div className="subscription-summary">
                {Object.entries(overview.monthly_subscription_cost_by_currency).map(
                  ([cur, cost]) => (
                    <p key={cur} className="subscription-cost">
                      <strong>{fmt(cost, cur)}/month</strong>
                    </p>
                  ),
                )}
                <div className="finance-section-footer">
                  <Link to="/subscriptions">View subscriptions →</Link>
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <span className="empty-icon">◉</span>
                <p>No active subscriptions</p>
              </div>
            )}
          </section>
        </div>
      )}
    </AppLayout>
  );
}
