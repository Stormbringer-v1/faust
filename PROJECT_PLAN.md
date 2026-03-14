# FAUST — Project Plan (Phase 4: E2E Validation & Polish)
> **Architect:** Claude Opus | **Last Updated:** 2026-03-14
> **VM:** `192.168.50.10` | **Backend:** `http://192.168.50.10:8000`
> **Rollback point:** `git checkout stable-baseline` or `git reset --hard v0.1.0-stable`

---

## RULE ZERO
**NOTHING RUNS LOCALLY.**
1. Edit code in the local directory.
2. `rsync -avz -e "ssh -i ~/.ssh/key101" ~/Documents/antigravity/vuln-scanner/ root@192.168.50.10:/root/faust/`
3. SSH to VM and run `docker compose`, `pytest`, etc.

---

## AGENT ROSTER

| Role | Agent | Strengths | Use For |
|------|-------|-----------|---------|
| **ARCHITECT** | Claude Opus | System design, security, code review, debugging | Task design, reviews, complex debugging |
| **BUILDER** | Claude Sonnet | Fast, reliable code generation | Backend logic, integrations, complex features |
| **RAPID-ENG** | Gemini CLI | Frontend, quick scaffolding | React pages, UI components, CSS |
| **CODEX-ENG** | Codex | Parallel batch work | Parsers, data transforms, test files |
| **FLEX-ENG** | OpenCode (free) | Simple edits, boilerplate | Config files, simple fixes, docs |

---

## COMPLETED PHASES

<details>
<summary>Phase 1-3 (click to expand)</summary>

- [x] Backend API & Database Schema (7 models, full CRUD)
- [x] JWT Auth with refresh tokens, RBAC (admin/analyst/viewer)
- [x] Multi-scanner framework (Nmap/Nuclei/Trivy base classes + parsers)
- [x] AI remediation engine (4 providers, Redis cache, fallback chain)
- [x] Report generator (PDF/HTML/JSON/CSV renderers)
- [x] Celery infrastructure (scan/report/sync tasks, Beat scheduler)
- [x] Frontend: Auth, Dashboard, Assets, Scans, Findings, Reports, Settings pages
- [x] All pages wired to real API (no dummy data except 2 dashboard widgets)
- [x] Docker Compose: all 7 containers healthy
- [x] Infra fixes: DB auth, Celery env, healthchecks

</details>

---

## PHASE 4 — ACTIVE TASK BOARD

### P0: Core E2E Flows (Must work before anything else)

| ID | Task | Assigned To | Status | Depends On |
|----|------|-------------|--------|------------|
| 4.1 | E2E Nmap Scan Pipeline | BUILDER | `TODO` | — |
| 4.2 | E2E Report Generation & Download | BUILDER | `TODO` | 4.1 |
| 4.3 | Nuclei Scanner E2E | CODEX-ENG | `TODO` | 4.1 |
| 4.4 | Trivy Scanner E2E | CODEX-ENG | `TODO` | 4.1 |

### P1: Data Pipeline & Enrichment

| ID | Task | Assigned To | Status | Depends On |
|----|------|-------------|--------|------------|
| 4.5 | Vuln DB Sync (NVD/EPSS/KEV) | CODEX-ENG | `TODO` | — |
| 4.6 | AI Remediation E2E Test | BUILDER | `TODO` | 4.1 |

### P2: Frontend Polish

| ID | Task | Assigned To | Status | Depends On |
|----|------|-------------|--------|------------|
| 4.7 | Finding Detail View (click row -> panel) | RAPID-ENG | `TODO` | 4.1 |
| 4.8 | Scan Status Auto-Polling | RAPID-ENG | `TODO` | 4.1 |
| 4.9 | Dashboard: Real RiskTrendChart | RAPID-ENG | `TODO` | 4.1 |
| 4.10 | Dashboard: Real RecentActivity | RAPID-ENG | `TODO` | 4.1 |

### P3: Nice-to-Have

| ID | Task | Assigned To | Status | Depends On |
|----|------|-------------|--------|------------|
| 4.11 | Settings Page API Integration | FLEX-ENG | `TODO` | — |
| 4.12 | CSV Import for Assets | CODEX-ENG | `TODO` | — |
| 4.13 | Auth Input Contrast Fix | FLEX-ENG | `TODO` | — |

---

## TASK PROMPTS

Copy the relevant prompt below when launching an agent. Each prompt is self-contained.

