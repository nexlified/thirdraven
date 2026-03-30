import { api } from "./client";

// ── Shared ────────────────────────────────────────────────────────────────────

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

// ── Channels & Addresses ──────────────────────────────────────────────────────

export interface ChannelPublic {
  id: string;
  type: string;
  value: string;
  label: string | null;
  is_primary: boolean;
}

export interface ChannelCreate {
  type: string;
  value: string;
  label?: string;
  is_primary?: boolean;
}

export interface ChannelUpdate {
  type?: string;
  value?: string;
  label?: string;
  is_primary?: boolean;
}

export interface AddressPublic {
  id: string;
  type: string;
  street: string | null;
  city: string | null;
  postal_code: string | null;
  country: { id: string; name: string; alpha2: string } | null;
  lat: number | null;
  lng: number | null;
  is_primary: boolean;
}

export interface AddressCreate {
  type?: string;
  street?: string;
  city?: string;
  postal_code?: string;
  country?: string;
  lat?: number;
  lng?: number;
  is_primary?: boolean;
}

// ── Extension sections ────────────────────────────────────────────────────────

export interface PersonProfileSection {
  middle_name: string | null;
  prefix: TermSlim | null;
  date_of_birth: string | null;
  gender: TermSlim | null;
  nationality: { id: string; name: string; alpha2: string } | null;
  languages: { id: string; name: string; iso_639_1: string }[];
}

export interface PersonProfessionalSection {
  occupation: TermSlim | null;
  company: string | null;
  job_title: string | null;
}

export interface PersonLocationSection {
  timezone: { id: string; name: string; utc_offset: string; utc_offset_dst: string | null } | null;
  addresses: AddressPublic[];
}

export interface PersonContextSection {
  how_we_met: string | null;
  first_met_on: string | null;
  last_contacted_on: string | null;
  contact_frequency_days: number | null;
  preferred_contact: TermSlim | null;
  relationship_nature: string | null;
}

// ── Relationships ─────────────────────────────────────────────────────────────

export interface RelatedPersonRef {
  id: string;
  first_name: string;
  last_name: string | null;
  nickname: string | null;
}

export interface RelationshipPublic {
  id: string;
  person: RelatedPersonRef;
  related_person: RelatedPersonRef;
  label: TermSlim;
  inverse_id: string | null;
  created_at: string;
}

// ── Core person types ─────────────────────────────────────────────────────────

export interface PersonSlim {
  id: string;
  owner_id: string;
  first_name: string;
  last_name: string | null;
  nickname: string | null;
  email: string | null;
  phone: string | null;
  notes: string | null;
  tags: TermSlim[];
  closeness_level: number | null;
  visibility: string;
  is_placeholder: boolean;
  is_bot: boolean;
  created_at: string;
  updated_at: string;
}

export interface PersonExtended extends PersonSlim {
  profile?: PersonProfileSection | null;
  professional?: PersonProfessionalSection | null;
  location?: PersonLocationSection | null;
  context?: PersonContextSection | null;
  channels?: ChannelPublic[] | null;
  relationships: RelationshipPublic[];
}

// ── Schema / options ──────────────────────────────────────────────────────────

export interface PersonFieldOptions {
  prefixes: TermSlim[];
  genders: TermSlim[];
  occupations: TermSlim[];
  tags: TermSlim[];
  relationship_types: TermSlim[];
  preferred_contact: TermSlim[];
  address_types: string[];
  channel_types: string[];
}

// ── Payloads ──────────────────────────────────────────────────────────────────

export interface PersonCreatePayload {
  first_name: string;
  last_name?: string | null;
  nickname?: string | null;
  notes?: string | null;
  closeness_level?: number | null;
  channels?: ChannelCreate[];
  tags?: string[];
  preferred_contact?: string | null;
  middle_name?: string | null;
  prefix?: string | null;
  date_of_birth?: string | null;
  gender?: string | null;
  nationality?: string | null;
  languages?: string[];
  occupation?: string | null;
  company?: string | null;
  job_title?: string | null;
  timezone?: string | null;
  how_we_met?: string | null;
  first_met_on?: string | null;
  last_contacted_on?: string | null;
  contact_frequency_days?: number | null;
  relationship_nature?: string | null;
  visibility?: string;
  is_placeholder?: boolean;
  is_bot?: boolean;
}

