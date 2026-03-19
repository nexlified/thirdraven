# ThirdRaven — API Reference

All endpoints are prefixed with `/api/v1/`. All protected endpoints require `Authorization: Bearer <token>`.

---

## Authentication — `/api/v1/auth`

### `POST /auth/register`

Register a new user.

**Request body:**
| Field | Type | Required |
|---|---|---|
| `username` | str | yes |
| `email` | str (email) | yes |
| `password` | str | yes |

**Response — 201:**
```json
{
  "id": "uuid",
  "username": "alice",
  "email": "alice@example.com",
  "created_at": "2026-01-01T00:00:00"
}
```

---

### `POST /auth/login`

Obtain a JWT access token.

**Request body (form data):**
| Field | Type |
|---|---|
| `username` | str |
| `password` | str |

**Response — 200:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

---

## Persons — `/api/v1/persons`

### `POST /persons/`

Create a new person (flat payload; CRUD splits across up to 6 tables).

**Request body:**
| Field | Type | Section |
|---|---|---|
| `first_name` | str | core (required) |
| `last_name` | str \| null | core |
| `nickname` | str \| null | core |
| `email` | str \| null | core |
| `phone` | str \| null | core |
| `notes` | str \| null | core |
| `closeness_level` | int \| null | core |
| `tags` | list[str] (slugs) | core / junction |
| `middle_name` | str \| null | profile |
| `prefix` | str \| null (slug) | profile |
| `date_of_birth` | date \| null | profile |
| `gender` | str \| null (slug) | profile |
| `nationality` | str \| null (alpha2) | profile |
| `languages` | list[str] (ISO 639-1) | profile / junction |
| `occupation` | str \| null (slug) | professional |
| `company` | str \| null | professional |
| `job_title` | str \| null | professional |
| `linkedin_url` | str \| null | professional |
| `phone_secondary` | str \| null | professional |
| `twitter_handle` | str \| null | social |
| `instagram_handle` | str \| null | social |
| `website_url` | str \| null | social |
| `address_home` | str \| null | location |
| `address_work` | str \| null | location |
| `city` | str \| null | location |
| `country` | str \| null (alpha2) | location |
| `timezone` | str \| null (IANA name) | location |
| `how_we_met` | str \| null | context |
| `first_met_on` | date \| null | context |

**Response — 201:** `PersonSlim`
```json
{
  "id": "uuid",
  "owner_id": "uuid",
  "first_name": "Alice",
  "last_name": "Smith",
  "nickname": null,
  "email": "alice@example.com",
  "phone": null,
  "notes": null,
  "closeness_level": 8,
  "tags": [{ "id": "uuid", "name": "Friend", "slug": "friend" }],
  "created_at": "...",
  "updated_at": "..."
}
```

---

### `GET /persons/`

List persons owned by the current user.

**Query params:**
| Param | Type | Default |
|---|---|---|
| `skip` | int | 0 |
| `limit` | int | 100 |

**Response — 200:** `list[PersonSlim]`

---

### `GET /persons/{person_id}`

Get a single person. Optionally load extension sections.

**Query params:**
| Param | Type | Values |
|---|---|---|
| `include` | str | comma-separated: `profile`, `professional`, `social`, `location`, `context` |

**Response — 200:** `PersonWithRelationships`
```json
{
  "id": "uuid",
  "first_name": "Alice",
  "tags": [...],
  "profile": {
    "middle_name": null,
    "prefix": { "id": "uuid", "name": "Dr.", "slug": "dr" },
    "date_of_birth": "1990-05-15",
    "gender": { "id": "uuid", "name": "Female", "slug": "female" },
    "nationality": { "id": "uuid", "name": "United States", "alpha2": "US" },
    "languages": [{ "id": "uuid", "name": "English", "iso_639_1": "en" }]
  },
  "professional": { "company": "Acme", "job_title": "Engineer", ... },
  "social": { "twitter_handle": "@alice", ... },
  "location": { "city": "NYC", "country": {...}, "timezone": {...}, ... },
  "context": { "how_we_met": "Conference", "first_met_on": "2020-03-01" },
  "relationships": [
    { "id": "uuid", "from_person_id": "uuid", "to_person_id": "uuid", "label_term_id": "uuid", "created_at": "..." }
  ]
}
```

---

### `PATCH /persons/{person_id}`

Partial update. All fields optional (same shape as `PersonCreate`).

**Response — 200:** `PersonSlim`

---

### `DELETE /persons/{person_id}`

Soft-delete (sets `deleted_at`).

**Response — 204:** No content

---

### `POST /persons/{person_id}/relationships`

Create a directed relationship to another person.

**Request body:**
| Field | Type | Notes |
|---|---|---|
| `to_person_id` | UUID | Target person |
| `label` | str | Slug from vocab `relationship-types` (e.g., `"friend"`) |

**Response — 201:**
```json
{
  "id": "uuid",
  "from_person_id": "uuid",
  "to_person_id": "uuid",
  "label_term_id": "uuid",
  "created_at": "..."
}
```