---

### TASK 4.1 — E2E Nmap Scan Pipeline (BUILDER)

```text
You are BUILDER on Project FAUST — an open-source vulnerability management platform.

READ THESE FILES FIRST (in order):
1. FAUST.md — project overview
2. AGENTS_LOG.md — recent work history
3. PROJECT_PLAN.md — your task assignment

YOUR TASK: Verify and fix the end-to-end Nmap scan pipeline.

The flow is: POST /api/v1/projects/{id}/scans/ → Celery task `faust.scan.run` →
NmapScanner runs nmap binary → NmapParser parses XML output → findings saved to DB
→ GET /api/v1/projects/{id}/findings/ returns them.

STEPS:
1. Read these files to understand the scan flow:
   - backend/app/services/tasks/scan_task.py (Celery task)
   - backend/app/services/scanners/base.py (BaseScanner + _emit_finding)
   - backend/app/services/scanners/nmap_scanner.py (NmapScanner)
   - backend/app/services/scanners/parsers/nmap_parser.py (XML parsing)

2. Check if nmap is installed in the backend Docker container:
   SSH: ssh -i ~/.ssh/key101 root@192.168.50.10
   Then: docker exec docker-backend-1 which nmap
   And:  docker exec docker-celery-worker-1 which nmap

3. Create a test scan via the API (from the VM):
   - First register/login to get a token
   - Create a project with allowed_targets
   - Add an asset
   - POST a scan with scan_type=network targeting localhost or the VM itself (192.168.50.10)
   - Watch celery worker logs: docker logs -f docker-celery-worker-1

4. If the scan fails, read the traceback and fix the code. Common issues:
   - nmap binary not found or wrong path
   - XML output parsing errors
   - Database session handling in async context
   - Finding emission failures

5. Verify findings appear in the database after scan completes.

RULES:
- Do NOT run anything locally. Edit files locally, rsync to VM, run on VM via SSH.
- After code changes: rsync then `docker compose build backend celery-worker && docker compose up -d`
- Log your work in AGENTS_LOG.md when done.

GIT SAFETY: Current working state is tagged v0.1.0-stable. Do not force-push or rebase.
```

---

### TASK 4.2 — E2E Report Generation & Download (BUILDER)

```text
You are BUILDER on Project FAUST.

READ FIRST: FAUST.md, AGENTS_LOG.md, PROJECT_PLAN.md

YOUR TASK: Verify and fix end-to-end report generation (PDF, HTML, JSON, CSV).

PREREQUISITE: Task 4.1 must be complete (need findings in DB to generate reports).

The flow is: POST /api/v1/projects/{id}/reports/ → Celery task `faust.report.generate`
→ ReportGenerator queries findings/assets → renders to file → GET .../reports/{id}/download
returns the file.

STEPS:
1. Read these files:
   - backend/app/services/tasks/report_task.py
   - backend/app/ai/reporting/generator.py (ReportGenerator)
   - backend/app/api/v1/endpoints/reports.py (download endpoint)
   - backend/app/templates/report.html (Jinja2 template for HTML/PDF)

2. Test each format (JSON first, then CSV, HTML, PDF):
   - POST /api/v1/projects/{id}/reports/ with {"title": "Test", "report_format": "json"}
   - Poll GET /api/v1/projects/{id}/reports/{id} until status=completed
   - GET /api/v1/projects/{id}/reports/{id}/download — verify file downloads

3. PDF requires WeasyPrint. Check it works in the container:
   docker exec docker-celery-worker-1 python -c "import weasyprint; print('OK')"

4. Fix any issues found. Common problems:
   - Missing /app/reports/ directory in container
   - WeasyPrint missing system dependencies (pango, cairo, fontconfig)
   - Template rendering errors
   - File path mismatches between generator and download endpoint

RULES: Same as Task 4.1. Log work in AGENTS_LOG.md.
```

---

### TASK 4.7 — Finding Detail View (RAPID-ENG)

