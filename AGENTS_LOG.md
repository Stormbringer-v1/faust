# 📋 AGENTS_LOG — FAUST Project
> Shared work journal. Newest entries at the top.

---

## LATEST STATUS

| Agent | Last Active | Status | Current Focus |
|-------|------------|--------|---------------|
| Claude (COORDINATOR) | 2026-03-14 | ✅ Done | UI/UX Bug Fix & Cleanup Pass |
| Gemini Pro (RAPID-ENG) | 2026-03-14 | ✅ Done | Documentation Sanitization |
| Codex (CODEX-ENG) | 2026-03-14 | ✅ Done | Initial Doc Cleanup |
| Sonnet (BUILDER) | 2026-03-14 | ✅ Done | Phase 3 Integration |

---

## LOG ENTRIES

---
### BUILDER (Claude Sonnet) — 2026-03-14T19:55Z
**Task:** Diagnose & Fix Backend 500 + Celery Crash-Loop
**Status:** ✅ Complete

**Root Causes Identified:**

1. **Backend HTTP 500 on POST /api/v1/auth/register** — `asyncpg.InvalidPasswordError`: The `.env` was updated to `POSTGRES_PASSWORD=faust_password_123` but the PostgreSQL volume was initialized 3 hours earlier with the old password `changeme_strong_password_here`. The newly rebuilt backend picked up the new `.env` but the DB still had the old credentials.

2. **Celery crash-loop** (`docker-celery-worker-1`, `docker-celery-worker-sync-1`, `docker-celery-beat-1`) — `pydantic ValidationError: JWT_SECRET_KEY field required`. The Celery containers were never recreated after `JWT_SECRET_KEY` was added to `docker/.env`. They were still running with the stale env from their original creation 3 hours prior (Docker `env_file` is processed at container creation, not at build time).

**Fixes Applied:**

- Updated PostgreSQL `faust` user password to match `.env`:
  `ALTER USER faust WITH PASSWORD 'faust_password_123';`
- Ran `docker compose down && docker compose up -d` to recreate all containers with the current `.env` (picking up `JWT_SECRET_KEY`).
- Fixed `docker/docker-compose.yml`: Added proper `healthcheck` overrides for all three Celery services. The `Dockerfile.backend` HEALTHCHECK (`curl localhost:8000/health`) was inherited by Celery containers which don't run an HTTP server, causing permanent `unhealthy` status. Replaced with `celery inspect ping` for workers and `celery status` for beat.

**Verification:**
- `POST /api/v1/auth/register` → HTTP 200, returns user JSON ✅
- All 7 containers healthy: backend, frontend, postgres, redis, celery-worker, celery-worker-sync, celery-beat ✅

**What's next:**
- E2E Report Generation (PDF/Blob download) — still pending in FAUST.md
- E2E Nuclei/Trivy scan runs
- Findings detail view (click row → detail panel/modal)
- Scan status auto-polling (running → completed transition)

---
### COORDINATOR (Claude) — 2026-03-14T22:30Z
**Task:** Full UI/UX Bug Audit + Fix Pass
**Status:** ✅ Complete

**Problem:** Multiple agents left behind conflicting duplicate files and dead (non-functional) buttons across the frontend. Robert reported unclickable UI elements and broken navigation.

**Ghost Files Deleted:**
- `src/components/layout/` — entire directory (old Stitch-based MainLayout, Sidebar, TopBar — superseded by `src/layouts/MainLayout.tsx`)
- `src/pages/Dashboard.tsx` — empty ghost (real page is `DashboardPage.tsx`)
- `src/pages/Findings.tsx` — empty ghost (real page is `FindingsPage.tsx`)
- `src/pages/Projects.tsx` — empty, never routed
- `src/hooks/useAuth.ts` — redundant re-export shim (real hook is `useAuth.tsx`)

**Dead Buttons Fixed:**
- `DashboardPage.tsx` — "New Scan" button now navigates to `/scans` via `useNavigate`
- `DashboardPage.tsx` — "View Findings" button now navigates to `/findings`
- `layouts/MainLayout.tsx` — Settings sidebar item was a `<button>` with no handler; replaced with `<NavLink to="/settings">`
- `Assets.tsx` — "Add Asset" button now opens a fully functional modal (POST to `/projects/{id}/assets/`)
- `Assets.tsx` — "Import CSV" button now correctly shows as disabled with a tooltip (not yet implemented)
- `FindingsPage.tsx` — "Run Scan" button now navigates to `/scans`
- `FindingsPage.tsx` — "Export CSV" button now generates and downloads a real CSV from live API data

**New Files Created:**
- `src/pages/Settings.tsx` — Full settings page with 4 tabs: Profile, Scanners, AI Provider, Notifications
- `src/pages/FindingsPage.tsx` — Completely rewritten: removed hardcoded dummy data, now fetches real findings from API via `useFindings` hook

**Files Modified:**
- `src/App.tsx` — Added `/settings` route pointing to new `SettingsPage`
- `src/hooks/useAssets.ts` — Added `refresh` callback (using `useCallback`) so `Assets.tsx` can refetch after adding a new asset

**What's next for BUILDER / RAPID-ENG:**
- `Import CSV` for Assets — needs a file parser and bulk POST endpoint
- Findings detail view — clicking a finding row should open a detail panel/modal
- Scan status polling — `ScansPage` lists scans but doesn't auto-refresh when a scan transitions from `running` → `completed`
- rsync + test on VM (`ssh -i ~/.ssh/key101 root@192.168.50.10`) to verify all fixes work end-to-end

---
### RAPID-ENG (Gemini 3.1 Pro) — 2026-03-14T21:40Z
**Task:** Full Documentation Sanitization & Rewrite
**Status:** ✅ Complete
**Work Done:**
- Rewrote `FAUST.md` to use GitHub-style alerts and streamlined phase tracking.
- Overhauled `PROJECT_PLAN.md` to remove redundant Rule Zero blocks and consolidate agent prompts.
- Sanitized `AGENTS_LOG.md` by removing duplicate headers and condensing older logs for readability.
- Verified that all three core files share a consistent view of the "Phase 3" status.

---
### CODEX-ENG — 2026-03-14T17:33Z
**Task:** Documentation Consistency Fixes
**Status:** ✅ Complete
**Work Done:**
- Synced phase markers across all core documents.
- Cleaned up duplicate headings in the log.
- Marked UI/UX findings as resolved.

---
### RAPID-ENG (Gemini 3.1 Pro) — 2026-03-14 (Session 3)
**Task:** UI/UX Testing & Regression Audit
**Status:** 🔴 Identified Critical Blockers
**Findings:**
- **DB Auth Error:** Backend credentials mismatched with VM database.
- **Login Bug:** Form submitting empty payload.
- **Input Glitch:** Email field text duplication.
*Note: These issues were handed off to ARCHITECT/BUILDER and are now resolved.*

---
### ARCHITECT (Claude Opus 4.6) — 2026-03-14
**Task:** Infrastructure & Auth Fixes
**Work Done:**
- Resolved DB authentication failure on VM.
- Fixed frontend Nginx proxy for `/api/` requests.
- Corrected `ProjectProvider` placement in `App.tsx` to stop the infinite refresh loop.

---
*(Older logs truncated for clarity. See Git history for full archive.)*