export type PersonUpdatePayload = Partial<PersonCreatePayload>;

// ── API functions ─────────────────────────────────────────────────────────────

export function listPersons(params: {
  skip?: number;
  limit?: number;
  is_placeholder?: boolean;
  is_bot?: boolean;
  relationship_nature?: string;
} = {}): Promise<Paginated<PersonSlim>> {
  const q = new URLSearchParams();
  if (params.skip !== undefined) q.set("skip", String(params.skip));
  if (params.limit !== undefined) q.set("limit", String(params.limit));
  if (params.is_placeholder !== undefined) q.set("is_placeholder", String(params.is_placeholder));
  if (params.is_bot !== undefined) q.set("is_bot", String(params.is_bot));
  if (params.relationship_nature) q.set("relationship_nature", params.relationship_nature);
  const qs = q.toString();
  return api.get<Paginated<PersonSlim>>(`/persons${qs ? `?${qs}` : ""}`);
}

export function createPerson(data: PersonCreatePayload): Promise<PersonSlim> {
  return api.post<PersonSlim>("/persons", data);
}

export function getPerson(id: string, include: string[] = []): Promise<PersonExtended> {
  const qs = include.length ? `?include=${include.join(",")}` : "";
  return api.get<PersonExtended>(`/persons/${id}${qs}`);
}

export function updatePerson(id: string, data: PersonUpdatePayload): Promise<PersonSlim> {
  return api.patch<PersonSlim>(`/persons/${id}`, data);
}

export function deletePerson(id: string): Promise<void> {
  return api.delete(`/persons/${id}`);
}

export function getPersonSchema(): Promise<PersonFieldOptions> {
  return api.get<PersonFieldOptions>("/persons/schema");
}

// ── Channels ──────────────────────────────────────────────────────────────────

export function addChannel(personId: string, data: ChannelCreate): Promise<ChannelPublic> {
  return api.post<ChannelPublic>(`/persons/${personId}/channels`, data);
}

export function updateChannel(personId: string, channelId: string, data: ChannelUpdate): Promise<ChannelPublic> {
  return api.patch<ChannelPublic>(`/persons/${personId}/channels/${channelId}`, data);
}

export function deleteChannel(personId: string, channelId: string): Promise<void> {
  return api.delete(`/persons/${personId}/channels/${channelId}`);
}

// ── Addresses ─────────────────────────────────────────────────────────────────

export function addAddress(personId: string, data: AddressCreate): Promise<AddressPublic> {
  return api.post<AddressPublic>(`/persons/${personId}/addresses`, data);
}

export function updateAddress(personId: string, addressId: string, data: AddressCreate): Promise<AddressPublic> {
  return api.patch<AddressPublic>(`/persons/${personId}/addresses/${addressId}`, data);
}

export function deleteAddress(personId: string, addressId: string): Promise<void> {
  return api.delete(`/persons/${personId}/addresses/${addressId}`);
}

// ── Relationships ─────────────────────────────────────────────────────────────

export interface RelationshipCreatePayload {
  to_person_id: string;
  label: string;  // slug from "relationship-types" vocabulary
}

export interface RelationshipUpdatePayload {
  label: string;  // slug from "relationship-types" vocabulary
}

export function createRelationship(personId: string, data: RelationshipCreatePayload): Promise<RelationshipPublic> {
  return api.post<RelationshipPublic>(`/persons/${personId}/relationships`, data);
}

export function updateRelationship(relId: string, data: RelationshipUpdatePayload): Promise<RelationshipPublic> {
  return api.patch<RelationshipPublic>(`/relationships/${relId}`, data);
}

export function deleteRelationship(relId: string): Promise<void> {
  return api.delete(`/relationships/${relId}`);
}