```text
You are RAPID-ENG on Project FAUST — a vulnerability management platform.

READ FIRST: FAUST.md, AGENTS_LOG.md, PROJECT_PLAN.md

YOUR TASK: Add a finding detail panel to FindingsPage.tsx.

When a user clicks a finding row in the findings table, a slide-over panel (or modal)
should appear showing full details:

PANEL CONTENTS:
- Title, severity badge, status badge
- Description (full text)
- CVE ID (linked to NVD if present), CWE ID
- CVSS score + vector string
- EPSS score + percentile (if available)
- CISA KEV status (boolean badge)
- Risk score (0-100, color-coded)
- Scanner name + rule ID
- Evidence (JSON, rendered as key-value pairs)
- AI Remediation (markdown, rendered)
- Triage section: current status, triaged_by, triage_notes
- Button: "Request AI Remediation" → POST /api/v1/projects/{id}/findings/{id}/remediation
- Button: "Update Triage" → PATCH /api/v1/projects/{id}/findings/{id}/triage

The API already returns all these fields from GET /api/v1/projects/{id}/findings/{findingId}.

IMPLEMENTATION:
- Add a new component: src/components/findings/FindingDetailPanel.tsx
- Use Tailwind CSS for styling (slide-over from right side, like a drawer)
- Fetch full finding data when panel opens (the list endpoint may not include all fields)
- Use the existing axios client from src/services/api.ts

STYLE: Match the existing dark theme (slate/gray backgrounds, brand-blue accents).
Do NOT install new UI libraries. Use plain Tailwind.

RULES:
- Edit files locally only. Do not run npm/docker commands.
- Log your work in AGENTS_LOG.md.
```

---

### TASK 4.8 — Scan Status Auto-Polling (RAPID-ENG)

```text
You are RAPID-ENG on Project FAUST.

READ FIRST: FAUST.md, AGENTS_LOG.md, PROJECT_PLAN.md

YOUR TASK: Add auto-polling to the Scans page so running scans update in real-time.

CURRENT STATE: src/pages/Scans.tsx fetches scans once on mount via useScans hook.
If a scan is PENDING or RUNNING, the user must manually refresh to see updates.

IMPLEMENTATION:
1. In src/hooks/useScans.ts, add a polling interval (every 5 seconds) that activates
   ONLY when there are scans with status "pending" or "running".
2. When all scans are completed/failed/cancelled, stop polling.
3. Use setInterval + cleanup in useEffect. No external libraries.
4. Show a subtle pulsing indicator next to running scans in the UI.

RULES: Edit locally only. Log work in AGENTS_LOG.md.
```

---

### TASK 4.5 — Vuln DB Sync Verification (CODEX-ENG)

```text
You are CODEX-ENG on Project FAUST.

READ FIRST: FAUST.md, AGENTS_LOG.md, PROJECT_PLAN.md

YOUR TASK: Verify and fix the vulnerability database sync tasks (NVD, EPSS, CISA KEV).

These are Celery Beat scheduled tasks that populate the `vulnerability` table:
- faust.sync.nvd — fetches CVEs from NVD API (every 6 hours)
- faust.sync.epss — fetches EPSS scores (daily at 06:00 UTC)
- faust.sync.cisa_kev — fetches CISA KEV catalog (every 4 hours)

STEPS:
1. Read these files:
   - backend/app/vuln_db/sync/scheduler.py (Beat schedule config)
   - backend/app/vuln_db/sync/nvd.py (NVD sync logic)
   - backend/app/vuln_db/sync/epss.py (EPSS sync logic)
   - backend/app/vuln_db/sync/kev.py (CISA KEV sync logic)
   - backend/app/services/tasks/sync_tasks.py (Celery task wrappers)

2. Test each sync task manually on the VM:
   docker exec docker-celery-worker-sync-1 celery -A app.services.celery_app call faust.sync.cisa_kev
   Then check: docker logs docker-celery-worker-sync-1 --tail 30

3. Verify data lands in the vulnerability table:
   docker exec docker-postgres-1 psql -U faust -c "SELECT COUNT(*) FROM vulnerability;"

4. Fix any issues (HTTP client errors, schema mismatches, missing fields).

RULES: Edit locally, rsync to VM, test on VM. Log work in AGENTS_LOG.md.
```

---

## RESOLVED ISSUES (Archive)

- **2026-03-14:** DB password mismatch (`InvalidPasswordError`) — synced via ALTER USER
- **2026-03-14:** Celery crash-loop — `JWT_SECRET_KEY` missing from container env, fixed by recreating containers
- **2026-03-14:** Celery false-unhealthy — Dockerfile HEALTHCHECK inherited by workers, overridden in docker-compose.yml
- **2026-03-14:** Login form empty payload, layout sprawl, invisible buttons — all fixed
- **2026-03-14:** Ghost files deleted (old layout dir, empty page stubs, redundant hook shim)
