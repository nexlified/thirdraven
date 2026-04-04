export interface TermSlim {
  id: string;
  name: string;
  slug: string;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

