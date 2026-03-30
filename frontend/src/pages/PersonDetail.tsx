import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { AppLayout } from "../components/AppLayout";
import { SearchableSelect, TermSelect, ClosenessMeter } from "../components/FormControls";
import {
  getPerson, updatePerson, deletePerson,
  addChannel, updateChannel, deleteChannel,
  addAddress, updateAddress, deleteAddress,
  getPersonSchema,
  createRelationship, updateRelationship, deleteRelationship,
  listPersons,
} from "../api/persons";
import type {
  PersonExtended, PersonFieldOptions, ChannelPublic,
  AddressPublic, RelationshipPublic, PersonSlim,
} from "../api/persons";
import { listCountries, listLanguages, listTimezones } from "../api/reference";
import type { CountryPublic, LanguagePublic, TimezonePublic } from "../api/reference";
import { useSettings } from "../hooks/useSettings";

type TabId = "identity" | "professional" | "contacts" | "location" | "context" | "notes" | "relationships";
type SaveStatus = "idle" | "saving" | "saved" | "error";

function SaveButton({ status, onSave }: { status: SaveStatus; onSave: () => void }) {
  return (
    <div className="section-actions">
      {status === "saved" && <span className="save-status saved">Saved ✓</span>}
      {status === "error" && <span className="save-status error">Save failed</span>}
      <button
        className="btn-primary"
        onClick={onSave}
        disabled={status === "saving"}
        style={{ minWidth: 80 }}
      >
        {status === "saving" ? "Saving…" : "Save"}
      </button>
    </div>
  );
}

// ── Identity Tab ──────────────────────────────────────────────────────────────

function IdentityTab({
  person,
  schema,
  countries,
  languages,
  onSave,
}: {
  person: PersonExtended;
  schema: PersonFieldOptions;
  countries: CountryPublic[];
  languages: LanguagePublic[];
  onSave: (patch: Record<string, unknown>) => Promise<void>;
}) {
  const profile = person.profile;
  const [settings] = useSettings();
  const [draft, setDraft] = useState({
    first_name: person.first_name,
    last_name: person.last_name ?? "",
    nickname: person.nickname ?? "",
    middle_name: profile?.middle_name ?? "",
    prefix: profile?.prefix?.slug ?? "",
    date_of_birth: profile?.date_of_birth ?? "",
    gender: profile?.gender?.slug ?? "",
    nationality: profile?.nationality?.alpha2 ?? settings.defaultCountry,
    languages: (profile?.languages ?? []).map((l) => l.iso_639_1).length > 0
      ? (profile?.languages ?? []).map((l) => l.iso_639_1)
      : settings.defaultLanguages,
    closeness_level: person.closeness_level ?? settings.defaultClosenessLevel,
  });
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("idle");

  const countryOptions = countries.map((c) => ({ id: c.alpha2, name: `${c.flag_emoji ?? ""} ${c.name}`.trim() }));
  const langOptions = languages.map((l) => ({ id: l.iso_639_1, name: `${l.name} (${l.iso_639_1})` }));

  function toggleLanguage(code: string) {
    setDraft((d) => ({
      ...d,
      languages: d.languages.includes(code)
        ? d.languages.filter((c) => c !== code)
        : [...d.languages, code],
    }));
  }

  async function handleSave() {
    setSaveStatus("saving");
    try {
      await onSave({
        first_name: draft.first_name,
        last_name: draft.last_name || null,
        nickname: draft.nickname || null,
        middle_name: draft.middle_name || null,
        prefix: draft.prefix || null,
        date_of_birth: draft.date_of_birth || null,
        gender: draft.gender || null,
        nationality: draft.nationality || null,
        languages: draft.languages,
        closeness_level: draft.closeness_level,
      });
      setSaveStatus("saved");
      setTimeout(() => setSaveStatus("idle"), 2500);
    } catch {
      setSaveStatus("error");
      setTimeout(() => setSaveStatus("idle"), 3000);
    }
  }

  const selectedLangs = languages.filter((l) => draft.languages.includes(l.iso_639_1));

  return (
    <div className="section-form">
      <div className="form-row">
        <div className="field">
          <label>First name *</label>
          <input
            type="text"
            value={draft.first_name}
            onChange={(e) => setDraft((d) => ({ ...d, first_name: e.target.value }))}
          />
        </div>
        <div className="field">
          <label>Last name</label>
          <input
            type="text"
            value={draft.last_name}
            onChange={(e) => setDraft((d) => ({ ...d, last_name: e.target.value }))}
          />
        </div>
      </div>
      <div className="form-row">
        <div className="field">
          <label>Nickname</label>
          <input
            type="text"
            value={draft.nickname}
            onChange={(e) => setDraft((d) => ({ ...d, nickname: e.target.value }))}
          />
        </div>
        <div className="field">
          <label>Middle name</label>
          <input
            type="text"
            value={draft.middle_name}
            onChange={(e) => setDraft((d) => ({ ...d, middle_name: e.target.value }))}
          />
        </div>
      </div>
      <div className="form-row">
        <div className="field">
          <label>Prefix</label>
          <TermSelect
            value={draft.prefix}
            onChange={(v) => setDraft((d) => ({ ...d, prefix: v }))}
            options={schema.prefixes}
            placeholder="— none —"
          />
        </div>
        <div className="field">
          <label>Gender</label>
          <TermSelect
            value={draft.gender}
            onChange={(v) => setDraft((d) => ({ ...d, gender: v }))}
            options={schema.genders}
            placeholder="— none —"
          />
        </div>
      </div>
      <div className="form-row">
        <div className="field">
          <label>Date of birth</label>
          <input
            type="date"
            value={draft.date_of_birth}
            onChange={(e) => setDraft((d) => ({ ...d, date_of_birth: e.target.value }))}
          />
        </div>
        <div className="field">
          <label>Closeness</label>
          <div style={{ paddingTop: 8 }}>
            <ClosenessMeter
              level={draft.closeness_level}
              onChange={(v) => setDraft((d) => ({ ...d, closeness_level: v }))}
            />
          </div>
        </div>
      </div>
      <div className="field">
        <label>Nationality</label>
        <SearchableSelect
          value={draft.nationality}
          onChange={(v) => setDraft((d) => ({ ...d, nationality: v }))}
          options={countryOptions}
          placeholder="Search countries…"
          labelKey="name"
          valueKey="id"
        />
      </div>
      <div className="field">
        <label>Languages</label>
        {selectedLangs.length > 0 && (
          <div className="language-pills" style={{ marginBottom: 6 }}>
            {selectedLangs.map((l) => (
              <span key={l.iso_639_1} className="language-pill">
                {l.name}
                <button type="button" onClick={() => toggleLanguage(l.iso_639_1)}>×</button>
              </span>
            ))}
          </div>
        )}
        <SearchableSelect
          value=""
          onChange={(code) => { if (code) toggleLanguage(code); }}
          options={langOptions.filter((l) => !draft.languages.includes(l.id))}
          placeholder="Add a language…"
          labelKey="name"
          valueKey="id"
        />
      </div>
      <SaveButton status={saveStatus} onSave={handleSave} />
    </div>
  );
}

