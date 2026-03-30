# ThirdRaven — Frontend

Vite + React + TypeScript SPA for ThirdRaven. Provides the web interface for managing people, interactions, observations, and other personal data stored in the ThirdRaven backend.

> Part of the [ThirdRaven monorepo](../README.md).

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | React 19 |
| Language | TypeScript 5 |
| Build tool | Vite |
| Routing | React Router 7 |
| Package manager | npm (or bun) |
| Linting | ESLint |

---

## Setup

### Prerequisites

- Node.js 18+
- npm (or bun)
- ThirdRaven backend running on `http://localhost:8000`

### 1. Install dependencies

```bash
cd frontend
npm install
```

### 2. Start the dev server

```bash
npm run dev
```

App available at `http://localhost:5173`.

---

## Development Commands

| Task | Command |
|---|---|
| Start dev server | `npm run dev` |
| Build for production | `npm run build` |
| Preview production build | `npm run preview` |
| Lint | `npm run lint` |

---

## Project Structure

```
frontend/
├── src/
│   ├── api/                # HTTP client modules (auth, persons, vocabularies, etc.)
│   ├── components/         # Reusable React components
│   │   ├── AppLayout.tsx
│   │   ├── FormControls.tsx
│   │   ├── ProtectedRoute.tsx
│   │   └── QuickCreateModal.tsx
│   ├── context/            # React context (AuthContext)
│   ├── hooks/              # Custom hooks (useSettings)
│   ├── pages/              # Page components
│   │   ├── Dashboard.tsx
│   │   ├── Login.tsx
│   │   ├── Register.tsx
│   │   ├── People.tsx
│   │   ├── PersonDetail.tsx
│   │   ├── Settings.tsx
│   │   └── Vocabularies.tsx
│   ├── assets/             # Static assets
│   ├── App.tsx             # Root component with routing
│   ├── main.tsx            # Entry point
│   └── index.css           # Global styles
├── public/
├── index.html
├── vite.config.ts
├── tsconfig.app.json
├── tsconfig.node.json
└── package.json
```

---

## Backend Connection

The frontend communicates with the ThirdRaven backend API at `http://localhost:8000/api/v1`. The HTTP client is configured in `src/api/client.ts`. JWT tokens obtained at login are stored in `localStorage` and attached to every authenticated request.

To point the frontend at a different backend URL, update the base URL in `src/api/client.ts`.

