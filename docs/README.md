# ThirdRaven — Docs

VitePress documentation site for ThirdRaven. Contains architecture guides, API reference, data model documentation, and technical specifications.

> Part of the [ThirdRaven monorepo](../README.md).

---

## Setup

### Prerequisites

- Node.js 18+
- npm (or bun)

### 1. Install dependencies

```bash
cd docs
npm install
```

### 2. Start the dev server

```bash
npm run docs:dev
```

Docs available at `http://localhost:5173` (or the next available port).

---

## Development Commands

| Task | Command |
|---|---|
| Start dev server | `npm run docs:dev` |
| Build for production | `npm run docs:build` |
| Preview production build | `npm run docs:preview` |

Or from the repo root:

```bash
make dev-docs   # start VitePress dev server
make build      # build frontend + docs for production
```

---

## Content Structure

```
docs/
├── .vitepress/
│   └── config.ts           # VitePress nav and sidebar configuration
├── specs/
│   ├── person-entity-spec.md
│   ├── asset-entity-spec.md
│   └── migration-plan.md
├── index.md                # Homepage (hero layout)
├── architecture.md         # System design and data flow
├── api-reference.md        # Endpoint documentation
├── data-models.md          # Full schema reference
├── development.md          # Contributor and development guide
├── vocabulary-system.md    # How slugs and vocabulary terms work
└── person_entity_example.md
```

---

## Adding a New Page

1. Create a `.md` file in `docs/`.
2. Add it to the sidebar in `.vitepress/config.ts`.

```ts
sidebar: [
  { text: 'My New Page', link: '/my-new-page' },
  // ...
]
```
