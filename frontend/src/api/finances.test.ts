import { beforeEach, describe, expect, it, vi } from "vitest";
import { getFinanceOverview } from "./finances";
import { api } from "./client";

vi.mock("./client", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe("getFinanceOverview", () => {
  it("uses INR by default", async () => {
    vi.mocked(api.get).mockResolvedValue({ current_month_currency: "INR" });

    const result = await getFinanceOverview();

    expect(api.get).toHaveBeenCalledWith("/finances/overview?currency=INR");
    expect(result.current_month_currency).toBe("INR");
  });

  it("accepts a custom currency", async () => {
    vi.mocked(api.get).mockResolvedValue({ current_month_currency: "USD" });

    const result = await getFinanceOverview("USD");

    expect(api.get).toHaveBeenCalledWith("/finances/overview?currency=USD");
    expect(result.current_month_currency).toBe("USD");
  });
});

