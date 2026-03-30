import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AppLayout } from "../components/AppLayout";
import { QuickCreateModal } from "../components/QuickCreateModal";
import { listPersons, getPersonSchema } from "../api/persons";
import type { PersonSlim, PersonFieldOptions } from "../api/persons";

const PAGE_SIZE = 25;

function ClosenessMeter({ level }: { level: number | null }) {
  return (
    <div className="closeness-meter">
      {[1, 2, 3, 4, 5].map((i) => (
        <span key={i} className={`closeness-dot${level !== null && i <= level ? " filled" : ""}`} />
      ))}
    </div>
  );
}

export function People() {
  const navigate = useNavigate();
  const [persons, setPersons] = useState<PersonSlim[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [schema, setSchema] = useState<PersonFieldOptions | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      listPersons({ skip: page * PAGE_SIZE, limit: PAGE_SIZE }),
      schema ? Promise.resolve(schema) : getPersonSchema(),
    ])
      .then(([res, schemaRes]) => {
        setPersons(res.items);
        setTotal(res.total);
        if (!schema) setSchema(schemaRes);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"))
      .finally(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const filtered = search.trim()
    ? persons.filter((p) => {
        const full = [p.first_name, p.last_name, p.nickname].filter(Boolean).join(" ").toLowerCase();
        return full.includes(search.toLowerCase());
      })
    : persons;

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <AppLayout
      title="People"
      subtitle={total > 0 ? `${total} person${total !== 1 ? "s" : ""} in your network` : undefined}
      headerRight={
        <button className="btn-primary" onClick={() => setShowModal(true)}>
          + Quick Add
        </button>
      }
    >
      <div className="people-toolbar">
        <input
          className="search-input"
          type="search"
          placeholder="Search current page…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        {search && (
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
            {filtered.length} of {persons.length} shown
          </span>
        )}
      </div>

      {loading ? (
        <div className="splash"><div className="spinner" /></div>
      ) : error ? (
        <div className="form-error">{error}</div>
      ) : filtered.length === 0 ? (
        <div className="empty-state" style={{ paddingTop: 80 }}>
          <span className="empty-icon">◎</span>
          <p>
            {total === 0
              ? "No people yet. Click \"+ Quick Add\" to add your first person."
              : "No people match your search."}
          </p>
        </div>
      ) : (
        <table className="people-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Tags</th>
              <th>Closeness</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Added</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((p) => (
              <tr key={p.id} onClick={() => navigate(`/people/${p.id}`)}>
                <td>
                  <div className="person-name">
                    {p.first_name} {p.last_name}
                  </div>
                  {p.nickname && <div className="person-nickname">{p.nickname}</div>}
                </td>
                <td>
                  <div className="people-tags">
                    {p.tags.slice(0, 3).map((t) => (
                      <span key={t.id} className="tag-pill">{t.name}</span>
                    ))}
                    {p.tags.length > 3 && (
                      <span className="tag-pill">+{p.tags.length - 3}</span>
                    )}
                  </div>
                </td>
                <td><ClosenessMeter level={p.closeness_level} /></td>
                <td className="person-contact">{p.email ?? "—"}</td>
                <td className="person-contact">{p.phone ?? "—"}</td>
                <td className="person-date">
                  {new Date(p.created_at).toLocaleDateString("en-US", {
                    month: "short", day: "numeric", year: "numeric",
                  })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

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

      {showModal && schema && (
        <QuickCreateModal
          schema={schema}
          onClose={() => setShowModal(false)}
          onCreated={(person) => {
            setShowModal(false);
            navigate(`/people/${person.id}`);
          }}
        />
      )}
    </AppLayout>
  );
}
