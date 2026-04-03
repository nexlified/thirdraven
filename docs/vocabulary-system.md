# ThirdRaven — Vocabulary System

## Why Vocabulary / Term?

Early designs used Python `StrEnum` for fixed categories (asset status, gender, relationship type) and plain string arrays for tags. This approach had two problems:

1. **Rigidity** — Adding a new category required a code change, migration, and redeploy.
2. **No metadata** — Enums cannot carry descriptions, sort weights, hierarchy, or external provider IDs.

The vocabulary/term system replaces all of those patterns with a flexible, database-driven taxonomy. A **vocabulary** is a named set; a **term** is a member of that set. New terms can be added at runtime via the API — no code change required.

---

## Vocabulary Fields

| Field | Type | Purpose |
|---|---|---|
| `id` | UUID | Primary key |
| `name` | str | Human-readable label (e.g., `"Relationship Types"`) |
| `machine_name` | str | URL-safe slug used in API paths (e.g., `"relationship-types"`) |
| `description` | str \| None | Optional explanation |
| `is_hierarchical` | bool | If `true`, terms may have `parent_id` set |
| `allows_new_terms` | bool | If `false`, only seed terms may be used (effectively read-only at runtime) |
| `is_locked` | bool | If `true`, the vocabulary cannot be deleted via the API |
| `source_type` | str | `"internal"` (default) or `"external"` |
| `external_provider` | str \| None | Name of the provider if `source_type = "external"` |
| `is_active` | bool | Soft visibility flag |
| `created_at` | datetime | |

---

## Term Fields