---

### `POST /persons/{person_id}/terms`

Attach an ad-hoc term to a person.

**Request body:**
| Field | Type | Notes |
|---|---|---|
| `term_id` | UUID | Term to attach |
| `context` | str \| null | Optional note |

**Response — 201:**
```json
{
  "id": "uuid",
  "person_id": "uuid",
  "term_id": "uuid",
  "context": "Met at hackathon",
  "created_at": "..."
}
```

---

### `GET /persons/{person_id}/terms`

List all terms attached to a person.

**Response — 200:** `list[PersonTermPublic]`

---

### `DELETE /persons/{person_id}/terms/{term_id}`

Remove a term from a person.

**Response — 204:** No content

---

## Contacts — `/api/v1/contacts`

### `POST /contacts/`

**Request body:**
| Field | Type |
|---|---|
| `first_name` | str (required) |
| `last_name` | str \| null |
| `email` | str \| null |
| `phone` | str \| null |
| `notes` | str \| null |
| `tags` | list[str] |

**Response — 201:** `ContactPublicRead`
```json
{
  "id": "uuid",
  "owner_id": "uuid",
  "first_name": "Bob",
  "last_name": "Jones",
  "email": null,
  "phone": null,
  "notes": null,
  "tags": [],
  "created_at": "...",
  "updated_at": "..."
}
```

---

### `GET /contacts/`

**Query params:** `skip` (default 0), `limit` (default 100)

**Response — 200:** `list[ContactPublicRead]`

---

### `GET /contacts/{contact_id}`

**Response — 200:** `ContactWithRelationships`
```json
{
  ...ContactPublicRead,
  "relationships": [
    { "id": "uuid", "from_contact_id": "uuid", "to_contact_id": "uuid", "label": "colleague", "created_at": "..." }
  ]
}
```

---

### `PATCH /contacts/{contact_id}`

All fields optional.

**Response — 200:** `ContactPublicRead`

---

### `DELETE /contacts/{contact_id}`

Soft delete.

**Response — 204:** No content

---

### `POST /contacts/{contact_id}/relationships`

**Request body:**
| Field | Type |
|---|---|
| `to_contact_id` | UUID |
| `label` | str (free-text) |

**Response — 201:** `RelationshipPublic`

---

## Assets — `/api/v1/assets`

### `POST /assets/`

**Request body:**
| Field | Type | Notes |
|---|---|---|
| `name` | str | required |
| `category` | str | slug from vocab `asset-categories` (required) |
| `status` | str | slug from vocab `asset-statuses` (default: `"active"`) |
| `description` | str \| null | |
| `serial_number` | str \| null | |
| `vendor` | str \| null | |
| `purchase_date` | date \| null | |
| `purchase_price` | float \| null | |
| `current_value` | float \| null | |
| `tags` | list[str] | slugs from vocab `asset-tags` |
| `notes` | str \| null | |

**Response — 201:** `AssetPublicRead`
```json
{
  "id": "uuid",
  "owner_id": "uuid",
  "name": "MacBook Pro",
  "category": { "id": "uuid", "name": "Hardware", "slug": "hardware" },
  "status": { "id": "uuid", "name": "Active", "slug": "active" },
  "description": null,
  "serial_number": "C02XY",
  "vendor": "Apple",
  "purchase_date": "2023-01-15",
  "purchase_price": 2499.00,
  "current_value": 1800.00,
  "tags": [{ "id": "uuid", "name": "Work", "slug": "work" }],
  "notes": null,
  "created_at": "...",
  "updated_at": "..."
}
```

---

### `GET /assets/`

**Query params:**
| Param | Type | Notes |
|---|---|---|
| `skip` | int | default 0 |
| `limit` | int | default 100 |
| `category` | str \| null | Filter by category slug |
| `status` | str \| null | Filter by status slug |

**Response — 200:** `list[AssetPublicRead]`

---

### `GET /assets/{asset_id}`

**Response — 200:** `AssetPublicRead`

---

### `PATCH /assets/{asset_id}`

All fields optional.

**Response — 200:** `AssetPublicRead`

---

### `DELETE /assets/{asset_id}`

Soft delete.

**Response — 204:** No content

---

## Interactions — `/api/v1/persons/{person_id}/interactions`

### `POST /persons/{person_id}/interactions/`

**Request body:**
| Field | Type | Notes |
|---|---|---|
| `title` | str | required |
| `interaction_type_id` | UUID \| null | FK → term |
| `term_id` | UUID \| null | FK → term (generic classifier) |
| `occurred_on` | date \| null | |
| `notes` | str \| null | |
| `metadata_` | dict \| null | Arbitrary JSON |

**Response — 201:** `InteractionPublicRead`

---

### `GET /persons/{person_id}/interactions/`

**Query params:**
| Param | Type | Notes |
|---|---|---|
| `skip` | int | default 0 |
| `limit` | int | default 100 |
| `type_slug` | str \| null | Filter by interaction type slug |

