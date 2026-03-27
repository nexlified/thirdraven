# Person — Field Guide

A Person is the central entity in ThirdRaven. Every contact, relationship, communication, and observation links back to one.

Fields are grouped into a **core** set (always returned) and **sections** that load on demand. Use `?include=profile,social` or `?include=all` to load extra sections.

---

## Core fields

These are always present in every Person response.

| Field | Example value | What it means |
|---|---|---|
| `id` | `01960000-…0001` | Unique identifier for this person |
| `owner_id` | `01960000-…0002` | The user account this person belongs to |
| `first_name` | `Alexandra` | First name (required) |
| `last_name` | `Reinholt` | Last name |
| `nickname` | `Alex` | Informal name or alias |
| `email` | `alex@example.com` | Primary email — derived from contact methods (read-only here) |
| `phone` | `+49 151 12345678` | Primary phone — derived from contact methods (read-only here) |
| `closeness_level` | `4` | How close you are: 1 (distant) → 5 (very close) |
| `notes` | `"Met at FinTech Forum…"` | Free-text notes about the person |
| `tags` | `["Investor", "Mentor"]` | Labels from your vocabulary (see *Tags* below) |
| `visibility` | `private` | `private` = only you · `household` = shared with household |
| `household_id` | `null` | ID of the household this person is shared with, if any |
| `is_placeholder` | `false` | Auto-created from an unknown sender; not yet a real contact |
| `is_bot` | `false` | Automated sender (newsletter, CI bot, notification service) |
| `created_at` | `2025-06-15T09:30:00Z` | When this record was created |
| `updated_at` | `2026-03-10T14:22:11Z` | When this record was last modified |

> **Note on email and phone**: these are convenience fields derived from the person's primary contact method. To add, update, or manage all contact methods use `POST/PATCH/DELETE /persons/{id}/contact-methods/` or `?include=contact_methods`.

### Tags

Tags are free labels you define in your vocabulary. Each tag in the response looks like:

| Sub-field | Example | What it means |
|---|---|---|
| `id` | `01960000-…0010` | Internal ID of the tag term |
| `name` | `Investor` | Display name |
| `slug` | `investor` | The value you use when creating/updating |

---

## Profile section — `?include=profile`

Personal identity details.

| Field | Example value | What it means |
|---|---|---|
| `middle_name` | `Marie` | Middle name |
| `prefix` | `Dr.` | Name prefix (Mr, Dr, Prof, etc.) from your vocabulary |
| `date_of_birth` | `1988-04-23` | Date of birth (YYYY-MM-DD) |
| `gender` | `Female` | Gender, from your vocabulary |
| `nationality` | `Germany (DE)` | Country of nationality — ISO 3166-1 code stored, full name returned |
| `languages` | `German, English, French` | Languages spoken — ISO 639-1 codes stored, full names returned |

---

## Professional section — `?include=professional`

Work and career details.

| Field | Example value | What it means |
|---|---|---|
| `occupation` | `Venture Capitalist` | Job category, from your vocabulary |
| `company` | `Reinholt Ventures GmbH` | Employer or company name |
| `job_title` | `Managing Partner` | Job title |
| `linkedin_url` | `https://linkedin.com/in/…` | LinkedIn profile URL |
| `phone_secondary` | `+49 30 9876543` | Work or secondary phone |

---

## Social section — `?include=social`

Online handles and presence.

| Field | Example value | What it means |
|---|---|---|
| `twitter_handle` | `@alexreinholt` | X / Twitter username |
| `instagram_handle` | `alex.reinholt` | Instagram username |
| `website_url` | `https://reinholtventures.de` | Personal or company website |
| `facebook_url` | `https://facebook.com/…` | Facebook profile URL |
| `github_handle` | `alexreinholt` | GitHub username |
| `discord_handle` | `alexreinholt#4821` | Discord username |
| `telegram_handle` | `@alex_r` | Telegram username |

---

## Location section — `?include=location`

Where the person lives and works. Each address is a structured object with its own city, postal code, country, and coordinates.

**Home address** (`address_home`):

| Sub-field | Example value | What it means |
|---|---|---|
| `street` | `Kastanienallee 22` | Street address |
| `city` | `Berlin` | City |
| `postal_code` | `10435` | Postal / ZIP code |
| `country` | `Germany (DE)` | Country — ISO code stored, full name returned |
| `lat` | `52.5382` | Latitude (set automatically if geocoded) |
| `lng` | `13.4034` | Longitude |

