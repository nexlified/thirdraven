import { beforeEach, describe, expect, it, vi } from "vitest";
import { createBudget, deleteBudget, listBudgets, updateBudget } from "./budgets";
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

const mockBudget = {
  id: "budget-1",
  owner_id: "owner-1",
  category: { id: "cat-1", name: "Groceries", slug: "groceries" },
  year: 2026,
  month: 4,
  amount: 10000,
  currency: "INR",
  notes: null,
  created_at: "2026-04-01T00:00:00Z",
  updated_at: "2026-04-01T00:00:00Z",
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("listBudgets", () => {
  it("calls GET /budgets with year and month", async () => {
    vi.mocked(api.get).mockResolvedValue([
      {
        ...mockBudget,
        spent: 4200,
        remaining: 5800,
        utilization: 0.42,
      },
    ]);

    const result = await listBudgets(2026, 4);

    expect(api.get).toHaveBeenCalledWith("/budgets?year=2026&month=4");
    expect(result[0].spent).toBe(4200);
  });
});

describe("budget mutations", () => {
  it("creates budget", async () => {
    vi.mocked(api.post).mockResolvedValue(mockBudget);

    const result = await createBudget({
      category: "groceries",
      year: 2026,
      month: 4,
      amount: 10000,
    });

    expect(api.post).toHaveBeenCalledWith("/budgets", expect.objectContaining({ category: "groceries" }));
    expect(result.id).toBe("budget-1");
  });

  it("updates and deletes budget", async () => {
    vi.mocked(api.patch).mockResolvedValue({ ...mockBudget, amount: 12000 });
    vi.mocked(api.delete).mockResolvedValue(undefined);

    const result = await updateBudget("budget-1", { amount: 12000, notes: "Adjusted" });
    await deleteBudget("budget-1");

    expect(api.patch).toHaveBeenCalledWith("/budgets/budget-1", { amount: 12000, notes: "Adjusted" });
    expect(api.delete).toHaveBeenCalledWith("/budgets/budget-1");
    expect(result.amount).toBe(12000);
  });
});

