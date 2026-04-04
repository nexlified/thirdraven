import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import QuickAddTransaction from "./QuickAddTransaction";
import { quickAddTransaction, type TransactionPublic } from "../api/transactions";

vi.mock("../api/transactions", () => ({
  quickAddTransaction: vi.fn(),
}));

describe("QuickAddTransaction", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("disables submit when input is empty", () => {
    render(<QuickAddTransaction />);
    expect(screen.getByRole("button", { name: "Add" })).toBeDisabled();
  });

  it("submits, shows success, calls onSuccess, and clears success after 3s", async () => {
    const onSuccess = vi.fn();

    vi.mocked(quickAddTransaction).mockResolvedValue({
      id: "tx-1",
      owner_id: "owner-1",
      transaction_type: "expense",
      amount: 500,
      currency: "INR",
      transacted_on: "2026-04-04",
      description: "fuel",
      category: { id: "cat-1", name: "Fuel", slug: "fuel" },
      payment_method: null,
      asset_id: null,
      subscription_id: null,
      merchant: null,
      reference: null,
      tags: [],
      import_batch_id: null,
      notes: null,
      created_at: "2026-04-04T10:00:00Z",
      updated_at: "2026-04-04T10:00:00Z",
    } satisfies TransactionPublic);

    render(<QuickAddTransaction onSuccess={onSuccess} />);

    const input = screen.getByLabelText("Quick add transaction");
    fireEvent.change(input, { target: { value: "500 fuel" } });
    fireEvent.click(screen.getByRole("button", { name: "Add" }));

    expect(quickAddTransaction).toHaveBeenCalledWith("500 fuel", "INR");
    expect(await screen.findByText("− INR 500 — Fuel")).toBeInTheDocument();
    expect(onSuccess).toHaveBeenCalledTimes(1);
    expect(input).toHaveValue("");

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 3100));
    });
    await waitFor(() => {
      expect(screen.queryByText("− INR 500 — Fuel")).not.toBeInTheDocument();
    });
  }, 10000);

  it("shows loading state while request is pending", async () => {
  let resolveRequest!: (value: TransactionPublic) => void;
  const pending = new Promise<TransactionPublic>((resolve) => {
    resolveRequest = resolve;
  });

  vi.mocked(quickAddTransaction).mockReturnValue(pending);

	render(<QuickAddTransaction />);

	const input = screen.getByLabelText("Quick add transaction");
	fireEvent.change(input, { target: { value: "salary 50000" } });
	fireEvent.click(screen.getByRole("button", { name: "Add" }));

	expect(screen.getByRole("button", { name: "Adding..." })).toBeDisabled();
	expect(input).toBeDisabled();

	resolveRequest({
	  id: "tx-2",
	  owner_id: "owner-1",
	  transaction_type: "income",
	  amount: 50000,
	  currency: "INR",
	  transacted_on: "2026-04-04",
	  description: "salary",
	  category: null,
	  payment_method: null,
	  asset_id: null,
	  subscription_id: null,
	  merchant: null,
	  reference: null,
	  tags: [],
	  import_batch_id: null,
	  notes: null,
	  created_at: "2026-04-04T10:00:00Z",
	  updated_at: "2026-04-04T10:00:00Z",
	});

	await waitFor(() => {
	  expect(screen.getByRole("button", { name: "Add" })).toBeInTheDocument();
	});
  });

  it("renders API errors inline", async () => {
	vi.mocked(quickAddTransaction).mockRejectedValue(new Error("Could not parse input"));

	render(<QuickAddTransaction defaultCurrency="USD" />);

	fireEvent.change(screen.getByLabelText("Quick add transaction"), { target: { value: "bad text" } });
	fireEvent.click(screen.getByRole("button", { name: "Add" }));

	expect(quickAddTransaction).toHaveBeenCalledWith("bad text", "USD");
	expect(await screen.findByText("Could not parse input")).toBeInTheDocument();
  });
});

