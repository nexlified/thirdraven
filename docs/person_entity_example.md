# Person — Field Guide

A Person is the central entity in ThirdRaven. Every contact, relationship, communication, and observation links back to one.

Fields are grouped into a **core** set (always returned) and **sections** that load on demand. Use `?include=profile,location` or `?include=all` to load extra sections.

---

## Core fields

Always present in every Person response.

| Field | Example value | What it means |
|---|---|---|
| `id` | `01960000-…0001` | Unique identifier |
| `owner_id` | `01960000-…0002` | The user account this person belongs to |
| `first_name` | `Alexandra` | First name (required) |
| `last_name` | `Reinholt` | Last name |
| `nickname` | `Alex` | Informal name or alias |
| `email` | `alex@example.com` | Primary email — derived from channels (read-only shortcut) |
| `phone` | `+49 151 12345678` | Primary mobile/phone — derived from channels (read-only shortcut) |
| `closeness_level` | `4` | How close you are: 1 (distant) → 5 (very close) |
| `notes` | `"Met at FinTech Forum…"` | Free-text notes |
| `tags` | `[{id, name, slug}]` | Labels from your vocabulary |
| `visibility` | `private` | `private` = only you · `household` = shared with household |
| `household_id` | `null` | ID of the household this person is shared with |
| `is_placeholder` | `false` | Auto-created from an unknown sender; not yet a real contact |
| `is_bot` | `false` | Automated sender (newsletter, CI bot, notification service) |
| `created_at` | `2025-06-15T09:30:00Z` | When this record was created |
| `updated_at` | `2026-03-10T14:22:11Z` | When this record was last modified |

> **Note on `email` and `phone`**: these are convenience shortcuts derived from the person's channels (`is_primary=true` entries for `email` and `mobile`/`phone` types). To manage all contact channels use `POST/PATCH/DELETE /persons/{id}/channels/` or `?include=channels`.

### Tags

Each tag in the response:

| Sub-field | Example | What it means |
|---|---|---|
| `id` | `01960000-…0010` | Internal ID |
| `name` | `Investor` | Display name |
| `slug` | `investor` | Value to pass when creating/updating |

---

## Profile section — `?include=profile`

Personal identity details.

| Field | Example value | What it means |
|---|---|---|
| `middle_name` | `Marie` | Middle name |
| `prefix` | `{name: "Dr.", slug: "dr"}` | Name prefix from your vocabulary (`name-prefixes`) |
| `date_of_birth` | `1988-04-23` | Date of birth (YYYY-MM-DD) |
| `gender` | `{name: "Female", slug: "female"}` | Gender from your vocabulary (`genders`) |
| `nationality` | `{name: "Germany", alpha2: "DE"}` | Country of nationality — pass ISO alpha-2 code to set |
| `languages` | `[{name: "German", iso_639_1: "de"}, …]` | Languages spoken — pass ISO 639-1 codes to set |

---

## Professional section — `?include=professional`

Work and career details.

| Field | Example value | What it means |
|---|---|---|
| `occupation` | `{name: "Venture Capitalist", slug: "vc"}` | Job category from your vocabulary (`occupations`) |
| `company` | `Reinholt Ventures GmbH` | Employer or company name |
| `job_title` | `Managing Partner` | Job title |

> LinkedIn URL, secondary phone, and social handles are now stored as **channels** (see below) — not in this section.

---

## Location section — `?include=location`

Timezone and any number of addresses.

### Timezone

| Field | Example value | What it means |
|---|---|---|
| `timezone` | `{name: "Europe/Berlin", utc_offset: "+01:00"}` | IANA timezone — used for scheduling and time display |

### Addresses

A person can have any number of addresses. Each entry:

| Field | Example value | What it means |
|---|---|---|
| `id` | `01960000-…0030` | Unique ID of this address |
| `type` | `home` | `home` · `work` · `other` (free string) |
| `street` | `Kastanienallee 22` | Street address |
| `city` | `Berlin` | City |
| `postal_code` | `10435` | Postal / ZIP code |
| `country` | `{name: "Germany", alpha2: "DE"}` | Country — pass ISO alpha-2 code to set |
| `lat` | `52.5382` | Latitude (set automatically if geocoded) |
| `lng` | `13.4034` | Longitude |
| `is_primary` | `true` | The main address for this type |

**Managing addresses individually:**

