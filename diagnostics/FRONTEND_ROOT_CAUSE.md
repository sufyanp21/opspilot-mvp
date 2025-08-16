## Frontend Root Cause Report

### A. Observed symptoms
- New Vite app under `apps/web` renders, but some environments still show an older UI.
- Repo contains multiple frontends: `apps/web` (Vite), `frontend` (Next.js), and `opspilot-mvp/apps/frontend` (legacy Vite). This increases risk of serving or running the wrong app.

How verified:
- Build/config inventory shows:
  - Vite configs: `apps/web/vite.config.ts`, `opspilot-mvp/apps/frontend/vite.config.ts`.
  - Next.js config: `frontend/next.config.js`.
  - Index HTML files: `apps/web/index.html`, `opspilot-mvp/apps/frontend/index.html`.
  - `apps/web/package.json` scripts: `dev`, `build`, `preview` present.
  - Router: `apps/web/src/routes.tsx` with new `AppLayout` and pages.

### B. All root-cause pathways (ways old UI could be served)
- Wrong app being served/started locally: running `frontend` (port 3000) or `opspilot-mvp/apps/frontend` instead of `apps/web` (port 5173).
- Static hosting/Nginx pointing to the wrong `dist` directory (legacy app) in container/deploy.
- Service worker caching a prior build and serving old assets.
- Env/base path mismatch leading to asset fetches from a stale location.

### C. Decisions & Fix Plan
- Add a runtime Build Beacon rendered on every page showing `APP_NAME`, `GIT_SHA`, `BUILD_TIME_ISO`, and a short nonce. This creates a definitive visual/version proof across dev and prod.
- Inject the same build info as meta tags in `index.html` so scripts can verify without a browser runtime.
- Force-unregister any service workers on load to eliminate stale caches. One-time safety switch with a comment to re-enable later.
- Log `VITE_API_BASE` at app startup in dev for env verification.
- Add diagnostic scripts:
  - `scripts/scanOldRefs.mjs` to scan for old references, ports, stale configs. Outputs `/diagnostics/SCAN_OLD_REFS.json` and `.md`.
  - `scripts/verifyNewUI.mjs` to start the server, fetch pages, parse the beacon/meta, and assert no old asset paths. Outputs `/diagnostics/VERIFY_{timestamp}.md`.
  - `scripts/resolveEnv.mjs` to record effective env resolution to `/diagnostics/ENV_RESOLUTION.md`.
  - `scripts/purgeCDN.mjs` (stub) for CDN invalidation if used.
- Keep structure unchanged; avoid re-scaffold. Minimal targeted edits only.

Verification:
- Visual beacon present in footer in both dev and prod.
- Verify script passes for dev (`npm run dev`) and preview (`npm run build && npm run preview`).
- No requests to legacy ports/apps; no service worker remains registered.

### D. Rollback plan
- Revert edits to `apps/web/src/main.tsx`, `apps/web/src/components/layout/AppLayout.tsx`, `apps/web/index.html`, and `apps/web/vite.config.ts`.
- Remove `src/components/BuildBeacon.tsx` and the `diagnostics/` scripts if undesired.
- Rebuild and restart the app.