| Field | Type | Purpose |
|---|---|---|
| `id` | UUID | Primary key |
| `vocabulary_id` | UUID | FK → vocabulary |
| `name` | str | Human-readable label (e.g., `"Best Friend"`) |
| `slug` | str | URL-safe identifier, unique **within** its vocabulary (e.g., `"best-friend"`) |
| `description` | str \| None | Optional explanation |
| `parent_id` | UUID \| None | FK → term (self-referential); used in hierarchical vocabs |
| `weight` | int | Sort weight; lower numbers sort first (default: `0`) |
| `external_id` | str \| None | ID from an external taxonomy provider |
| `metadata_` | dict \| None | Arbitrary JSON key-value data |
| `icon` | str \| None | [Lucide](https://lucide.dev) icon name (e.g., `"star"`, `"briefcase"`, `"heart"`). `null` means no icon. |
| `is_active` | bool | Soft visibility flag |
| `created_at` | datetime | |

The `(vocabulary_id, slug)` pair is unique — the same slug can exist in different vocabularies.

---

## Icons

Each term carries an optional `icon` field containing a **[Lucide](https://lucide.dev) icon name** — a lowercase, hyphen-separated string such as `"star"`, `"briefcase"`, or `"heart"`. The icon name is library-agnostic storage; rendering is done client-side using the Lucide library for your platform.

The seed script populates icons for all built-in terms. User-created terms default to `null` (no icon). Clients should always handle the `null` case gracefully.

### Rendering Icons in React

Install the `lucide-react` package:

```bash
npm install lucide-react
```

Use the `DynamicIcon` helper to render a term's icon by name:

```tsx
import { icons, type LucideProps } from "lucide-react";

interface TermIconProps extends LucideProps {
  name: string | null;
  fallback?: React.ReactNode;
}

function TermIcon({ name, fallback = null, ...props }: TermIconProps) {
  if (!name) return <>{fallback}</>;
  // Lucide icon names are kebab-case; component names are PascalCase
  const key = name
    .split("-")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join("") as keyof typeof icons;
  const Icon = icons[key];
  if (!Icon) return <>{fallback}</>;
  return <Icon {...props} />;
}

// Usage
<TermIcon name={term.icon} size={16} />
```

For static imports (better tree-shaking), import the icon directly:

```tsx
import { Star } from "lucide-react";

<Star size={16} />
```

### Rendering Icons in Flutter

Add the `lucide_icons` package:

```yaml
# pubspec.yaml
dependencies:
  lucide_icons: ^0.0.2
```

Map the icon name from the API to the Flutter `LucideIcons` constant. Icon names use camelCase in the Dart package:

```dart
import 'package:lucide_icons/lucide_icons.dart';

IconData? termIconData(String? iconName) {
  if (iconName == null) return null;
  // Convert kebab-case to camelCase
  final camel = iconName.splitMapJoin(
    RegExp(r'-([a-z])'),
    onMatch: (m) => m.group(1)!.toUpperCase(),
    onNonMatch: (s) => s,
  );
  // Look up by name using a reflection-style map (generate or maintain manually)
  const iconMap = <String, IconData>{
    'star': LucideIcons.star,
    'briefcase': LucideIcons.briefcase,
    'heart': LucideIcons.heart,
    'smile': LucideIcons.smile,
    'users': LucideIcons.users,
    // add other icons your app uses
  };
  return iconMap[iconName];
}

// Usage
final iconData = termIconData(term.icon);
if (iconData != null) Icon(iconData, size: 16)
```

---

## The `resolve_term_slug()` Pattern

Any write operation that stores a term FK (e.g., `category_term_id`, `label_term_id`, `gender_term_id`) accepts a **slug string** in the request payload rather than a UUID. The CRUD layer resolves the slug to a UUID before writing:

```python
# app/crud/vocabulary.py
async def resolve_term_slug(
    db: AsyncSession,
    machine_name: str,
    slug: str,
) -> uuid.UUID:
    result = await db.execute(
        select(Term.id)
        .join(Vocabulary, Term.vocabulary_id == Vocabulary.id)
        .where(Vocabulary.machine_name == machine_name)
        .where(Term.slug == slug)
        .where(Term.is_active == True)
    )
    term_id = result.scalar_one_or_none()
    if not term_id:
        raise HTTPException(
            status_code=422,
            detail=f"Term '{slug}' not found in vocabulary '{machine_name}'"
        )
    return term_id
```

Usage example in `crud/asset.py`:
```python
category_term_id = await resolve_term_slug(db, "asset-categories", data.category)
status_term_id   = await resolve_term_slug(db, "asset-statuses", data.status)
```

---

## ISO Resolver Pattern

The ISO reference tables (Country, Language, Timezone) use the same principle but resolve standard codes instead of slugs:

```python
# Resolve by ISO 3166-1 alpha-2
country_id = await resolve_country_alpha2(db, "US")

# Resolve by ISO 639-1
language_id = await resolve_language_code(db, "en")

# Resolve by IANA timezone name
timezone_id = await resolve_timezone_name(db, "America/New_York")
```

All resolvers raise HTTP 422 if the code is not found.

---

## Seeded Vocabularies

The following vocabularies are created by `python -m seeds.seed_data`. All are `is_locked = true` to prevent accidental deletion.

| `machine_name` | Locked | Hierarchical | Example Terms (with icons) |
|---|---|---|---|
| `person-tags` | yes | no | `friend` (smile), `vip` (star), `work` (briefcase) |
| `relationship-types` | yes | no | `friend` (smile), `colleague` (briefcase), `mentor` (book-open) |
| `name-prefixes` | yes | no | `mr`, `ms`, `dr` (no icons) |
| `genders` | yes | no | `male` (user), `female` (user), `non-binary` (user) |
| `occupations` | yes | no | `software-engineer` (code), `doctor` (stethoscope), `teacher` (book-open) |
| `asset-categories` | yes | no | `electronics` (cpu), `vehicle` (car), `software-license` (code) |
| `asset-statuses` | yes | no | `active` (check-circle), `broken` (x-circle), `sold` (tag) |
| `asset-tags` | yes | no | `essential` (star), `needs-repair` (wrench) |
| `interaction-types` | yes | no | `meeting` (users), `phone-call` (phone), `email` (mail) |
| `communication-channels` | no | no | `email` (mail), `whatsapp` (message-circle), `slack` (hash) |
| `life-event-types` | no | yes | `graduated` (graduation-cap), `got-married` (heart) |
| `life-event-emotions` | no | no | `happy` (smile), `sad` (frown), `excited` (zap) |
| `significant-date-types` | no | no | `birthday` (cake), `wedding-anniversary` (heart) |
| `observation-tags` | no | no | `gift-idea` (gift), `interests` (heart) |
| `asset-conditions` | yes | no | `new` (star), `broken-condition` (x-circle) |
| `document-asset-types` | no | no | `passport` (book), `drivers-license` (car) |
| `financial-account-types` | no | no | `savings` (piggy-bank), `credit-card` (credit-card) |

---

## How to Add New Terms at Runtime

No code change or migration required. Use the API:

```http
POST /api/v1/vocabularies/person-tags/terms
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Investor",
  "slug": "investor",
  "description": "People who have invested in my projects",
  "weight": 10,
  "icon": "trending-up"
}
```

If the vocabulary has `allows_new_terms = false`, this operation is blocked.

---

## Hierarchical Terms

Set `is_hierarchical = true` on the vocabulary, then provide `parent_id` when creating child terms:

```http
POST /api/v1/vocabularies/occupations/terms
{
  "name": "Frontend Engineer",
  "slug": "frontend-engineer",
  "parent_id": "<uuid of software-engineer term>",
  "icon": "code"
}
```

Filter terms by parent when listing:
```
GET /api/v1/vocabularies/occupations/terms?parent=software-engineer
```

---

## ISO Reference Tables vs. Vocabulary Terms

| Feature | Vocabulary / Term | ISO Tables |
|---|---|---|
| Managed by | API (runtime) | Seed script only |
| Identified by | `machine_name` + `slug` | Standard codes (`alpha2`, `iso_639_1`, IANA name) |
| Mutable | Yes (if `allows_new_terms`) | No |
| Use case | Custom taxonomies, tags, categories | Countries, languages, timezones |
| Resolver | `resolve_term_slug()` | `resolve_country_alpha2()`, etc. |