// ── Professional Tab ──────────────────────────────────────────────────────────

function ProfessionalTab({
  person,
  schema,
  onSave,
}: {
  person: PersonExtended;
  schema: PersonFieldOptions;
  onSave: (patch: Record<string, unknown>) => Promise<void>;
}) {
  const pro = person.professional;
  const [draft, setDraft] = useState({
    occupation: pro?.occupation?.slug ?? "",
    company: pro?.company ?? "",
    job_title: pro?.job_title ?? "",
  });
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("idle");

  async function handleSave() {
    setSaveStatus("saving");
    try {
      await onSave({
        occupation: draft.occupation || null,
        company: draft.company || null,
        job_title: draft.job_title || null,
      });
      setSaveStatus("saved");
      setTimeout(() => setSaveStatus("idle"), 2500);
    } catch {
      setSaveStatus("error");
      setTimeout(() => setSaveStatus("idle"), 3000);
    }
  }

  return (
    <div className="section-form">
      <div className="field">
        <label>Occupation</label>
        <TermSelect
          value={draft.occupation}
          onChange={(v) => setDraft((d) => ({ ...d, occupation: v }))}
          options={schema.occupations}
          placeholder="— none —"
        />
      </div>
      <div className="field">
        <label>Company</label>
        <input
          type="text"
          value={draft.company}
          onChange={(e) => setDraft((d) => ({ ...d, company: e.target.value }))}
          placeholder="Acme Corp"
        />
      </div>
      <div className="field">
        <label>Job title</label>
        <input
          type="text"
          value={draft.job_title}
          onChange={(e) => setDraft((d) => ({ ...d, job_title: e.target.value }))}
          placeholder="Software Engineer"
        />
      </div>
      <SaveButton status={saveStatus} onSave={handleSave} />
    </div>
  );
}

// ── Contacts Tab ──────────────────────────────────────────────────────────────

const CHANNEL_ICONS: Record<string, string> = {
  email: "✉", mobile: "📱", phone: "☎", whatsapp: "💬",
  telegram: "✈", discord: "◈", twitter: "◎", linkedin: "◐",
  github: "◉", website: "🌐", signal: "◬", slack: "◧", other: "○",
};

