# Frontend — Resyntha

React 19 + TypeScript 6 + Vite 8 workspace for the Resyntha research intelligence platform.

> See [README.md](../README.md) for project overview and quick start.

---

## Tech Stack

| Concern | Choice |
|---------|--------|
| Framework | React 19 |
| Build Tool | Vite 8 |
| Language | TypeScript 6 (strict mode) |
| Styling | Tailwind CSS 4 |
| Server State | TanStack Query 5 |
| Client State | Zustand 5 |
| Routing | React Router 7 |
| Graph Visualization | React Flow 12 |
| Icons | Lucide React |
| UI Primitives | Radix UI |
| HTTP Client | Axios |
| Linting | oxlint |
| Testing | Vitest + Testing Library |

---

## Routing

Defined in `src/app/router.tsx` using `createBrowserRouter`:

```
/                          → redirect to /investigations
/investigations            → DashboardPage (list all)
/investigations/:id        → InvestigationLayout (nested)
  /overview                → OverviewPage
  /papers                  → PapersPage
  /landscape               → LandscapePage
  /artifacts               → ArtifactsPage
  /executions              → ExecutionsPage
  /knowledge               → WorkspaceKnowledge
  /graph                   → GraphPage
  /notes                   → NotesPage
  /copilot                 → CopilotPage
  /analysis                → WorkspaceAnalysis
  /validation              → WorkspaceValidation
  /timeline                → WorkspaceTimeline
  /gaps                    → WorkspaceResearchGaps
/pipeline                  → Pipeline
/settings                  → Settings
*                          → NotFound
```

- Protected routes rendered inside `AppShell` (sidebar + top bar + workspace layout).
- All investigation pages share `InvestigationLayout` which loads investigation data and provides it via React Query.
- Route guards in `src/routes/guards.tsx` (currently a stub for future auth).

---

## Feature Folders

The `src/features/` directory follows a domain-grouped structure:

```
features/investigations/
├── api/                     # API call functions
├── artifacts/               # Artifact-specific components
├── bookmarks/               # Bookmark feature
├── collections/             # Collection management
├── components/              # Shared investigation components
├── copilot/                 # Copilot components + pages
├── executions/              # Execution display
├── graph/                   # Graph visualization (React Flow)
├── hooks/                   # Investigation-specific hooks
├── landscape/               # Landscape display
├── layout/                  # InvestigationLayout
├── notes/                   # Notes feature
├── pages/                   # Investigation sub-pages
├── papers/                  # Paper list + cards
└── reading-status/          # Reading status controls
```

---

## TanStack Query

Configured in `src/app/query-client.ts` with:

- `staleTime: 30_000` — 30s before refetch
- `retry: 1` — single retry on failure
- `refetchOnWindowFocus: false`

Custom hooks in `src/hooks/` wrap TanStack Query:

| Hook | Endpoint | Stale Time |
|------|----------|------------|
| `useInvestigations()` | `GET /investigations` | 30s |
| `useInvestigation(id)` | `GET /investigations/:id` | 30s |
| `usePapers(id)` | `GET /investigations/:id/papers` | 60s |
| `useExecutions(id)` | `GET /investigations/:id/executions` | 15s |
| `useArtifacts(id)` | `GET /investigations/:id/artifacts` | 30s |
| `useCopilot(id)` | `GET /investigations/:id/copilot/messages` | 0 (always fresh) |

Mutations use `useMutation` with optimistic updates and query invalidation.

---

## State Management

Three Zustand stores in `src/stores/`:

| Store | File | Purpose |
|-------|------|---------|
| `useAuthStore` | `auth.ts` | Authentication token + user (stub for future auth) |
| `useUIStore` | `ui.ts` | Sidebar state, theme, command palette, inspector |
| `useBreadcrumbStore` | `breadcrumbs.ts` | Dynamic breadcrumb trail |
| `useNotificationStore` | `notifications.ts` | Toast notifications |

---

## API Layer

```
src/
├── api/                     # Core API infrastructure
│   ├── http.ts              # Axios instance (base URL, interceptors)
│   ├── errors.ts            # AppError class with status categorization
│   ├── retry.ts             # Retry logic
│   ├── cancellation.ts      # Request cancellation (AbortController)
│   └── types.ts             # API response/error types
├── services/                # Typed API client functions
│   ├── investigations.ts
│   ├── retrieval.ts
│   ├── executions.ts
│   ├── artifacts.ts
│   ├── copilot.ts
│   └── knowledge.ts
└── hooks/                   # TanStack Query wrappers
    ├── useInvestigations.ts
    ├── useExecutions.ts
    ├── useArtifacts.ts
    ├── useRetrieval.ts
    └── useCopilot.ts
```

The `http.ts` Axios instance:
- Base URL from `import.meta.env.VITE_API_URL` (default `http://localhost:8000/api/v1`)
- Request interceptor adds `Authorization: Bearer <token>` if available
- Response interceptor normalizes errors via `AppError`

---

## Testing

```bash
# Run all tests
npx vitest run

# Watch mode
npx vitest

# With coverage
npx vitest run --coverage
```

---

## Development

```bash
npm run dev       # Start dev server (port 5173)
npm run build     # TypeScript check + production build
npm run lint      # oxlint
npm run preview   # Preview production build
```
