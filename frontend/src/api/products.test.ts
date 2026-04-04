import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  createProduct,
  deleteProduct,
  getProductItems,
  listProducts,
  updateProduct,
} from "./products";
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

const mockProduct = {
  id: "prod-1",
  owner_id: "owner-1",
  name: "Milk",
  brand: "Acme",
  category: null,
  unit: "L",
  barcode: null,
  priceraven_product_id: null,
  notes: null,
  created_at: "2026-04-04T10:00:00Z",
  updated_at: "2026-04-04T10:00:00Z",
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("listProducts", () => {
  it("calls GET /products with no params", async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [mockProduct], total: 1, skip: 0, limit: 25 });

    const result = await listProducts();

    expect(api.get).toHaveBeenCalledWith("/products");
    expect(result.items[0].name).toBe("Milk");
  });

  it("appends filters", async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [], total: 0, skip: 0, limit: 25 });

    await listProducts({ category: "grocery", search: "milk", limit: 10 });

    const url = vi.mocked(api.get).mock.calls[0][0] as string;
    expect(url).toContain("/products?");
    expect(url).toContain("category=grocery");
    expect(url).toContain("search=milk");
    expect(url).toContain("limit=10");
  });
});

describe("product mutations", () => {
  it("creates product", async () => {
    vi.mocked(api.post).mockResolvedValue(mockProduct);

    const result = await createProduct({ name: "Milk", unit: "L" });

    expect(api.post).toHaveBeenCalledWith("/products", { name: "Milk", unit: "L" });
    expect(result.id).toBe("prod-1");
  });

  it("updates and deletes product", async () => {
    vi.mocked(api.patch).mockResolvedValue({ ...mockProduct, brand: "Better Acme" });
    vi.mocked(api.delete).mockResolvedValue(undefined);

    const result = await updateProduct("prod-1", { brand: "Better Acme" });
    await deleteProduct("prod-1");

    expect(api.patch).toHaveBeenCalledWith("/products/prod-1", { brand: "Better Acme" });
    expect(api.delete).toHaveBeenCalledWith("/products/prod-1");
    expect(result.brand).toBe("Better Acme");
  });
});

describe("getProductItems", () => {
  it("calls /products/{id}/items with pagination", async () => {
    vi.mocked(api.get).mockResolvedValue({ items: [], total: 0, skip: 0, limit: 50 });

    await getProductItems("prod-1", { skip: 0, limit: 50 });

    expect(api.get).toHaveBeenCalledWith("/products/prod-1/items?skip=0&limit=50");
  });
});