**Response — 200:** `list[InteractionPublicRead]`

---

### `GET /persons/{person_id}/interactions/{interaction_id}`

**Response — 200:** `InteractionPublicRead`

---

### `PATCH /persons/{person_id}/interactions/{interaction_id}`

**Response — 200:** `InteractionPublicRead`

---

### `DELETE /persons/{person_id}/interactions/{interaction_id}`

Hard delete (no soft delete).

**Response — 204:** No content

---

## Vocabularies — `/api/v1/vocabularies`

### `GET /vocabularies/`

**Query params:** `skip`, `limit`

**Response — 200:** `list[VocabularyPublic]`

---

### `POST /vocabularies/`

**Request body:**
| Field | Type | Notes |
|---|---|---|
| `name` | str | required |
| `machine_name` | str | required, unique slug |
| `description` | str \| null | |
| `is_hierarchical` | bool | default `false` |
| `allows_new_terms` | bool | default `true` |
| `is_locked` | bool | default `false` |
| `source_type` | str | default `"internal"` |
| `external_provider` | str \| null | |

**Response — 201:** `VocabularyPublic`

---

### `GET /vocabularies/{machine_name}`

**Response — 200:** `VocabularyPublic`

---

### `PATCH /vocabularies/{machine_name}`

Updatable fields: `name`, `description`, `allows_new_terms`, `external_provider`, `is_active`

**Response — 200:** `VocabularyPublic`

---

### `DELETE /vocabularies/{machine_name}`

Returns **409 Conflict** if `is_locked = true`.

**Response — 204:** No content

---

### `GET /vocabularies/{machine_name}/terms`

**Query params:**
| Param | Type | Notes |
|---|---|---|
| `parent` | str \| null | Filter by parent term slug |
| `search` | str \| null | Substring match on name/slug |
| `skip` | int | default 0 |
| `limit` | int | default 100 |

**Response — 200:** `list[TermPublic]`

---

### `POST /vocabularies/{machine_name}/terms`

**Request body:**
| Field | Type | Notes |
|---|---|---|
| `name` | str | required |
| `slug` | str | required, unique within vocabulary |
| `description` | str \| null | |
| `parent_id` | UUID \| null | For hierarchical vocabs |
| `weight` | int | default 0 |
| `external_id` | str \| null | |
| `metadata_` | dict \| null | |

**Response — 201:** `TermPublic`

---

### `GET /vocabularies/{machine_name}/terms/{slug}`

**Response — 200:** `TermPublic`

---

### `PATCH /vocabularies/{machine_name}/terms/{slug}`

All fields optional.

**Response — 200:** `TermPublic`

---

### `DELETE /vocabularies/{machine_name}/terms/{slug}`

Hard delete.

**Response — 204:** No content

---

## ISO Reference — `/api/v1/iso`

All ISO endpoints are **read-only** and do not require authentication for listing (implementation may vary).

### `GET /iso/countries/`

**Query params:** `search` (str), `skip`, `limit`

**Response — 200:** `list[CountryPublic]`

---

### `GET /iso/countries/{alpha2}`

**Response — 200:** `CountryPublic`
```json
{
  "id": "uuid",
  "name": "United States",
  "alpha2": "US",
  "alpha3": "USA",
  "numeric": "840",
  "calling_code": "+1",
  "region": "Americas",
  "subregion": "Northern America",
  "flag_emoji": "🇺🇸",
  "is_active": true
}
```

---

### `GET /iso/languages/`

**Query params:** `search` (str), `skip`, `limit`

**Response — 200:** `list[LanguagePublic]`

---

### `GET /iso/languages/{iso_639_1}`

**Response — 200:** `LanguagePublic`
```json
{
  "id": "uuid",
  "name": "English",
  "native_name": "English",
  "iso_639_1": "en",
  "iso_639_2": "eng",
  "is_active": true
}
```

---

### `GET /iso/timezones/`

**Query params:**
| Param | Type | Notes |
|---|---|---|
| `country` | str \| null | Filter by alpha2 country code |
| `skip` | int | default 0 |
| `limit` | int | default 100 |

**Response — 200:** `list[TimezonePublic]`

---

### `GET /iso/timezones/{timezone_id}`

**Response — 200:** `TimezonePublic`
```json
{
  "id": "uuid",
  "name": "America/New_York",
  "utc_offset": "-05:00",
  "utc_offset_dst": "-04:00",
  "country_id": "uuid",
  "is_active": true
}
```

---

## Health

### `GET /health`

No authentication required.

**Response — 200:**
```json
{ "status": "ok" }
```

---

## Common Error Responses

| Status | Meaning |
|---|---|
| 401 | Missing or invalid JWT |
| 404 | Resource not found (or belongs to another user) |
| 409 | Conflict (e.g., deleting a locked vocabulary) |
| 422 | Validation error (invalid slug, code not found in ISO tables, etc.) |
