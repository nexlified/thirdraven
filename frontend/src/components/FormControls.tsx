import { useEffect, useRef, useState } from "react";
import type { TermSlim } from "../api/persons";

// ── SearchableSelect ──────────────────────────────────────────────────────────
// A freetext-searchable dropdown that maps a display label to a value key.
// `options` is an array of plain objects; `labelKey` and `valueKey` specify
// which property to display vs. what value to emit via `onChange`.

export interface SelectOption {
  [key: string]: string;
}

export function SearchableSelect({
  value,
  onChange,
  options,
  placeholder,
  labelKey = "name",
  valueKey = "id",
}: {
  value: string;
  onChange: (v: string) => void;
  options: SelectOption[];
  placeholder?: string;
  labelKey?: string;
  valueKey?: string;
}) {
  const [query, setQuery] = useState(
    value ? (options.find((o) => o[valueKey] === value)?.[labelKey] ?? value) : ""
  );
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!value) { setQuery(""); return; }
    const match = options.find((o) => o[valueKey] === value);
    if (match) setQuery(match[labelKey]);
  }, [value, options, valueKey, labelKey]);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
        if (!value) setQuery("");
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [value]);

  const filtered = query
    ? options.filter((o) => o[labelKey].toLowerCase().includes(query.toLowerCase()))
    : options;

  return (
    <div className="searchable-select" ref={ref}>
      <input
        type="text"
        value={query}
        placeholder={placeholder}
        onChange={(e) => { setQuery(e.target.value); setOpen(true); onChange(""); }}
        onFocus={() => setOpen(true)}
      />
      {open && filtered.length > 0 && (
        <div className="searchable-select-dropdown">
          <div
            className="searchable-select-option"
            onClick={() => { onChange(""); setQuery(""); setOpen(false); }}
          >
            <em style={{ color: "var(--text-muted)" }}>Clear</em>
          </div>
          {filtered.slice(0, 100).map((o) => (
            <div
              key={o[valueKey]}
              className="searchable-select-option"
              onClick={() => { onChange(o[valueKey]); setQuery(o[labelKey]); setOpen(false); }}
            >
              {o[labelKey]}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── TermSelect ────────────────────────────────────────────────────────────────
// A simple <select> backed by a list of TermSlim objects.

export function TermSelect({
  value,
  onChange,
  options,
  placeholder,
}: {
  value: string;
  onChange: (slug: string) => void;
  options: TermSlim[];
  placeholder?: string;
}) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)}>
      <option value="">{placeholder ?? "— none —"}</option>
      {options.map((t) => (
        <option key={t.slug} value={t.slug}>{t.name}</option>
      ))}
    </select>
  );
}

// ── ClosenessMeter ────────────────────────────────────────────────────────────
// 5-dot rating control. Click a dot to set; click the same dot to clear.

export function ClosenessMeter({
  level,
  onChange,
  readonly = false,
}: {
  level: number | null;
  onChange?: (v: number | null) => void;
  readonly?: boolean;
}) {
  return (
    <div className="closeness-meter" style={{ gap: 5 }}>
      {[1, 2, 3, 4, 5].map((i) => (
        <span
          key={i}
          className={`closeness-dot${level !== null && i <= level ? " filled" : ""}`}
          style={{ width: 12, height: 12, cursor: readonly ? "default" : "pointer" }}
          onClick={() => !readonly && onChange && onChange(level === i ? null : i)}
          title={readonly ? undefined : `Closeness ${i}`}
        />
      ))}
    </div>
  );
}