function ContactsTab({
  person,
  schema,
  onRefresh,
}: {
  person: PersonExtended;
  schema: PersonFieldOptions;
  onRefresh: () => Promise<void>;
}) {
  const channels = person.channels ?? [];
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editDraft, setEditDraft] = useState<{ type: string; value: string; label: string; is_primary: boolean }>({
    type: "", value: "", label: "", is_primary: false,
  });
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [addForm, setAddForm] = useState<{ type: string; value: string; label: string; is_primary: boolean } | null>(null);
  const [busy, setBusy] = useState(false);

  function startEdit(ch: ChannelPublic) {
    setEditingId(ch.id);
    setEditDraft({ type: ch.type, value: ch.value, label: ch.label ?? "", is_primary: ch.is_primary });
  }

  async function saveEdit() {
    if (!editingId) return;
    setBusy(true);
    try {
      await updateChannel(person.id, editingId, {
        type: editDraft.type,
        value: editDraft.value,
        label: editDraft.label || undefined,
        is_primary: editDraft.is_primary,
      });
      setEditingId(null);
      await onRefresh();
    } finally { setBusy(false); }
  }

  async function handleDelete(id: string) {
    setBusy(true);
    try {
      await deleteChannel(person.id, id);
      setConfirmDeleteId(null);
      await onRefresh();
    } finally { setBusy(false); }
  }

  async function handleAdd() {
    if (!addForm || !addForm.type || !addForm.value) return;
    setBusy(true);
    try {
      await addChannel(person.id, {
        type: addForm.type,
        value: addForm.value,
        label: addForm.label || undefined,
        is_primary: addForm.is_primary,
      });
      setAddForm(null);
      await onRefresh();
    } finally { setBusy(false); }
  }

  return (
    <div style={{ maxWidth: 640 }}>
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 12 }}>
        <button
          className="btn-secondary"
          onClick={() => setAddForm({ type: "email", value: "", label: "", is_primary: false })}
          disabled={!!addForm}
        >
          + Add contact
        </button>
      </div>

      {channels.length === 0 && !addForm && (
        <div className="empty-state" style={{ paddingTop: 40 }}>
          <span className="empty-icon">✉</span>
          <p>No contact channels yet.</p>
        </div>
      )}

      {channels.map((ch) => (
        <div key={ch.id}>
          {editingId === ch.id ? (
            <div className="channel-row">
              <div className="channel-edit-form">
                <div className="field" style={{ minWidth: 110, flex: "0 0 auto" }}>
                  <select
                    value={editDraft.type}
                    onChange={(e) => setEditDraft((d) => ({ ...d, type: e.target.value }))}
                  >
                    {schema.channel_types.map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
                <div className="field" style={{ flex: 2 }}>
                  <input
                    type="text"
                    value={editDraft.value}
                    onChange={(e) => setEditDraft((d) => ({ ...d, value: e.target.value }))}
                    placeholder="Value"
                  />
                </div>
                <div className="field" style={{ flex: 1 }}>
                  <input
                    type="text"
                    value={editDraft.label}
                    onChange={(e) => setEditDraft((d) => ({ ...d, label: e.target.value }))}
                    placeholder="Label"
                  />
                </div>
                <button className="btn-primary" onClick={saveEdit} disabled={busy} style={{ padding: "9px 14px" }}>
                  {busy ? "…" : "Save"}
                </button>
                <button className="btn-secondary" onClick={() => setEditingId(null)} style={{ padding: "9px 14px" }}>
                  Cancel
                </button>
              </div>
            </div>
          ) : confirmDeleteId === ch.id ? (
            <div className="channel-row">
              <div className="inline-confirm" style={{ flex: 1 }}>
                <span>Delete {ch.type} channel?</span>
                <button className="btn-icon btn-danger-ghost" onClick={() => handleDelete(ch.id)} disabled={busy}>
                  {busy ? "…" : "Delete"}
                </button>
                <button className="btn-secondary" onClick={() => setConfirmDeleteId(null)} style={{ fontSize: 12, padding: "4px 8px" }}>
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="channel-row">
              <span className="channel-type-badge">
                {CHANNEL_ICONS[ch.type] ?? "○"} {ch.type}
              </span>
              <span className="channel-value">{ch.value}</span>
              {ch.label && <span className="channel-label">{ch.label}</span>}
              {ch.is_primary && <span className="channel-primary-star" title="Primary">★</span>}
              <button className="btn-icon" onClick={() => startEdit(ch)} title="Edit">✎</button>
              <button className="btn-icon btn-danger-ghost" onClick={() => setConfirmDeleteId(ch.id)} title="Delete">✕</button>
            </div>
          )}
        </div>
      ))}

      {addForm && (
        <div className="channel-add-form">
          <div className="field" style={{ flex: "0 0 110px" }}>
            <label>Type</label>
            <select
              value={addForm.type}
              onChange={(e) => setAddForm((f) => f && { ...f, type: e.target.value })}
            >
              {schema.channel_types.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          <div className="field" style={{ flex: 2 }}>
            <label>Value</label>
            <input
              type="text"
              value={addForm.value}
              onChange={(e) => setAddForm((f) => f && { ...f, value: e.target.value })}
              placeholder="email@example.com"
              autoFocus
            />
          </div>
          <div className="field" style={{ flex: 1 }}>
            <label>Label</label>
            <input
              type="text"
              value={addForm.label}
              onChange={(e) => setAddForm((f) => f && { ...f, label: e.target.value })}
              placeholder="work"
            />
          </div>
          <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
            <button className="btn-primary" onClick={handleAdd} disabled={busy || !addForm.value}>
              {busy ? "…" : "Add"}
            </button>
            <button className="btn-secondary" onClick={() => setAddForm(null)}>Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Location Tab ──────────────────────────────────────────────────────────────

function LocationTab({
  person,
  timezones,
  onSave,
  onRefresh,
}: {
  person: PersonExtended;
  timezones: TimezonePublic[];
  onSave: (patch: Record<string, unknown>) => Promise<void>;
  onRefresh: () => Promise<void>;
}) {
  const loc = person.location;
  const [settings] = useSettings();
  const [timezone, setTimezone] = useState(loc?.timezone?.name ?? settings.defaultTimezone);
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("idle");
  const [addingAddress, setAddingAddress] = useState(false);
  const [addrForm, setAddrForm] = useState({ type: "home", street: "", city: "", postal_code: "", country: "" });
  const [editingAddressId, setEditingAddressId] = useState<string | null>(null);
  const [editAddrDraft, setEditAddrDraft] = useState({ type: "home", street: "", city: "", postal_code: "", country: "" });
  const [confirmDeleteAddrId, setConfirmDeleteAddrId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const tzOptions = timezones.map((tz) => ({
    id: tz.name,
    name: `${tz.name} (${tz.utc_offset})`,
  }));

  async function handleSaveTz() {
    setSaveStatus("saving");
    try {
      await onSave({ timezone: timezone || null });
      setSaveStatus("saved");
      setTimeout(() => setSaveStatus("idle"), 2500);
    } catch {
      setSaveStatus("error");
      setTimeout(() => setSaveStatus("idle"), 3000);
    }
  }

  async function handleAddAddress() {
    setBusy(true);
    try {
      await addAddress(person.id, {
        type: addrForm.type,
        street: addrForm.street || undefined,
        city: addrForm.city || undefined,
        postal_code: addrForm.postal_code || undefined,
        country: addrForm.country || undefined,
      });
      setAddingAddress(false);
      setAddrForm({ type: "home", street: "", city: "", postal_code: "", country: "" });
      await onRefresh();
    } finally { setBusy(false); }
  }

  async function handleUpdateAddress(id: string) {
    setBusy(true);
    try {
      await updateAddress(person.id, id, {
        type: editAddrDraft.type,
        street: editAddrDraft.street || undefined,
        city: editAddrDraft.city || undefined,
        postal_code: editAddrDraft.postal_code || undefined,
        country: editAddrDraft.country || undefined,
      });
      setEditingAddressId(null);
      await onRefresh();
    } finally { setBusy(false); }
  }

  async function handleDeleteAddress(id: string) {
    setBusy(true);
    try {
      await deleteAddress(person.id, id);
      setConfirmDeleteAddrId(null);
      await onRefresh();
    } finally { setBusy(false); }
  }

  function startEditAddress(addr: AddressPublic) {
    setEditingAddressId(addr.id);
    setEditAddrDraft({
      type: addr.type,
      street: addr.street ?? "",
      city: addr.city ?? "",
      postal_code: addr.postal_code ?? "",
      country: addr.country?.alpha2 ?? "",
    });
  }

  const addresses = loc?.addresses ?? [];

  return (
    <div style={{ maxWidth: 640 }}>
      <div className="section-form" style={{ marginBottom: 28 }}>
        <div className="field">
          <label>Timezone</label>
          <SearchableSelect
            value={timezone}
            onChange={setTimezone}
            options={tzOptions}
            placeholder="Search timezones…"
            labelKey="name"
            valueKey="id"
          />
        </div>
        <SaveButton status={saveStatus} onSave={handleSaveTz} />
      </div>

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
        <h3 style={{ fontSize: 14, fontWeight: 600 }}>Addresses</h3>
        <button className="btn-secondary" onClick={() => setAddingAddress(true)} disabled={addingAddress}>
          + Add address
        </button>
      </div>

      {addresses.map((addr) => (
        <div key={addr.id}>
          {editingAddressId === addr.id ? (
            <div className="address-form">
              <div className="form-row">
                <div className="field">
                  <label>Type</label>
                  <select value={editAddrDraft.type} onChange={(e) => setEditAddrDraft((d) => ({ ...d, type: e.target.value }))}>
                    {["home", "work", "other"].map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div className="field">
                  <label>Country (ISO alpha2)</label>
                  <input type="text" value={editAddrDraft.country} onChange={(e) => setEditAddrDraft((d) => ({ ...d, country: e.target.value }))} placeholder="US" maxLength={2} />
                </div>
              </div>
              <div className="field">
                <label>Street</label>
                <input type="text" value={editAddrDraft.street} onChange={(e) => setEditAddrDraft((d) => ({ ...d, street: e.target.value }))} />
              </div>
              <div className="form-row">
                <div className="field">
                  <label>City</label>
                  <input type="text" value={editAddrDraft.city} onChange={(e) => setEditAddrDraft((d) => ({ ...d, city: e.target.value }))} />
                </div>
                <div className="field">
                  <label>Postal code</label>
                  <input type="text" value={editAddrDraft.postal_code} onChange={(e) => setEditAddrDraft((d) => ({ ...d, postal_code: e.target.value }))} />
                </div>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <button className="btn-primary" onClick={() => handleUpdateAddress(addr.id)} disabled={busy}>{busy ? "…" : "Save"}</button>
                <button className="btn-secondary" onClick={() => setEditingAddressId(null)}>Cancel</button>
              </div>
            </div>
          ) : confirmDeleteAddrId === addr.id ? (
            <div className="address-row">
              <div className="inline-confirm">
                <span>Delete this address?</span>
                <button className="btn-icon btn-danger-ghost" onClick={() => handleDeleteAddress(addr.id)} disabled={busy}>{busy ? "…" : "Delete"}</button>
                <button className="btn-secondary" onClick={() => setConfirmDeleteAddrId(null)} style={{ fontSize: 12, padding: "4px 8px" }}>Cancel</button>
              </div>
            </div>
          ) : (
            <div className="address-row">
              <div className="address-row-header">
                <span className="address-type-badge">{addr.type}</span>
                <div style={{ display: "flex", gap: 6 }}>
                  <button className="btn-icon" onClick={() => startEditAddress(addr)} title="Edit">✎</button>
                  <button className="btn-icon btn-danger-ghost" onClick={() => setConfirmDeleteAddrId(addr.id)} title="Delete">✕</button>
                </div>
              </div>
              <div className="address-text">
                {[addr.street, addr.city, addr.postal_code, addr.country?.name].filter(Boolean).join(", ") || "No details"}
              </div>
            </div>
          )}
        </div>
      ))}

      {addingAddress && (
        <div className="address-form">
          <div className="form-row">
            <div className="field">
              <label>Type</label>
              <select value={addrForm.type} onChange={(e) => setAddrForm((f) => ({ ...f, type: e.target.value }))}>
                {["home", "work", "other"].map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div className="field">
              <label>Country (ISO alpha2)</label>
              <input type="text" value={addrForm.country} onChange={(e) => setAddrForm((f) => ({ ...f, country: e.target.value }))} placeholder="US" maxLength={2} />
            </div>
          </div>
          <div className="field">
            <label>Street</label>
            <input type="text" value={addrForm.street} onChange={(e) => setAddrForm((f) => ({ ...f, street: e.target.value }))} autoFocus />
          </div>
          <div className="form-row">
            <div className="field">
              <label>City</label>
              <input type="text" value={addrForm.city} onChange={(e) => setAddrForm((f) => ({ ...f, city: e.target.value }))} />
            </div>
            <div className="field">
              <label>Postal code</label>
              <input type="text" value={addrForm.postal_code} onChange={(e) => setAddrForm((f) => ({ ...f, postal_code: e.target.value }))} />
            </div>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button className="btn-primary" onClick={handleAddAddress} disabled={busy}>{busy ? "…" : "Add"}</button>
            <button className="btn-secondary" onClick={() => setAddingAddress(false)}>Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Context Tab ───────────────────────────────────────────────────────────────

function ContextTab({
  person,
  schema,
  onSave,
}: {
  person: PersonExtended;
  schema: PersonFieldOptions;
  onSave: (patch: Record<string, unknown>) => Promise<void>;
}) {
  const ctx = person.context;
  const [settings] = useSettings();
  const [draft, setDraft] = useState({
    how_we_met: ctx?.how_we_met ?? "",
    first_met_on: ctx?.first_met_on ?? "",
    last_contacted_on: ctx?.last_contacted_on ?? "",
    contact_frequency_days: ctx?.contact_frequency_days ?? "",
    preferred_contact: ctx?.preferred_contact?.slug ?? "",
    relationship_nature: ctx?.relationship_nature ?? settings.defaultRelationshipNature,
  });
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("idle");

  async function handleSave() {
    setSaveStatus("saving");
    try {
      await onSave({
        how_we_met: draft.how_we_met || null,
        first_met_on: draft.first_met_on || null,
        last_contacted_on: draft.last_contacted_on || null,
        contact_frequency_days: draft.contact_frequency_days ? Number(draft.contact_frequency_days) : null,
        preferred_contact: draft.preferred_contact || null,
        relationship_nature: draft.relationship_nature || null,
      });
      setSaveStatus("saved");
      setTimeout(() => setSaveStatus("idle"), 2500);
    } catch {
      setSaveStatus("error");
      setTimeout(() => setSaveStatus("idle"), 3000);
    }
  }

  return (
    <div className="section-form">
      <div className="field">
        <label>How we met</label>
        <textarea
          value={draft.how_we_met}
          onChange={(e) => setDraft((d) => ({ ...d, how_we_met: e.target.value }))}
          placeholder="We met at…"
          style={{ minHeight: 80 }}
        />
      </div>
      <div className="form-row">
        <div className="field">
          <label>First met on</label>
          <input type="date" value={draft.first_met_on} onChange={(e) => setDraft((d) => ({ ...d, first_met_on: e.target.value }))} />
        </div>
        <div className="field">
          <label>Last contacted on</label>
          <input type="date" value={draft.last_contacted_on} onChange={(e) => setDraft((d) => ({ ...d, last_contacted_on: e.target.value }))} />
        </div>
      </div>
      <div className="form-row">
        <div className="field">
          <label>Contact frequency (days)</label>
          <input
            type="number"
            min={1}
            value={draft.contact_frequency_days}
            onChange={(e) => setDraft((d) => ({ ...d, contact_frequency_days: e.target.value }))}
            placeholder="30"
          />
        </div>
        <div className="field">
          <label>Preferred contact</label>
          <TermSelect
            value={draft.preferred_contact}
            onChange={(v) => setDraft((d) => ({ ...d, preferred_contact: v }))}
            options={schema.preferred_contact}
          />
        </div>
      </div>
      <div className="field">
        <label>Relationship nature</label>
        <select
          value={draft.relationship_nature}
          onChange={(e) => setDraft((d) => ({ ...d, relationship_nature: e.target.value }))}
        >
          <option value="">— none —</option>
          <option value="personal">Personal</option>
          <option value="professional">Professional</option>
          <option value="mixed">Mixed</option>
        </select>
      </div>
      <SaveButton status={saveStatus} onSave={handleSave} />
    </div>
  );
}

// ── Notes Tab ─────────────────────────────────────────────────────────────────

function NotesTab({
  person,
  onSave,
}: {
  person: PersonExtended;
  onSave: (patch: Record<string, unknown>) => Promise<void>;
}) {
  const [notes, setNotes] = useState(person.notes ?? "");
  const [noteStatus, setNoteStatus] = useState<"idle" | "saving" | "saved">("idle");
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (notes === (person.notes ?? "")) return;
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(async () => {
      setNoteStatus("saving");
      try {
        await onSave({ notes: notes || null });
        setNoteStatus("saved");
        setTimeout(() => setNoteStatus("idle"), 2000);
      } catch {
        setNoteStatus("idle");
      }
    }, 2000);
    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [notes]);

  return (
    <div className="section-form">
      <div className="field">
        <label>Notes</label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Free-form notes about this person…"
          style={{ minHeight: 200 }}
        />
      </div>
      <div className={`notes-status${noteStatus === "saved" ? " saved" : ""}`}>
        {noteStatus === "saving" && "Saving…"}
        {noteStatus === "saved" && "Saved ✓"}
      </div>
    </div>
  );
}

// ── Relationships Tab ─────────────────────────────────────────────────────────

function RelationshipsTab({
  person,
  schema,
  onRefresh,
}: {
  person: PersonExtended;
  schema: PersonFieldOptions;
  onRefresh: () => Promise<void>;
}) {
  const [allPersons, setAllPersons] = useState<PersonSlim[] | null>(null);
  const [personsLoading, setPersonsLoading] = useState(false);
  const [personsQuery, setPersonsQuery] = useState("");
  const [addForm, setAddForm] = useState<{ toPersonId: string; label: string } | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editLabel, setEditLabel] = useState("");
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);

  async function openAddForm() {
    setAddForm({ toPersonId: "", label: schema.relationship_types[0]?.slug ?? "" });
    setAddError(null);
    if (allPersons === null) {
      setPersonsLoading(true);
      try {
        const res = await listPersons({ skip: 0, limit: 200 });
        setAllPersons(res.items.filter((p) => p.id !== person.id));
      } finally {
        setPersonsLoading(false);
      }
    }
  }

  const filteredPersons = (allPersons ?? []).filter((p) => {
    if (!personsQuery.trim()) return true;
    const full = [p.first_name, p.last_name, p.nickname].filter(Boolean).join(" ").toLowerCase();
    return full.includes(personsQuery.toLowerCase());
  });

  const personOptions = filteredPersons.map((p) => ({
    id: p.id,
    name: [p.first_name, p.last_name].filter(Boolean).join(" ") + (p.nickname ? ` (${p.nickname})` : ""),
  }));

  async function handleAdd() {
    if (!addForm?.toPersonId || !addForm?.label) return;
    setBusy(true);
    setAddError(null);
    try {
      await createRelationship(person.id, {
        to_person_id: addForm.toPersonId,
        label: addForm.label,
      });
      setAddForm(null);
      setPersonsQuery("");
      await onRefresh();
    } catch (err) {
      setAddError(err instanceof Error ? err.message : "Failed to create relationship");
    } finally {
      setBusy(false);
    }
  }

  function startEdit(rel: RelationshipPublic) {
    setEditingId(rel.id);
    setEditLabel(rel.label.slug);
    setConfirmDeleteId(null);
  }

  async function handleUpdate(relId: string) {
    setBusy(true);
    try {
      await updateRelationship(relId, { label: editLabel });
      setEditingId(null);
      await onRefresh();
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(relId: string) {
    setBusy(true);
    try {
      await deleteRelationship(relId);
      setConfirmDeleteId(null);
      await onRefresh();
    } finally {
      setBusy(false);
    }
  }

  const rels = person.relationships ?? [];

  return (
    <div className="relationships-tab">
      <div className="relationships-header">
        <h3>Relationships{rels.length > 0 ? ` (${rels.length})` : ""}</h3>
        <button className="btn-secondary" onClick={openAddForm} disabled={!!addForm}>
          + Add relationship
        </button>
      </div>

      {addForm !== null && (
        <div className="relationship-add-form">
          <div className="field" style={{ flex: 2, minWidth: 200 }}>
            <label>Person</label>
            {personsLoading ? (
              <div style={{ fontSize: 13, color: "var(--text-muted)", padding: "10px 0" }}>Loading…</div>
            ) : (
              <>
                <input
                  className="search-input"
                  style={{ width: "100%", marginBottom: 6 }}
                  type="search"
                  placeholder="Search people…"
                  value={personsQuery}
                  onChange={(e) => setPersonsQuery(e.target.value)}
                />
                <select
                  value={addForm.toPersonId}
                  onChange={(e) => setAddForm((f) => f && { ...f, toPersonId: e.target.value })}
                  size={Math.min(6, personOptions.length + 1)}
                  style={{
                    background: "var(--bg-elevated)", border: "1px solid var(--border)",
                    borderRadius: "var(--radius)", padding: "4px 8px", color: "var(--text-strong)",
                    fontFamily: "inherit", fontSize: 13, width: "100%",
                  }}
                >
                  <option value="">— select person —</option>
                  {personOptions.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </>
            )}
          </div>
          <div className="field" style={{ flex: 1, minWidth: 140 }}>
            <label>Relationship label</label>
            <TermSelect
              value={addForm.label}
              onChange={(v) => setAddForm((f) => f && { ...f, label: v })}
              options={schema.relationship_types}
              placeholder="— select —"
            />
          </div>
          <div style={{ display: "flex", gap: 8, alignItems: "flex-end", paddingBottom: 1 }}>
            <button
              className="btn-primary"
              onClick={handleAdd}
              disabled={busy || !addForm.toPersonId || !addForm.label}
              style={{ padding: "9px 14px" }}
            >
              {busy ? "…" : "Add"}
            </button>
            <button className="btn-secondary" onClick={() => { setAddForm(null); setPersonsQuery(""); }} style={{ padding: "9px 14px" }}>
              Cancel
            </button>
          </div>
          {addError && <div className="form-error" style={{ width: "100%" }}>{addError}</div>}
        </div>
      )}

      {rels.length === 0 && !addForm && (
        <div className="empty-state" style={{ paddingTop: 40 }}>
          <span className="empty-icon">◎</span>
          <p>No relationships added yet.</p>
        </div>
      )}

      {rels.map((rel) => (
        <div key={rel.id} className="relationship-row">
          {editingId === rel.id ? (
            <div className="relationship-edit-inline" style={{ flex: 1 }}>
              <Link to={`/people/${rel.related_person.id}`} className="relationship-person-link">
                {rel.related_person.first_name} {rel.related_person.last_name}
              </Link>
              <select
                value={editLabel}
                onChange={(e) => setEditLabel(e.target.value)}
                style={{
                  background: "var(--bg-elevated)", border: "1px solid var(--border)",
                  borderRadius: "var(--radius)", padding: "6px 10px", color: "var(--text-strong)",
                  fontFamily: "inherit", fontSize: 13,
                }}
              >
                {schema.relationship_types.map((t) => (
                  <option key={t.slug} value={t.slug}>{t.name}</option>
                ))}
              </select>
              <button className="btn-primary" onClick={() => handleUpdate(rel.id)} disabled={busy} style={{ padding: "6px 12px", fontSize: 12 }}>
                {busy ? "…" : "Save"}
              </button>
              <button className="btn-secondary" onClick={() => setEditingId(null)} style={{ padding: "6px 10px", fontSize: 12 }}>
                Cancel
              </button>
            </div>
          ) : confirmDeleteId === rel.id ? (
            <>
              <Link to={`/people/${rel.related_person.id}`} className="relationship-person-link">
                {rel.related_person.first_name} {rel.related_person.last_name}
              </Link>
              <div className="inline-confirm">
                <span>Remove relationship?</span>
                <button className="btn-icon btn-danger-ghost" onClick={() => handleDelete(rel.id)} disabled={busy}>
                  {busy ? "…" : "Remove"}
                </button>
                <button className="btn-secondary" onClick={() => setConfirmDeleteId(null)} style={{ fontSize: 12, padding: "4px 8px" }}>
                  Cancel
                </button>
              </div>
            </>
          ) : (
            <>
              <Link to={`/people/${rel.related_person.id}`} className="relationship-person-link">
                {rel.related_person.first_name} {rel.related_person.last_name}
                {rel.related_person.nickname && (
                  <span style={{ fontWeight: 400, color: "var(--text-muted)", marginLeft: 6 }}>
                    ({rel.related_person.nickname})
                  </span>
                )}
              </Link>
              <span className="relationship-label-badge">{rel.label.name}</span>
              <button className="btn-icon" onClick={() => startEdit(rel)} title="Edit label">✎</button>
              <button className="btn-icon btn-danger-ghost" onClick={() => { setConfirmDeleteId(rel.id); setEditingId(null); }} title="Remove">✕</button>
            </>
          )}
        </div>
      ))}
    </div>
  );
}

// ── Main PersonDetail component ───────────────────────────────────────────────

export function PersonDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [person, setPerson] = useState<PersonExtended | null>(null);
  const [schema, setSchema] = useState<PersonFieldOptions | null>(null);
  const [countries, setCountries] = useState<CountryPublic[]>([]);
  const [languages, setLanguages] = useState<LanguagePublic[]>([]);
  const [timezones, setTimezones] = useState<TimezonePublic[]>([]);
  const [activeTab, setActiveTab] = useState<TabId>("identity");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  async function loadPerson() {
    if (!id) return;
    const data = await getPerson(id, ["profile", "professional", "location", "context", "channels"]);
    setPerson(data);
  }

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    Promise.all([
      getPerson(id, ["profile", "professional", "location", "context", "channels"]),
      getPersonSchema(),
    ])
      .then(([p, s]) => { setPerson(p); setSchema(s); })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, [id]);

  // Lazy-load reference data when tabs are first activated
  useEffect(() => {
    if (activeTab === "identity" && countries.length === 0) {
      listCountries().then(setCountries).catch(() => {});
      listLanguages().then(setLanguages).catch(() => {});
    }
    if (activeTab === "location" && timezones.length === 0) {
      listTimezones().then(setTimezones).catch(() => {});
    }
  }, [activeTab, countries.length, timezones.length]);

  async function handleSave(patch: Record<string, unknown>) {
    if (!id) return;
    await updatePerson(id, patch);
    await loadPerson();
  }

  async function handleDelete() {
    if (!id) return;
    setDeleting(true);
    try {
      await deletePerson(id);
      navigate("/people");
    } finally {
      setDeleting(false);
    }
  }

  if (loading) {
    return (
      <AppLayout title="Loading…">
        <div className="splash"><div className="spinner" /></div>
      </AppLayout>
    );
  }

  if (error || !person || !schema) {
    return (
      <AppLayout title="Error">
        <div className="form-error">{error ?? "Person not found"}</div>
        <Link to="/people">← Back to People</Link>
      </AppLayout>
    );
  }

  const fullName = [person.first_name, person.last_name].filter(Boolean).join(" ");
  const missingHints = [
    !person.channels?.length && { label: "Add contact info", tab: "contacts" as TabId },
    !person.professional?.occupation && !person.professional?.company && { label: "Add occupation", tab: "professional" as TabId },
    !person.context?.how_we_met && { label: "Add context", tab: "context" as TabId },
  ].filter(Boolean) as { label: string; tab: TabId }[];

  const TABS: { id: TabId; label: string }[] = [
    { id: "identity", label: "Identity" },
    { id: "professional", label: "Professional" },
    { id: "contacts", label: `Contacts${person.channels?.length ? ` (${person.channels.length})` : ""}` },
    { id: "location", label: "Location" },
    { id: "context", label: "Context" },
    { id: "notes", label: "Notes" },
    { id: "relationships", label: `Relationships${person.relationships?.length ? ` (${person.relationships.length})` : ""}` },
  ];

  return (
    <AppLayout title="">
      <div className="breadcrumb">
        <Link to="/people">← People</Link>
        <span>/</span>
        <span>{fullName}</span>
      </div>

      <div className="person-detail-header">
        <div className="person-header-left">
          <div className="person-name-display">{fullName}</div>
          {person.nickname && (
            <div className="person-nickname-display">"{person.nickname}"</div>
          )}
          {person.tags.length > 0 && (
            <div className="person-header-tags">
              {person.tags.map((t) => (
                <span key={t.id} className="tag-pill">{t.name}</span>
              ))}
            </div>
          )}
          <div className="person-contact-links">
            {person.email && (
              <span className="person-contact-link">
                ✉ <a href={`mailto:${person.email}`}>{person.email}</a>
              </span>
            )}
            {person.phone && (
              <span className="person-contact-link">
                📱 <a href={`tel:${person.phone}`}>{person.phone}</a>
              </span>
            )}
          </div>
          {missingHints.length > 0 && (
            <div className="completeness-hints">
              {missingHints.map((h, i) => (
                <span key={h.tab}>
                  {i > 0 && <span style={{ color: "var(--border)" }}> · </span>}
                  <a onClick={() => setActiveTab(h.tab)}>{h.label}</a>
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="person-header-actions">
          {confirmDelete ? (
            <div className="inline-confirm">
              <span>Delete person?</span>
              <button className="btn-icon btn-danger-ghost" onClick={handleDelete} disabled={deleting}>
                {deleting ? "…" : "Delete"}
              </button>
              <button className="btn-secondary" onClick={() => setConfirmDelete(false)} style={{ fontSize: 12, padding: "4px 8px" }}>
                Cancel
              </button>
            </div>
          ) : (
            <button className="btn-icon btn-danger-ghost" onClick={() => setConfirmDelete(true)} title="Delete person">
              ✕
            </button>
          )}
        </div>
      </div>

      <div className="tab-bar">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`tab-btn${activeTab === tab.id ? " active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "identity" && (
        <IdentityTab
          person={person}
          schema={schema}
          countries={countries}
          languages={languages}
          onSave={handleSave}
        />
      )}
      {activeTab === "professional" && (
        <ProfessionalTab person={person} schema={schema} onSave={handleSave} />
      )}
      {activeTab === "contacts" && (
        <ContactsTab person={person} schema={schema} onRefresh={loadPerson} />
      )}
      {activeTab === "location" && (
        <LocationTab
          person={person}
          timezones={timezones}
          onSave={handleSave}
          onRefresh={loadPerson}
        />
      )}
      {activeTab === "context" && (
        <ContextTab person={person} schema={schema} onSave={handleSave} />
      )}
      {activeTab === "notes" && (
        <NotesTab person={person} onSave={handleSave} />
      )}
      {activeTab === "relationships" && (
        <RelationshipsTab person={person} schema={schema} onRefresh={loadPerson} />
      )}
    </AppLayout>
  );
}
