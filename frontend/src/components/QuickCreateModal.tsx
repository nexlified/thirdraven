import { useRef, useState } from "react";
import { ClosenessMeter } from "./FormControls";
import type { PersonFieldOptions, PersonSlim, TermSlim } from "../api/persons";
import { createPerson } from "../api/persons";
import { useSettings } from "../hooks/useSettings";

interface Props {
  schema: PersonFieldOptions;
  onClose: () => void;
  onCreated: (person: PersonSlim) => void;
}

export function QuickCreateModal({ schema, onClose, onCreated }: Props) {
  const [settings] = useSettings();

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [nickname, setNickname] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [closenessLevel, setClosenessLevel] = useState<number | null>(settings.defaultClosenessLevel);
  const [relationshipNature, setRelationshipNature] = useState(settings.defaultRelationshipNature);
  const [visibility, setVisibility] = useState<"private" | "household">(settings.defaultVisibility);
  const [tagDropdownOpen, setTagDropdownOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const tagRef = useRef<HTMLDivElement>(null);

  function toggleTag(slug: string) {
    setSelectedTags((prev) =>
      prev.includes(slug) ? prev.filter((s) => s !== slug) : [...prev, slug]
    );
  }

  function handleOverlayClick(e: React.MouseEvent) {
    if (e.target === e.currentTarget) onClose();
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!firstName.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const channels = [];
      if (email.trim()) channels.push({ type: "email", value: email.trim(), is_primary: !phone.trim() });
      if (phone.trim()) channels.push({ type: "mobile", value: phone.trim(), is_primary: true });
      const person = await createPerson({
        first_name: firstName.trim(),
        last_name: lastName.trim() || undefined,
        nickname: nickname.trim() || undefined,
        channels,
        tags: selectedTags,
        closeness_level: closenessLevel,
        relationship_nature: relationshipNature || undefined,
        visibility,
      });
      onCreated(person);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create person");
    } finally {
      setSubmitting(false);
    }
  }

  const selectedTagObjs = schema.tags.filter((t) => selectedTags.includes(t.slug));

  return (
    <div className="modal-overlay" onMouseDown={handleOverlayClick}>
      <div className="modal">
        <div className="modal-header">
          <h3>Quick Add Person</h3>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="form-row">
              <div className="field">
                <label>First name *</label>
                <input
                  type="text"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  placeholder="Jane"
                  autoFocus
                  required
                />
              </div>
              <div className="field">
                <label>Last name</label>
                <input
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  placeholder="Doe"
                />
              </div>
            </div>

            <div className="field">
              <label>Nickname</label>
              <input
                type="text"
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                placeholder="Optional"
              />
            </div>

            <div className="form-row">
              <div className="field">
                <label>Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="jane@example.com"
                />
              </div>
              <div className="field">
                <label>Phone</label>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+1 555 0100"
                />
              </div>
            </div>

            {schema.tags.length > 0 && (
              <div className="field" style={{ position: "relative" }} ref={tagRef}>
                <label>Tags</label>
                <div
                  className="tag-multi"
                  onClick={() => setTagDropdownOpen((o) => !o)}
                >
                  {selectedTagObjs.length === 0 ? (
                    <span className="tag-multi-placeholder">Select tags…</span>
                  ) : (
                    selectedTagObjs.map((t) => (
                      <span key={t.slug} className="tag-pill">{t.name}</span>
                    ))
                  )}
                </div>
                {tagDropdownOpen && (
                  <div className="tag-multi-dropdown">
                    {schema.tags.map((t: TermSlim) => (
                      <div
                        key={t.slug}
                        className={`tag-multi-option${selectedTags.includes(t.slug) ? " selected" : ""}`}
                        onClick={() => toggleTag(t.slug)}
                      >
                        <span className="tag-multi-check">
                          {selectedTags.includes(t.slug) ? "✓" : ""}
                        </span>
                        {t.name}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            <div className="form-row">
              <div className="field">
                <label>Closeness</label>
                <div style={{ paddingTop: 8 }}>
                  <ClosenessMeter
                    level={closenessLevel}
                    onChange={setClosenessLevel}
                  />
                </div>
              </div>
              <div className="field">
                <label>Relationship nature</label>
                <select
                  value={relationshipNature}
                  onChange={(e) => setRelationshipNature(e.target.value as typeof relationshipNature)}
                >
                  <option value="">— none —</option>
                  <option value="personal">Personal</option>
                  <option value="professional">Professional</option>
                  <option value="mixed">Mixed</option>
                </select>
              </div>
            </div>

            <div className="field">
              <label>Visibility</label>
              <select
                value={visibility}
                onChange={(e) => setVisibility(e.target.value as "private" | "household")}
              >
                <option value="private">Private</option>
                <option value="household">Household</option>
              </select>
            </div>

            {error && <div className="form-error">{error}</div>}
          </div>

          <div className="modal-footer">
            <button type="button" className="btn-secondary" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={submitting || !firstName.trim()}>
              {submitting ? "Creating…" : "Create & Open"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
