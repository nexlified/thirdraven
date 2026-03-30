import { api } from "./client";

export interface CountryPublic {
  id: string;
  name: string;
  alpha2: string;
  alpha3: string;
  calling_code: string | null;
  flag_emoji: string | null;
}

export interface LanguagePublic {
  id: string;
  name: string;
  native_name: string | null;
  iso_639_1: string;
  iso_639_2: string | null;
}

export interface TimezonePublic {
  id: string;
  name: string;
  utc_offset: string;
  utc_offset_dst: string | null;
}

export function listCountries(search?: string): Promise<CountryPublic[]> {
  const qs = search ? `?search=${encodeURIComponent(search)}&limit=300` : "?limit=300";
  return api.get<CountryPublic[]>(`/iso/countries/${qs}`);
}

export function listLanguages(search?: string): Promise<LanguagePublic[]> {
  const qs = search ? `?search=${encodeURIComponent(search)}&limit=200` : "?limit=200";
  return api.get<LanguagePublic[]>(`/iso/languages/${qs}`);
}

export function listTimezones(countryAlpha2?: string): Promise<TimezonePublic[]> {
  const qs = countryAlpha2 ? `?country=${countryAlpha2}&limit=200` : "?limit=600";
  return api.get<TimezonePublic[]>(`/iso/timezones/${qs}`);
}
