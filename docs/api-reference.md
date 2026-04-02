# ThirdRaven — Complete API Reference

All endpoints are prefixed with `/api/v1/`. All protected endpoints require `Authorization: Bearer <token>`.

**Response Format:** Paginated endpoints return:
```json
{
  "items": [...],
  "total": 123,
  "skip": 0,
  "limit": 50
}
```

---

## Quick Navigation

### Core Entities
- [Authentication](#authentication) • [Persons](#persons) • [Contacts](#contacts) • [Organizations](#organizations)

### People Knowledge Base
- [Observations](#person-observations) • [Follow-Ups](#person-follow-ups) • [Goals](#person-goals)
- [Life Events](#person-life-events) • [Relationships](#person-relationships)

### Assets & Subscriptions
- [Assets](#assets) • [Asset Extensions](#asset-extensions) • [Subscriptions](#subscriptions)

### Interactions & Tracking
- [Interactions](#interactions) • [Communications](#communications) • [Events](#events)

### Management
- [Loans](#loans) • [Reminders](#reminders) • [Notes](#notes) • [Tasks](#tasks)
- [Documents](#documents) • [Records](#records) • [Renewals](#renewals)

### Admin & Integration
- [Households](#households) • [Import](#import) • [Raven (AI)](#raven-ai)
- [Vocabularies](#vocabularies) • [ISO Reference](#iso-reference) • [Health](#health)

---

## Authentication

### `POST /auth/register`
Register a new user.

**Request:**
```json
{"username": "alice", "email": "alice@example.com", "password": "secret"}
```

**Response — 201:**
```json
{
  "id": "uuid",
  "username": "alice",
  "email": "alice@example.com",
  "created_at": "2026-01-01T00:00:00"
}
```

### `POST /auth/login` (OAuth2)
Obtain JWT access token.

**Request (form-data):** `username`, `password`

**Response — 200:**
```json
{"access_token": "eyJ...", "token_type": "bearer"}
```

---

## Persons

### `POST /persons/`
Create a person. Payload is flat; CRUD splits across core + 5 optional extension tables.

**Fields:**
- **Core** (required: `first_name`): last_name, nickname, email, phone, notes, closeness_level, is_placeholder, is_bot, relationship_nature, tags (slugs)
- **Profile**: middle_name, prefix (slug), date_of_birth, gender (slug), nationality (alpha2), languages (ISO-639-1 list)
- **Professional**: occupation (slug), company, job_title, linkedin_url, phone_secondary
- **Social**: twitter_handle, instagram_handle, website_url
- **Location**: address_home, address_work, city, country (alpha2), timezone (IANA)
- **Context**: how_we_met, first_met_on, contact_frequency_days, last_contacted_on, preferred_contact (slug)

**Response — 201:** `PersonSlim`

### `GET /persons/`
List persons. Query: skip, limit, is_placeholder, is_bot, relationship_nature

**Response — 200:** `Paginated[PersonSlim]`

### `GET /persons/relationship-health` ⚠️
**Must be declared BEFORE** `GET /persons/{person_id}` to avoid UUID parsing collision.

Returns contact cadence health.

**Response — 200:** `list[{person_id, first_name, last_name, last_contacted_on, contact_frequency_days, days_since_contact, health_status}]`

### `GET /persons/schema`
Returns vocabulary options for all person fields (prefixes, genders, occupations, tags, relationship_types, contact methods, etc.).

**Response — 200:** `PersonFieldOptions`

### `GET /persons/{person_id}`
Fetch a single person with optional extensions.

**Query:** `include` = `profile,professional,social,location,context` or `all`

**Response — 200:** `PersonWithRelationships` (includes all requested sections + relationships array)

### `PATCH /persons/{person_id}`
Partial update (all fields optional).

**Response — 200:** `PersonSlim`

### `DELETE /persons/{person_id}`
Soft-delete. Returns 403 if deleting your own user person.

**Response — 204**

### `GET /persons/{person_id}/context-package`
Full AI context package for the person.

**Response — 200:** `{person, observations, follow_ups, goals, interactions, organizations, relationship_health}`

---

## Person Relationships

### `POST /persons/{person_id}/relationships`
Create directed relationship.

**Body:** `{to_person_id: uuid, label: "friend"}`

**Response — 201:** `{id, from_person_id, to_person_id, label_term_id, created_at}`

### `GET /persons/{person_id}/relationships`
List relationships. Query: skip, limit

**Response — 200:** `Paginated[RelationshipPublic]`

### `GET /relationships/{rel_id}`
**Response — 200:** `RelationshipPublic`

### `PATCH /relationships/{rel_id}`
**Body:** `{label: "colleague"}`

### `DELETE /relationships/{rel_id}`

---

## Person Addresses

### `POST /persons/{person_id}/addresses/`
**Body:** `{line1, line2, city, state, postal_code, country (alpha2), address_type, is_primary}`

**Response — 201:** `AddressPublic`

### `PATCH /persons/{person_id}/addresses/{address_id}`
### `DELETE /persons/{person_id}/addresses/{address_id}`

---

## Person Channels

Typed contact methods (email, phone, WhatsApp, Telegram, Discord, Twitter, Instagram, LinkedIn, GitHub, Website, Signal, Slack, etc.).

### `POST /persons/{person_id}/channels/`
**Body:** `{channel_type, value, label, is_primary}`

**Response — 201:** `ChannelPublic`

### `PATCH /persons/{person_id}/channels/{channel_id}`
### `DELETE /persons/{person_id}/channels/{channel_id}`

---

## Person Observations

Episodic notes about a person.

### `POST /persons/{person_id}/observations/`
**Body:** `{body (required), observed_on, source, context (personal|professional|mixed), is_sensitive, tags (slugs)}`

**Response — 201:** `{id, person_id, owner_id, body, observed_on, source, context, is_sensitive, tags, created_at, updated_at}`

### `GET /persons/{person_id}/observations/`
Query: skip, limit, include_sensitive (default true), context

**Response — 200:** `Paginated[ObservationPublic]`

### `GET /persons/{person_id}/observations/{obs_id}`
### `PATCH /persons/{person_id}/observations/{obs_id}`
### `DELETE /persons/{person_id}/observations/{obs_id}`

---

## Person Follow-Ups

### `POST /persons/{person_id}/follow-ups/`
**Body:** `{body (required), due_on, interaction_id}`

**Response — 201:** `{id, person_id, owner_id, body, due_on, interaction_id, cleared_at, created_at, updated_at}`

### `GET /persons/{person_id}/follow-ups/`
Query: skip, limit, pending_only (default false)

### `GET /persons/{person_id}/follow-ups/{followup_id}`

### `PATCH /persons/{person_id}/follow-ups/{followup_id}`
**Body:** `{body, due_on, interaction_id, cleared (bool)}`

### `DELETE /persons/{person_id}/follow-ups/{followup_id}`

---

## Person Goals

Four types: aspiration, fear, current-focus, learning.

### `POST /persons/{person_id}/goals/`
**Body:** `{goal_type, body (required), target_date}`

### `GET /persons/{person_id}/goals/`
Query: skip, limit, active_only (default false)

### `GET /persons/{person_id}/goals/{goal_id}`

### `PATCH /persons/{person_id}/goals/{goal_id}`
**Body:** `{goal_type, body, target_date, achieved (bool)}`

### `DELETE /persons/{person_id}/goals/{goal_id}`

---

## Person Life Events

### Standalone

#### `POST /life-events/`
**Body:** `{title (required), event_type (slug), description, occurred_on, emotion (slug), participants [{person_id, role}]}`

#### `GET /life-events/`, `GET /life-events/{event_id}`, `PATCH /life-events/{event_id}`, `DELETE /life-events/{event_id}`

#### `POST /life-events/{event_id}/participants/`
#### `DELETE /life-events/{event_id}/participants/{person_id}`

### Person-Scoped

#### `POST /persons/{person_id}/life-events/`
Auto-adds person as primary participant.

#### `GET /persons/{person_id}/life-events/`

---

## Person Significant Dates

### `POST /persons/{person_id}/significant-dates/`
**Body:** `{date_type (slug), date (required), label, recurs_annually}`

### `GET /persons/{person_id}/significant-dates/`

### `GET /persons/{person_id}/significant-dates/{date_id}`

### `PATCH /persons/{person_id}/significant-dates/{date_id}`

### `DELETE /persons/{person_id}/significant-dates/{date_id}`

---

## Person Organizations

### `POST /persons/{person_id}/organizations/`
**Body:** `{org_id (required), role, started_on, ended_on, is_current, notes}`

### `GET /persons/{person_id}/organizations/`

### `PATCH /persons/{person_id}/organizations/{link_id}`

### `DELETE /persons/{person_id}/organizations/{link_id}`

---

## Person Loans (scoped)

### `GET /persons/{person_id}/loans/`
List person's loans. Query: skip, limit

---

## Person Reminders (scoped)

### `GET /persons/{person_id}/reminders/`
Query: skip, limit

---

## Contacts

Lightweight records (no AI/KB fields).

### `POST /contacts/`
**Body:** `{first_name (required), last_name, email, phone, notes, tags}`

### `GET /contacts/`, `GET /contacts/{contact_id}`, `PATCH /contacts/{contact_id}`, `DELETE /contacts/{contact_id}`

### `POST /contacts/{contact_id}/relationships`
**Body:** `{to_contact_id, label}`

---

## Organizations

### `POST /organizations/`
**Body:** `{name (required), org_type (slug), industry (slug), website, description, headquarters, founded_year, notes}`

### `GET /organizations/`, `GET /organizations/{org_id}`, `PATCH /organizations/{org_id}`, `DELETE /organizations/{org_id}`

---

## Events

Social/group events with person participants.

### `POST /events/`
**Body:** `{title (required), event_type (slug), description, occurred_on, location, notes}`

### `GET /events/`, `GET /events/{event_id}`, `PATCH /events/{event_id}`, `DELETE /events/{event_id}`

### `POST /events/{event_id}/persons/`
**Body:** `{person_id (required), role}`

### `GET /events/{event_id}/persons/`

### `DELETE /events/{event_id}/persons/{event_person_id}`

---

## Assets

### `POST /assets/`
**Body:** `{name (required), category (slug, required), status (slug, default "active"), description, serial_number, vendor, purchase_date, purchase_price, current_value, tags, notes}`

### `GET /assets/`
Query: skip, limit, category, status

### `GET /assets/{asset_id}`, `PATCH /assets/{asset_id}`, `DELETE /assets/{asset_id}`

---

## Asset Extensions

Each asset can have one extension: Physical, Document, Financial, or Digital (upsert pattern).

### Physical: `/assets/{asset_id}/physical/`
**Body:** `{condition (slug), weight_kg, color, model_number, dimensions, location}`

### Document: `/assets/{asset_id}/document/`
**Body:** `{doc_type (slug), issuer, issue_date, expiry_date, document_number, file_path}`

### Financial: `/assets/{asset_id}/financial/`
**Body:** `{account_type (slug), institution, account_number_last4, currency (ISO-4217), current_balance, interest_rate, maturity_date}`

### Digital: `/assets/{asset_id}/digital/`
**Body:** `{platform, url, login_email, license_key, expires_on, seats}`

### Lifecycle Events

#### `GET /assets/{asset_id}/events/`
#### `POST /assets/{asset_id}/events/`
**Body:** `{event_type, occurred_on (required), description, cost, vendor, notes}`

#### `DELETE /assets/{asset_id}/events/{event_id}`

---

## Subscriptions

### `POST /subscriptions/`
**Body:** `{name (required), provider, category (slug), status (active|paused|cancelled), cost (required), currency (default INR), payment_mode (manual|auto_debit), billing_cycle (monthly|annual|weekly|custom), billing_cycle_days, started_on, next_billing_date, trial_ends_on, auto_renews, url, notes, asset_id, tags}`

### `GET /subscriptions/summary`
**Response:** `{total_monthly_cost, total_annual_cost, active_count, paused_count, cancelled_count}`

### `GET /subscriptions/`
Query: skip, limit, status, category, billing_cycle

### `GET /subscriptions/{subscription_id}`, `PATCH /subscriptions/{subscription_id}`, `DELETE /subscriptions/{subscription_id}`

### Payments

#### `POST /subscriptions/{subscription_id}/payments`
**Body:** `{amount (required), currency, paid_amount, paid_currency, exchange_rate, payment_mode, billing_date (required), due_date, paid_on, status, notes}`

#### `GET /subscriptions/{subscription_id}/payments`
Query: skip, limit

#### `PATCH /subscriptions/{subscription_id}/payments/{payment_id}`

#### `DELETE /subscriptions/{subscription_id}/payments/{payment_id}`

---

## Interactions

Touchpoints with a person (call, meeting, email, etc.).

### `POST /persons/{person_id}/interactions/`
**Body:** `{title (required), interaction_type_id, term_id, occurred_on, notes, metadata_}`

### `GET /persons/{person_id}/interactions/`
Query: skip, limit, type_slug

### `GET /persons/{person_id}/interactions/{interaction_id}`, `PATCH /persons/{person_id}/interactions/{interaction_id}`, `DELETE /persons/{person_id}/interactions/{interaction_id}`

---

## Loans

### `POST /loans/`
**Body:** `{person_id (required), direction (lent|borrowed), loan_type (money|item), description (required), amount, currency, item_name, loaned_on, due_on, notes}`

### `GET /loans/`
Query: skip, limit, status_filter, direction

### `GET /loans/{loan_id}`, `PATCH /loans/{loan_id}`, `DELETE /loans/{loan_id}`

---

## Reminders

### `POST /reminders/`
**Body:** `{title (required), body, due_at (required), remind_at, recurrence (daily|weekly|monthly|annual), person_id, asset_id, subscription_id}`

### `GET /reminders/`
Query: skip, limit, is_done

### `GET /reminders/{reminder_id}`, `PATCH /reminders/{reminder_id}`, `DELETE /reminders/{reminder_id}`

---

## Notes

Freeform notes linked to person, asset, subscription, or event.

### `POST /notes/`
**Body:** `{title (required), body, pinned, person_id, asset_id, subscription_id, event_id, tags}`

### `GET /notes/statistics`
**Response:** `{total, pinned, by_attachment}`

### `GET /notes/`
Query: skip, limit, q, pinned, person_id, asset_id, subscription_id, event_id

### `GET /notes/{note_id}`, `PATCH /notes/{note_id}`, `DELETE /notes/{note_id}`

---

## Tasks

### `POST /tasks/`
**Body:** `{title (required), description, status (todo|in_progress|done), priority (low|normal|high|urgent), due_date, person_id, asset_id, subscription_id, event_id, tags}`

### `GET /tasks/summary`
**Response:** `{total, by_status, overdue, due_today, by_priority}`

### `GET /tasks/`
Query: skip, limit, status, priority, person_id, asset_id, subscription_id, event_id, due_before, due_after, overdue

### `GET /tasks/{task_id}`, `PATCH /tasks/{task_id}`, `DELETE /tasks/{task_id}`

---

## Documents

File-reference records (external storage).

### `POST /documents/`
**Body:** `{entity_type (asset|tracked_record|subscription|person|general), entity_id, doc_type (slug, required), title (required), file_path, file_name, file_size, mime_type, issued_on, expires_on, notes}`

### `GET /documents/`
Query: skip, limit, entity_type, entity_id

### `GET /documents/{doc_id}`, `PATCH /documents/{doc_id}`, `DELETE /documents/{doc_id}`

---

## Communications

Raw messages (emails, chat, SMS, etc.) optionally matched to person and generating interactions.

### `POST /communications/ingest`
**Flexible schema.** Unknown fields → raw_payload.

**Body:** `{channel (required), direction (default inbound), sender, recipients, source_app, external_id, thread_id, subject, body, communicated_at, extra, ...}`

### `POST /communications/`
**Structured.** All fields explicit.

**Body:** `{channel (required), direction, sender_identifier, recipient_identifiers, source_app, external_id, thread_id, subject, body, communicated_at, raw_payload, context (personal|professional|mixed), is_bot}`

### `GET /communications/`
Query: skip, limit, channel, status, person_id, is_bot, context

### `GET /communications/{comm_id}`, `PATCH /communications/{comm_id}`, `DELETE /communications/{comm_id}`

### `POST /communications/{comm_id}/match`
Re-attempt person matching. If person_id set, creates Interaction.

### `POST /communications/{comm_id}/extract-actions`
**501 Not Implemented** (Phase 2: AI extraction of follow-ups/observations)

---

## Records

Compliance/certificate items with expiry dates (insurance, warranties, passports, etc.).

### `POST /records/`
**Body:** `{title (required), record_type (slug), entity_type, entity_id, asset_id, person_id, issued_on, expires_on, issuer, reference_number, notes}`

### `GET /records/`
Query: skip, limit, record_type, asset_id, person_id, expires_before

### `GET /records/{record_id}`, `PATCH /records/{record_id}`, `DELETE /records/{record_id}`

---

## Renewals

### `GET /renewals/upcoming`
Aggregates upcoming renewals across subscriptions, records, and digital assets.

**Query:** days (default 30)

**Response:** `list[{entity_type, entity_id, name, renews_on, days_until, cost, currency}]`

---

## Households

Shared visibility across users.

### `POST /households/`
**Body:** `{name (required)}`

### `GET /households/me`
Get current user's household.

### `POST /households/{household_id}/members`
**Body:** `{username}` (owner-only)

### `DELETE /households/{household_id}/members/{user_id}` (owner-only)

### `DELETE /households/me/leave`

---

## Import

Background ETL with optional AI disambiguation.

### `POST /import/jobs` (multipart/form-data)
**Fields:** file, data_type (e.g., "persons"), source_format (default "csv")

**Response — 201:** `{id, data_type, status, total_rows, processed_rows, pending_questions, created_at, completed_at}`

### `GET /import/jobs`
Query: skip, limit

**Response:** `list[ImportJobPublic]`

### `GET /import/jobs/{job_id}`
**Response:** `{...ImportJobPublic, rows: [{id, job_id, row_index, status, entity_id, error}]}`

---

## Raven (AI)

### `GET /raven/logs`
Query: skip, limit, operation

**Response:** `list[{id, owner_id, operation, input_summary, decision, confidence, created_at}]`

### `GET /raven/questions`
Query: skip, limit, status_filter (pending|answered|resolved)

**Response:** `list[{id, owner_id, job_id, question, status, answer, answered_at, created_at}]`

### `GET /raven/questions/{question_id}`

### `POST /raven/questions/{question_id}/answer`
**Body:** `{answer (required)}`

**Response — 202:** `{detail: "Answer accepted, processing in background."}`

Returns 409 if not pending.

---

## Vocabularies

### `GET /vocabularies/`
Query: skip, limit

### `POST /vocabularies/`
**Body:** `{name (required), machine_name (required, unique), description, is_hierarchical, allows_new_terms, is_locked, source_type, external_provider}`

### `GET /vocabularies/{machine_name}`, `PATCH /vocabularies/{machine_name}`, `DELETE /vocabularies/{machine_name}`

Returns 409 if locked.

### `GET /vocabularies/{machine_name}/terms`
Query: parent, search, skip, limit

### `POST /vocabularies/{machine_name}/terms`
**Body:** `{name (required), slug (required, unique), description, parent_id, weight, external_id, metadata_}`

### `GET /vocabularies/{machine_name}/terms/{slug}`, `PATCH /vocabularies/{machine_name}/terms/{slug}`, `DELETE /vocabularies/{machine_name}/terms/{slug}`

---

## ISO Reference

Read-only. No auth required.

### `GET /iso/countries/`
Query: search, skip, limit

### `GET /iso/countries/{alpha2}`
**Response:** `{id, name, alpha2, alpha3, numeric, calling_code, region, subregion, flag_emoji, is_active}`

### `GET /iso/languages/`
Query: search, skip, limit

### `GET /iso/languages/{iso_639_1}`
**Response:** `{id, name, native_name, iso_639_1, iso_639_2, is_active}`

### `GET /iso/timezones/`
Query: country (alpha2), skip, limit

### `GET /iso/timezones/{timezone_id}`
**Response:** `{id, name, utc_offset, utc_offset_dst, country_id, is_active}`

---

## Health

### `GET /health`
No auth required.

**Response — 200:** `{status: "ok"}`

---

## Common Error Responses

| Status | Meaning |
|---|---|
| 401 | Missing or invalid JWT |
| 403 | Action forbidden (e.g., deleting your own user person) |
| 404 | Resource not found or belongs to another user |
| 409 | Conflict (e.g., non-pending question, locked vocabulary) |
| 422 | Validation error (invalid slug, missing field, unsupported type) |
| 501 | Feature not yet implemented |
