import { useEffect, useState } from "react";
import { AppLayout } from "../components/AppLayout";
import { SearchableSelect, ClosenessMeter } from "../components/FormControls";
import { useSettings } from "../hooks/useSettings";
import type { UserSettings } from "../hooks/useSettings";
import { listCountries, listLanguages, listTimezones } from "../api/reference";
import type { CountryPublic, LanguagePublic, TimezonePublic } from "../api/reference";

export function Settings() {
  const [settings, saveSettings] = useSettings();
  const [draft, setDraft] = useState<UserSettings>({ ...settings });
  const [saveStatus, setSaveStatus] = useState<"idle" | "saved">("idle");

  const [countries, setCountries] = useState<CountryPublic[]>([]);
  const [languages, setLanguages] = useState<LanguagePublic[]>([]);
  const [timezones, setTimezones] = useState<TimezonePublic[]>([]);
  const [refLoading, setRefLoading] = useState(true);

  useEffect(() => {
    Promise.all([listCountries(), listLanguages(), listTimezones()])
      .then(([c, l, tz]) => { setCountries(c); setLanguages(l); setTimezones(tz); })
      .catch(() => {})
      .finally(() => setRefLoading(false));
  }, []);

  const countryOptions = countries.map((c) => ({
    id: c.alpha2,
    name: `${c.flag_emoji ?? ""} ${c.name}`.trim(),
  }));

  const tzOptions = timezones.map((tz) => ({
    id: tz.name,
    name: `${tz.name} (${tz.utc_offset})`,
  }));

  const langOptions = languages.map((l) => ({
    id: l.iso_639_1,
    name: `${l.name} (${l.iso_639_1})`,
  }));

  const selectedLangs = languages.filter((l) => draft.defaultLanguages.includes(l.iso_639_1));

  function toggleLanguage(code: string) {
    setDraft((d) => ({
      ...d,
      defaultLanguages: d.defaultLanguages.includes(code)
        ? d.defaultLanguages.filter((c) => c !== code)
        : [...d.defaultLanguages, code],
    }));
  }

  function handleSave() {
    saveSettings(draft);
    setSaveStatus("saved");
    setTimeout(() => setSaveStatus("idle"), 2500);
  }

  return (
    <AppLayout
      title="Settings"
      subtitle="Default values pre-fill forms when creating or editing people."
    >
      {refLoading ? (
        <div className="splash"><div className="spinner" /></div>
      ) : (
        <div className="settings-page">
          {/* ── Location defaults ── */}
          <section className="settings-section">
            <div className="settings-section-title">Location defaults</div>

            <div className="field">
              <label>Default country</label>
              <SearchableSelect
                value={draft.defaultCountry}
                onChange={(v) => setDraft((d) => ({ ...d, defaultCountry: v }))}
                options={countryOptions}
                placeholder="Search countries… (e.g. India)"
              />
            </div>

            <div className="field">
              <label>Default timezone</label>
              <SearchableSelect
                value={draft.defaultTimezone}
                onChange={(v) => setDraft((d) => ({ ...d, defaultTimezone: v }))}
                options={tzOptions}
                placeholder="Search timezones… (e.g. Asia/Kolkata)"
              />
            </div>
          </section>

          {/* ── Language defaults ── */}
          <section className="settings-section">
            <div className="settings-section-title">Language defaults</div>
            <div className="field">
              <label>Default languages</label>
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
                options={langOptions.filter((l) => !draft.defaultLanguages.includes(l.id))}
                placeholder="Add a language…"
              />
            </div>
          </section>

          {/* ── Relationship defaults ── */}
          <section className="settings-section">
            <div className="settings-section-title">Relationship defaults</div>

            <div className="field">
              <label>Default relationship nature</label>
              <select
                value={draft.defaultRelationshipNature}
                onChange={(e) => setDraft((d) => ({
                  ...d,
                  defaultRelationshipNature: e.target.value as UserSettings["defaultRelationshipNature"],
                }))}
              >
                <option value="">— none —</option>
                <option value="personal">Personal</option>
                <option value="professional">Professional</option>
                <option value="mixed">Mixed</option>
              </select>
            </div>

            <div className="field">
              <label>Default visibility</label>
              <select
                value={draft.defaultVisibility}
                onChange={(e) => setDraft((d) => ({
                  ...d,
                  defaultVisibility: e.target.value as "private" | "household",
                }))}
              >
                <option value="private">Private</option>
                <option value="household">Household</option>
              </select>
            </div>

            <div className="field">
              <label>Default closeness level</label>
              <div style={{ paddingTop: 8 }}>
                <ClosenessMeter
                  level={draft.defaultClosenessLevel}
                  onChange={(v) => setDraft((d) => ({ ...d, defaultClosenessLevel: v }))}
                />
              </div>
              <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 6 }}>
                Click a dot to set. Click the same dot again to clear.
              </p>
            </div>
          </section>

          {/* ── Save ── */}
          <div className="settings-actions">
            <button className="btn-primary" onClick={handleSave} style={{ minWidth: 100 }}>
              Save settings
            </button>
            {saveStatus === "saved" && (
              <span className="save-status saved">Saved ✓</span>
            )}
          </div>
        </div>
      )}
    </AppLayout>
  );
}