| Endpoint | What it does |
|---|---|
| `POST /persons/{id}/addresses/` | Add an address |
| `PATCH /persons/{id}/addresses/{addr_id}` | Update an address |
| `DELETE /persons/{id}/addresses/{addr_id}` | Remove an address |

**Replace all at once** — pass `"addresses": [...]` in `POST /persons/` or `PATCH /persons/{id}`. Omitting the field leaves existing addresses intact; passing an empty list clears them all.

---

## Context section — `?include=context`

How and when you know this person, and how often to stay in touch.

| Field | Example value | What it means |
|---|---|---|
| `how_we_met` | `"Introduced by Tobias at FinTech Forum 2023"` | Origin story of the relationship |
| `first_met_on` | `2023-09-14` | Date you first met (YYYY-MM-DD) |
| `last_contacted_on` | `2026-02-28` | Date of most recent contact — updated automatically when a communication arrives |
| `contact_frequency_days` | `30` | How often you intend to reach out, in days (30 = monthly) |
| `preferred_contact` | `{name: "Email", slug: "email"}` | Their preferred channel from your vocabulary (`preferred-contact`) |
| `relationship_nature` | `professional` | Overall nature: `personal` · `professional` · `mixed` · *(blank = unclassified)* |

---

## Physical section — `?include=physical`

Physical characteristics — useful for remembering people after a long time.

| Field | Example value | What it means |
|---|---|---|
| `height_cm` | `172.0` | Height in centimetres |
| `eye_color` | `{name: "Green", slug: "green"}` | Eye colour from your vocabulary (`eye-colors`) |
| `hair_color` | `{name: "Brown", slug: "brown"}` | Hair colour from your vocabulary (`hair-colors`) |
| `blood_type` | `A+` | Blood type (free text) |

---

## Personality section — `?include=personality`

Preferences and personality notes — useful context for RavenPair.

| Field | Example value | What it means |
|---|---|---|
| `interests` | `Hiking, classical piano, urban farming` | Hobbies and topics they enjoy |
| `food_preferences` | `Vegetarian, loves Ethiopian cuisine` | Food likes |
| `dietary_restrictions` | `No shellfish (allergy)` | Restrictions or allergies |
| `personality_notes` | `"Very direct. Prefers async updates."` | Free-text personality observations |
| `communication_style` | `{name: "Direct", slug: "direct"}` | How they prefer to communicate (`communication-styles`) |

---

## Channels section — `?include=channels`

A person can have **any number** of contact channels — email addresses, phone numbers, social handles, messaging apps, websites, and more. Each channel has a free `type` string so you're not limited to a fixed list.

| Field | Example value | What it means |
|---|---|---|
| `id` | `01960000-…0020` | Unique ID of this channel |
| `type` | `email` | The channel type — see common values below |
| `value` | `alex@example.com` | The actual address, number, or handle |
| `label` | `work` | Optional label: `work` · `personal` · *(blank)* |
| `is_primary` | `true` | Primary entry for this type — drives the `email`/`phone` shortcuts in core |

### Common channel types

| Type | Example value |
|---|---|
| `email` | `alex@example.com` |
| `mobile` | `+49 151 12345678` |
| `phone` | `+49 30 9876543` (landline / work) |
| `whatsapp` | `+49 151 12345678` |
| `telegram` | `@alex_r` |
| `discord` | `alexreinholt` |
| `twitter` | `@alexreinholt` |
| `instagram` | `alex.reinholt` |
| `github` | `alexreinholt` |
| `linkedin` | `https://linkedin.com/in/alexreinholt` |
| `facebook` | `https://facebook.com/alexreinholt` |
| `website` | `https://reinholtventures.de` |
| `signal` | `+49 151 12345678` |
| `slack` | `@alex` |

Any other string is valid — the list above is a convention, not a constraint.

The `email` and `phone` core fields are derived from `is_primary=true` channels with `type == "email"` and `type in ("mobile", "phone")`.

**Managing channels individually:**

| Endpoint | What it does |
|---|---|
| `POST /persons/{id}/channels/` | Add a channel |
| `PATCH /persons/{id}/channels/{channel_id}` | Update a channel |
| `DELETE /persons/{id}/channels/{channel_id}` | Remove a channel |

