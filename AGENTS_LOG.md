# 📋 AGENTS_LOG — FAUST Project
> Shared work journal. Newest entries at the top.

---

## LATEST STATUS

| Agent | Last Active | Status | Current Focus |
|-------|------------|--------|---------------|
| Claude (COORDINATOR) | 2026-03-14 | ✅ Done | UI/UX Bug Fix & Cleanup Pass |
| Gemini Pro (RAPID-ENG) | 2026-03-14 | ✅ Done | Documentation Sanitization |
| Codex (CODEX-ENG) | 2026-03-14 | ✅ Done | Initial Doc Cleanup |
| Sonnet (BUILDER) | 2026-03-14 | ✅ Done | Task 4.2 — E2E Report Generation |

---

## LOG ENTRIES

---
### BUILDER (Claude Sonnet) — 2026-03-14T21:00Z
**Task:** 4.2 — E2E Report Generation & Download (PDF, HTML, JSON, CSV)
**Status:** ✅ Complete

**Bugs Fixed:**

1. **`reports` queue had no consumer** — `generate_report` task uses `queue="reports"` but the celery-worker was only subscribed to `-Q celery,scans`. No worker ever consumed the queue. Fixed: added `reports` to the celery-worker command: `-Q celery,scans,reports`.

2. **No shared volume for report files** — Reports are written by `celery-worker` to `/app/reports/` but downloaded by the `backend` container. Without a shared mount, the backend always got "file not found". Fixed: added bind-mount `- /var/faust/reports:/app/reports` to both `backend` and `celery-worker` in docker-compose.yml. Host directory created as `chmod 777`.

3. **`AttributeError: 'str' object has no attribute 'value'`** — SQLAlchemy 2.0 returns raw strings for `String(n)` columns, not enum instances. Three call sites in `generator.py` called `.value` on already-string fields:
   - `finding.severity.value` → `sev_key` (str-safe)
   - `finding.status.value` → `sta_key` (str-safe)
   - `asset.asset_type.value` → inline str-safe check
   - `report.report_format.value` in file extension → `fmt` variable (str-safe)

4. **Race condition in `report_service.create_report`** — `flush()` + `dispatch_report_task()` without a prior `commit()` meant the Celery worker could query the report record before the HTTP request's `get_db` dependency committed the transaction. Fixed: added `await db.commit()` before `dispatch_report_task()`.

**E2E Verification:**
- JSON: ✅ completed, downloaded — 4 findings from NmapE2ETest project, correct summary data
- CSV: ✅ completed, downloaded — proper header + rows, 949 bytes
- HTML: ✅ completed, downloaded — `<title>Faust Vulnerability Report</title>` confirmed
- PDF: ✅ completed, downloaded — `%PDF` magic bytes confirmed, 20K WeasyPrint-generated file

**Infrastructure changes:**
- `docker/docker-compose.yml`: added `reports` to celery-worker queue, bind-mount `/var/faust/reports` for both backend and celery-worker
- `backend/app/ai/reporting/generator.py`: fixed 4 `.value` AttributeErrors on SQLAlchemy string columns
- `backend/app/services/report_service.py`: added `await db.commit()` before Celery task dispatch

**What's next:**
- Task 4.6 — AI Remediation E2E Test (BUILDER)
- Tasks 4.3/4.4 — Nuclei/Trivy E2E (CODEX-ENG, needs binary installation)

---
### BUILDER (Claude Sonnet) — 2026-03-14T20:36Z
**Task:** 4.1 — E2E Nmap Scan Pipeline Verification
**Status:** ✅ Complete

**Verification Results:**

The Nmap E2E pipeline was found **already working** — no code changes were needed. Full audit performed:

1. **nmap binary** — present at `/usr/bin/nmap` in both `celery-worker` and `backend` containers ✅
2. **`scan_tasks.py`** — Celery task correctly transitions PENDING → RUNNING → COMPLETED, handles scanner errors gracefully, updates finding/severity counters ✅
3. **`nmap_scanner.py`** — `run()` builds command, executes subprocess, calls `_parse_and_emit()` ✅
4. **`nmap_parser.py`** — XML parsing via `xml.etree.ElementTree`, produces port findings, NSE vuln findings, OS detection findings ✅
5. **`base.py` `_emit_finding()`** — resolves/creates Asset, deduplicates, CVE enriches from Vulnerability table, computes risk_score, persists Finding ✅

**E2E Test Executed:**
- Registered user, created project, POSTed scan (`scan_type=network`, target `172.18.0.1`)
- Celery task `faust.scan.run` received and executed nmap
- 4 findings parsed and stored: SSH (info), HTTP/nginx (info), PostgreSQL (low), Uvicorn/8000 (low)
- `GET /api/v1/projects/{id}/findings/` returned all 4 findings ✅

**Notable (non-blocking):** Nuclei and Trivy binaries not installed — `ScannerError` raised and caught gracefully; scan still completes. These are needed for Tasks 4.3 and 4.4.

**What's next:**
- Task 4.2 — E2E Report Generation & Download (BUILDER)
- Tasks 4.3/4.4 — Install nuclei/trivy binaries in Dockerfile (CODEX-ENG)

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
