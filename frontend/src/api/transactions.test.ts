import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  bulkCreateTransactions,
  createTransaction,
  deleteTransaction,
  getTransactionSummary,
  listTransactions,
  parseTransactionInput,
  quickAddTransaction,
  updateTransaction,
} from "./transactions";
import { api } from "./client";

vi.mock("./client", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
  buildQuery: (params: Record<string, unknown>) => {
    const q = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== "") q.set(k, String(v));
    }
    return q.toString();
  },
}));

const mockTransaction = {
  id: "txn-1",
  owner_id: "owner-1",
  transaction_type: "expense",
  amount: 199.5,
  currency: "INR",
  transacted_on: "2026-04-04",
  description: "Groceries",
  category: null,
  payment_method: null,
  asset_id: null,
  subscription_id: null,
  merchant: "Local Store",
  reference: null,
  tags: ["groceries"],
  import_batch_id: null,
  notes: null,
  created_at: "2026-04-04T10:00:00Z",
  updated_at: "2026-04-04T10:00:00Z",
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("listTransactions", () => {
  it("calls GET /transactions with no params", async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [mockTransaction], total: 1, skip: 0, limit: 25 });
    const result = await listTransactions();
    expect(api.get).toHaveBeenCalledWith("/transactions");
    expect(result.items[0].description).toBe("Groceries");
  });

  it("appends multiple filters", async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [], total: 0, skip: 0, limit: 25 });
    await listTransactions({ transaction_type: "expense", limit: 10, search: "store" });
    const url = vi.mocked(api.get).mock.calls[0][0] as string;
    expect(url).toContain("/transactions?");
    expect(url).toContain("transaction_type=expense");
    expect(url).toContain("limit=10");
    expect(url).toContain("search=store");
  });
});

describe("getTransactionSummary", () => {
  it("calls GET /transactions/summary with filters", async () => {
    vi.mocked(api.get).mockResolvedValue({ total_income: 0, total_expense: 0 });
    await getTransactionSummary({ date_from: "2026-04-01", date_to: "2026-04-30", currency: "USD" });
    expect(api.get).toHaveBeenCalledWith("/transactions/summary?date_from=2026-04-01&date_to=2026-04-30&currency=USD");
  });
});

describe("mutation endpoints", () => {
  it("creates a transaction", async () => {
    vi.mocked(api.post).mockResolvedValue(mockTransaction);
    const result = await createTransaction({
      transaction_type: "expense",
      amount: 199.5,
      transacted_on: "2026-04-04",
      description: "Groceries",
    });
    expect(api.post).toHaveBeenCalledWith("/transactions", expect.objectContaining({ amount: 199.5 }));
    expect(result.id).toBe("txn-1");
  });

  it("updates and deletes a transaction", async () => {
    vi.mocked(api.patch).mockResolvedValue({ ...mockTransaction, notes: "updated" });
    vi.mocked(api.delete).mockResolvedValue(undefined);

    const updated = await updateTransaction("txn-1", { notes: "updated" });
    await deleteTransaction("txn-1");

    expect(api.patch).toHaveBeenCalledWith("/transactions/txn-1", { notes: "updated" });
    expect(api.delete).toHaveBeenCalledWith("/transactions/txn-1");
    expect(updated.notes).toBe("updated");
  });
});

describe("helper endpoints", () => {
  it("calls bulk create endpoint", async () => {
    vi.mocked(api.post).mockResolvedValue([mockTransaction]);
    const result = await bulkCreateTransactions([
      {
        transaction_type: "expense",
        amount: 199.5,
        transacted_on: "2026-04-04",
        description: "Groceries",
      },
    ]);
    expect(api.post).toHaveBeenCalledWith("/transactions/bulk", expect.any(Array));
    expect(result).toHaveLength(1);
  });

  it("uses default INR for parse and quick-add", async () => {
    vi.mocked(api.post)
      .mockResolvedValueOnce({
        transaction_type: "expense",
        amount: 75,
        transacted_on: "2026-04-04",
        description: "Coffee",
      })
      .mockResolvedValueOnce(mockTransaction);

    await parseTransactionInput("coffee 75");
    await quickAddTransaction("groceries 199.5");

    expect(api.post).toHaveBeenNthCalledWith(1, "/transactions/parse", { input: "coffee 75", currency: "INR" });
    expect(api.post).toHaveBeenNthCalledWith(2, "/transactions/quick-add", { input: "groceries 199.5", currency: "INR" });
  });
});