**Replace all at once** — pass `"channels": [...]` in `POST /persons/` or `PATCH /persons/{id}`. Omitting the field leaves existing channels intact; passing an empty list clears them all.

---

## Relationships

Always included when fetching a single person (`GET /persons/{id}`). Each entry represents one directional link.

```
relationship
├── id                 Unique ID of this relationship record
├── person             The "from" side (usually this person)
│   ├── id
│   ├── first_name     Alexandra
│   ├── last_name      Reinholt
│   └── nickname       Alex
├── related_person     The "to" side
│   ├── id
│   ├── first_name     Tobias
│   ├── last_name      Meier
│   └── nickname       —
├── label              Mentor  (from relationship-types vocabulary)
├── inverse_id         ID of the paired reverse record
└── created_at         2025-10-01T11:00:00Z
```

Relationships are always bidirectional — creating "Alexandra is Mentor of Tobias" automatically creates "Tobias is Mentee of Alexandra". The `inverse_id` links the two records.

---

## Context classification

The `relationship_nature` on the context section marks the overall tone of the relationship. The same three values also appear on individual interactions, communications, and observations.

| Value | When to use |
|---|---|
| `personal` | Social, family, or personal life |
| `professional` | Work, business, or career-related |
| `mixed` | Genuinely both (friend who is also a colleague) |
| *(blank)* | Not classified — the default |

Filter your network:

```
GET /persons/?relationship_nature=professional
GET /persons/?relationship_nature=personal
```

---

## Placeholder and bot contacts

| Flag | What it means | How to act |
|---|---|---|
| `is_placeholder: true` | Auto-created from an unrecognised sender. Details are incomplete. | Fill in the real name and details, then PATCH `is_placeholder: false` to promote them to a full contact. |
| `is_bot: true` | An automated sender — newsletter, notification service, CI bot, or similar. | Set via `PATCH /persons/{id}`. Future communications from the same sender will be auto-flagged as bot traffic. |

---

## Creating and updating a person

`POST /persons/` — create. `PATCH /persons/{id}` — update (all fields optional).

**Minimal create:**
```json
{
  "first_name": "Alexandra",
  "last_name": "Reinholt"
}
```

**With channels and addresses:**
```json
{
  "first_name": "Alexandra",
  "last_name": "Reinholt",
  "channels": [
    {"type": "email", "value": "alex@example.com", "is_primary": true},
    {"type": "mobile", "value": "+49 151 12345678", "is_primary": true},
    {"type": "linkedin", "value": "https://linkedin.com/in/alexreinholt"},
    {"type": "discord", "value": "alexreinholt"}
  ],
  "addresses": [
    {"type": "home", "street": "Kastanienallee 22", "city": "Berlin", "postal_code": "10435", "country": "DE", "is_primary": true},
    {"type": "work", "city": "Munich", "country": "DE"}
  ],
  "occupation": "vc",
  "company": "Reinholt Ventures GmbH",
  "job_title": "Managing Partner",
  "nationality": "DE",
  "languages": ["de", "en"],
  "timezone": "Europe/Berlin",
  "tags": ["investor", "mentor"]
}
```

When `channels` or `addresses` are passed on a PATCH, they **replace all** existing entries for that field. Omit the field entirely to leave them unchanged.

---

## Loading sections

Sections are `null` by default.

| Section | To load it |
|---|---|
| Profile | `?include=profile` |
| Professional | `?include=professional` |
| Location (timezone + addresses) | `?include=location` |
| Context | `?include=context` |
| Physical | `?include=physical` |
| Personality | `?include=personality` |
| Channels | `?include=channels` |
| All sections | `?include=all` |

Combine sections: `?include=profile,professional,channels`

---

## Schema endpoint

`GET /persons/schema` — returns all valid vocabulary options in one call (no auth-scoped data, useful for populating form dropdowns).

```json
{
  "prefixes":              [{"id": "…", "name": "Dr.", "slug": "dr"}, …],
  "genders":               […],
  "occupations":           […],
  "eye_colors":            […],
  "hair_colors":           […],
  "communication_styles":  […],
  "tags":                  […],
  "relationship_types":    […],
  "preferred_contact":     […],
  "address_types":         ["home", "work", "other"],
  "channel_types":         ["email", "mobile", "phone", "whatsapp", "telegram", "discord", "twitter", "instagram", "github", "facebook", "linkedin", "website", "signal", "slack", "other"]
}
```
