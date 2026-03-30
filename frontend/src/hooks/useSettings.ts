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

export function useSettings(): [UserSettings, (s: UserSettings) => void] {
  return [readSettings(), writeSettings];
}