**Work address** (`address_work`): same structure as home address.

| Field | Example value | What it means |
|---|---|---|
| `timezone` | `Europe/Berlin (+01:00)` | IANA timezone — used for scheduling and time display |

---

## Context section — `?include=context`

How and when you know this person, and how often to stay in touch.

| Field | Example value | What it means |
|---|---|---|
| `how_we_met` | `"Introduced by Tobias at FinTech Forum 2023"` | Origin story of the relationship |
| `first_met_on` | `2023-09-14` | Date you first met (YYYY-MM-DD) |
| `last_contacted_on` | `2026-02-28` | Date of most recent contact — updated automatically when a communication arrives |
| `contact_frequency_days` | `30` | How often you intend to reach out, in days (30 = monthly) |
| `preferred_contact` | `Email` | Their preferred communication channel, from your vocabulary |
| `relationship_nature` | `professional` | Overall nature of the relationship: `personal` · `professional` · `mixed` · *(blank = unclassified)* |

---

## Physical section — `?include=physical`

Physical characteristics — useful for remembering people after a long time.

| Field | Example value | What it means |
|---|---|---|
| `height_cm` | `172.0` | Height in centimetres |
| `eye_color` | `Green` | Eye colour, from your vocabulary |
| `hair_color` | `Brown` | Hair colour, from your vocabulary |
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
| `communication_style` | `Direct` | How they prefer to communicate, from your vocabulary |

---

## Contact methods section — `?include=contact_methods`

A person can have multiple email addresses, phone numbers, and other contact channels. Each entry looks like:

| Field | Example value | What it means |
|---|---|---|
| `id` | `01960000-…0020` | Unique ID of this contact method |
| `value` | `alex@example.com` | The actual address, number, or handle |
| `type` | `email` | Channel: `email` · `phone` · `whatsapp` · `telegram` · etc. |
| `label` | `work` | Optional label: `work` · `personal` · *(blank)* |
| `is_primary` | `true` | Whether this is the primary contact for its type |

The `email` and `phone` fields in the core response are shortcut views of the `is_primary=true` entries for those types.

**Managing contact methods:**

| Endpoint | What it does |
|---|---|
| `POST /persons/{id}/contact-methods/` | Add a new contact method |
| `PATCH /persons/{id}/contact-methods/{cm_id}` | Update an existing entry |
| `DELETE /persons/{id}/contact-methods/{cm_id}` | Remove an entry |

---

## Relationships

Relationships are always included when fetching a single person (`GET /persons/{id}`). Each entry represents one directional link.

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
├── inverse_id         ID of the paired reverse record (Tobias → Mentee → Alexandra)
└── created_at         2025-10-01T11:00:00Z
```

Relationships are always bidirectional — creating "Alexandra is Mentor of Tobias" also creates "Tobias is Mentee of Alexandra". The `inverse_id` links the two records together.

---

## Context classification

The `context` field on interactions, communications, and observations marks whether an event was personal, professional, or mixed.

| Value | When to use |
|---|---|
| `personal` | Social, family, or personal life |
| `professional` | Work meetings, business emails, career-related |
| `mixed` | Genuinely both (e.g. a friend who is also a colleague) |
| *(blank)* | Not classified — the default; only set it when you care |

The `relationship_nature` field on a person's context section is the same idea, but covers the **overall** relationship rather than individual events. Use it to quickly segment your network:

> `GET /persons/?relationship_nature=professional` — all professional contacts
> `GET /persons/?relationship_nature=personal` — all personal contacts

---

## Placeholder and bot contacts

| Flag | What it means | How to act on it |
|---|---|---|
| `is_placeholder: true` | ThirdRaven auto-created this person from an unrecognised sender in an incoming communication. Their details are incomplete. | Review and fill in their real name and details, then set `is_placeholder: false` to promote them to a full contact. |
| `is_bot: true` | This is an automated sender — a newsletter, notification service, CI bot, or similar. | Set via `PATCH /persons/{id}`. Future communications from the same sender will automatically be flagged as bot traffic. |

---

## Loading sections

Sections are `null` by default and loaded on request to keep responses lean.

| Section | To load it |
|---|---|
| Profile | `?include=profile` |
| Professional | `?include=professional` |
| Social | `?include=social` |
| Location | `?include=location` |
| Context | `?include=context` |
| Physical | `?include=physical` |
| Personality | `?include=personality` |
| Contact methods | `?include=contact_methods` |
| All sections | `?include=all` |

Combine sections: `?include=profile,professional,social`
