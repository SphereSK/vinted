## Vinted Frontend (Next.js + shadcn/ui)

This directory contains the Next.js 15 (App Router + Tailwind) frontend that will power the Vinted dashboard. It was scaffolded with `create-next-app` and is ready for shadcn/ui component generation.

### Development

```bash
npm install        # already run during scaffolding
npm run dev        # starts Next.js dev server on http://localhost:3000
```

Environment variables are sourced from the repository root `.env`/`.env.local` files so backend and frontend share a single source of truth. Create (or update) the root `.env` to include the FastAPI connection details, and add any browser-exposed values (prefixed with `NEXT_PUBLIC_`) to `.env.local` if you need overrides:

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8933
NEXT_PUBLIC_STATUS_POLL_INTERVAL=5000
NEXT_PUBLIC_API_KEY=change_me_api_key
NEXT_PUBLIC_API_KEY_HEADER=X-API-Key
```

> Tip: `frontend/next.config.ts` loads the root `.env` before handing off to Next.js, so server-only values (e.g., database URLs) continue to be available to the backend while `NEXT_PUBLIC_*` variables are automatically exposed to the browser bundle.

### Project Structure

```
src/
  app/                     # App Router entry points (routes/layouts)
  components/
    ui/                    # shadcn/ui primitives (keep server components by default)
    layout/                # Shell pieces: navbar, sidebar, footer
    forms/                 # Reusable form fragments (field groups, validation helpers)
    modals/                # Dialog/popover components
    shared/                # Generic building blocks (cards, badges, charts, etc.)
  lib/
    api-client.ts          # Fetch wrapper (adds auth headers)
    config.ts              # Runtime configuration
    endpoints.ts           # Typed API calls
    types.ts               # Shared TypeScript contracts
```

Guidelines:

- Prefer server components unless interactivity is required; mark a file with `"use client"` only when the component truly needs it.
- Co-locate Zustand stores or other client-only hooks under `src/lib/state/` (or within `components/shared`) and keep them tree-shakeable. When introducing GSAP or similar animation libraries, wrap them in dynamic imports to avoid bloating the default bundle.
- Keep dialog/overlay logic in `components/modals` so screen readers can rely on consistent accessibility patterns.
- Forms should delegate validation to shared helpers (e.g., Zod) inside `components/forms` and emit backend-ready payloads.
- For authentication enhancements, add provider wiring in `components/layout` and expose guard hooks in `src/lib/auth.ts`.

### Component System

Run the shadcn/ui installer to generate the shared design system (buttons, cards, tables, dialogs):

```bash
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card table input dialog tabs toast separator
```

Keep components in `src/components/ui` and export custom composites from `src/components`.

### Current Screens

- **Dashboard tab:** Fetches `/api/stats`, `/api/configs`, and `/api/cron/jobs` for key metrics and configuration highlights.
- **Listings tab:** Searchable table of `/api/listings` with price movement indicators.
- **Scrape configs tab:** CRUD controls, manual run action, and Redis-backed status badges (polling interval uses `NEXT_PUBLIC_STATUS_POLL_INTERVAL`).

### Remaining Enhancements

- Provide rich detail drawers for configs (history, execution logs) once backend endpoints are available.
- Surface cron jobs in a dedicated management tab with sync controls.
- Hook up realtime updates via WebSocket/Redis pub-sub instead of polling when infrastructure is ready.

### Production Build

Once UI flows are implemented:

```bash
npm run build
npm run export    # optional if serving static output
```

Coordinate with the FastAPI service to mount the built assets (e.g., `frontend/out` or `frontend/.next`) via `StaticFiles`.
