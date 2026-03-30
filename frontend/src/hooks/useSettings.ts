import { useCallback, useEffect, useState } from "react";
import { getMyPreferences, updateMyPreferences, type UserPreferencesPublic } from "../api/auth";

const STORAGE_KEY = "thirdraven_settings";

export interface UserSettings {
  defaultCountry: string;
  defaultTimezone: string;
  defaultRelationshipNature: "" | "personal" | "professional" | "mixed";
  defaultVisibility: "private" | "household";
  defaultClosenessLevel: number | null;
  defaultLanguages: string[];
}

const DEFAULTS: UserSettings = {
  defaultCountry: "",
  defaultTimezone: "",
  defaultRelationshipNature: "",
  defaultVisibility: "private",
  defaultClosenessLevel: null,
  defaultLanguages: [],
};

export function readSettings(): UserSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...DEFAULTS };
    return { ...DEFAULTS, ...JSON.parse(raw) };
  } catch {
    return { ...DEFAULTS };
  }
}

export function writeSettings(s: UserSettings): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
}

function fromApi(prefs: UserPreferencesPublic): UserSettings {
  return {
    defaultCountry: prefs.default_country,
    defaultTimezone: prefs.default_timezone,
    defaultRelationshipNature: prefs.default_relationship_nature,
    defaultVisibility: prefs.default_visibility,
    defaultClosenessLevel: prefs.default_closeness_level,
    defaultLanguages: prefs.default_languages,
  };
}

function toApi(settings: UserSettings): UserPreferencesPublic {
  return {
    default_country: settings.defaultCountry,
    default_timezone: settings.defaultTimezone,
    default_relationship_nature: settings.defaultRelationshipNature,
    default_visibility: settings.defaultVisibility,
    default_closeness_level: settings.defaultClosenessLevel,
    default_languages: settings.defaultLanguages,
  };
}

export function useSettings(): [UserSettings, (s: UserSettings) => void] {
  const [settings, setSettings] = useState<UserSettings>(readSettings());

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) return;

    getMyPreferences()
      .then((remote) => {
        const merged = fromApi(remote);
        setSettings(merged);
        writeSettings(merged);
      })
      .catch(() => {});
  }, []);

  const persist = useCallback((next: UserSettings) => {
    setSettings(next);
    writeSettings(next);
    const token = localStorage.getItem("access_token");
    if (!token) return;
    void updateMyPreferences(toApi(next)).catch(() => {});
  }, []);

  return [settings, persist];
}
