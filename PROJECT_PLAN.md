# 🛡️ FAUST — Project Plan & Agent Prompts
> **Project:** FAUST — Free & Autonomous Universal Security Tool
> **Type:** Open-source, enterprise-grade vulnerability management platform
> **Date:** 2026-03-14
> **Codename:** FAUST
> **VM:** `192.168.50.10` — backend live at `http://192.168.50.10:8000`

---

## 🚨 RULE ZERO — READ THIS FIRST 🚨

> **NOTHING EXECUTES ON THE LOCAL LAPTOP. EVER. NO EXCEPTIONS.**
> 
> ### The Workflow:
> 
> 1. **EDIT code locally** at `/Users/robertharutyunyan/Documents/antigravity/vuln-scanner` (via Antigravity IDE, Claude Code CLI, Gemini CLI, Codex, or any editor)
> 2. **rsync to VM** (`192.168.50.10`) for all execution
> 3. **Push to GitHub** for version control
> 
> ### What happens ONLY ON THE VM (never local):
> 
> - `docker-compose up`, any Docker commands
> - `pip install`, `npm install`, `npm run dev`
> - `pytest`, any test execution
> - `nmap`, `nuclei`, `trivy`, any scanning
> - Database operations, migrations, Celery workers
> - ANY process execution, compilation, or build step
> 
> **If an agent suggests `docker-compose up` or `pytest` locally — STOP. rsync first, run on VM.**

---

## 🤖 TOOLCHAIN & AGENT ROSTER

### ⚠️ Current Agent Availability (Rate Limits)
- **Active Now:** All agents are currently active and available.

### Roster
| Agent | Tool | Primary Role | Status |
|---|---|---|---|
| **Claude Opus 4.6** | Claude Code CLI | **ARCHITECT** — Security-critical code, engine design, DB models | 🟢 ACTIVE |
| **Claude Sonnet 4.6**| Claude Code CLI | **BUILDER** — Core integration, APIs, complex implementations | 🟢 ACTIVE |
| **Gemini 3.1 Pro** | Antigravity IDE / Gemini CLI | **RAPID-ENG** — Frontend scaffolding, quick fixes, bulk generation, Python wiring | 🟢 ACTIVE |
| **Codex 5.2** | OpenAI CLI | **CODEX-ENG** — Targeted coding tasks, parallel execution, parsing, templates | 🟢 ACTIVE |

**How to work with this plan:**
You go to an agent, tell them to read `FAUST.md`, `AGENTS_LOG.md`, and `PROJECT_PLAN.md`. They find their prompt below, do their assigned task, update `AGENTS_LOG.md`, update this plan if needed, and tell you which agent to go to next.

---

## 📋 AGENT PROMPTS — COPY AND PASTE

### For ARCHITECT (Claude Opus 4.6)
```text
You are ARCHITECT working on Project FAUST — an open-source, enterprise-grade vulnerability management platform.

## MANDATORY FIRST STEPS
1. Read `FAUST.md` — project spec and source of truth
2. Read `AGENTS_LOG.md` — shared work journal
3. Read `PROJECT_PLAN.md` (this file) — find your current assigned task below.

## PROJECT LOCATION
- Local: /Users/robertharutyunyan/Documents/antigravity/vuln-scanner
- VM: 192.168.50.10 → /root/faust (via rsync)

## 🚨 RULE ZERO
You are in the LOCAL project directory. You CAN create and edit files here.
You CANNOT run anything here — no docker, no pytest. All execution happens on the VM after rsync.

## YOUR IMMEDIATE TASK
Look in the "CURRENT ASSIGNMENTS" section below for any tasks tagged `ARCHITECT`.

## AFTER COMPLETING WORK
1. Append your session log to `AGENTS_LOG.md`.
2. Update the checkboxes in `PROJECT_PLAN.md`.
3. Inform the human exactly what to do next.
```

### For BUILDER (Claude Sonnet 4.6)
```text
You are BUILDER working on Project FAUST.

## MANDATORY FIRST STEPS
1. Read `FAUST.md`
2. Read `AGENTS_LOG.md`
3. Read `PROJECT_PLAN.md`

## PROJECT LOCATION
- Local: /Users/robertharutyunyan/Documents/antigravity/vuln-scanner
- VM: 192.168.50.10 → /root/faust (via rsync)

## 🚨 RULE ZERO
You are in the LOCAL project directory. You CAN create and edit files here.
You CANNOT run anything here — no docker, no pytest. All execution happens on the VM after rsync.

## YOUR IMMEDIATE TASK
Look in the "CURRENT ASSIGNMENTS" section below for any tasks tagged `BUILDER`.

## AFTER COMPLETING WORK
1. Append your session log to `AGENTS_LOG.md`.
2. Update the checkboxes in `PROJECT_PLAN.md`.
3. Inform the human exactly what to do next.
```

### For RAPID-ENG (Gemini 3.1 Pro)
```text
You are RAPID-ENG working on Project FAUST — an open-source, enterprise-grade vulnerability management platform.

## MANDATORY FIRST STEPS
1. Read `FAUST.md` — project spec and source of truth
2. Read `AGENTS_LOG.md` — shared work journal
3. Read `PROJECT_PLAN.md` (this file) — find your current assigned task below under YOUR RESPONSIBILITIES.
4. Do NOT overwrite existing files without checking what others have done in AGENTS_LOG.

## PROJECT LOCATION
- Local: /Users/robertharutyunyan/Documents/antigravity/vuln-scanner
- VM: 192.168.50.10 → /root/faust (via rsync)

## 🚨 RULE ZERO
You are in the LOCAL project directory. You CAN create and edit files here.
You CANNOT run anything here — no docker, no pytest. All execution happens on the VM after rsync.

## CURRENT STATE
- Phase 2 core backend/AI logic is complete. Frontend basic scaffolding complete.
- We need API integration between the React frontend and FastAPI backend, and end-to-end testing (Phase 3).

## YOUR IMMEDIATE TASK (from Current Assignments)
Look in the "CURRENT ASSIGNMENTS" section below for any tasks tagged `RAPID-ENG`.

## AFTER COMPLETING WORK
1. Append your session log to `AGENTS_LOG.md`.
2. Update the checkboxes in `PROJECT_PLAN.md`.
3. Inform the human exactly what to do next (e.g., "rsync to VM and run alembic upgrade head") and WHICH AGENT they should use next for the next task on the list.
```

### For CODEX-ENG (Codex 5.2)
```text
You are CODEX-ENG working on Project FAUST — an open-source, enterprise-grade vulnerability management platform.

## MANDATORY FIRST STEPS
1. Read `FAUST.md` — project spec and source of truth
2. Read `AGENTS_LOG.md` — shared work journal
3. Read `PROJECT_PLAN.md` (this file) — find your current assigned task below under YOUR RESPONSIBILITIES.
4. Do NOT overwrite existing files without checking what others have done in AGENTS_LOG.

## PROJECT LOCATION
- Local: /Users/robertharutyunyan/Documents/antigravity/vuln-scanner
- VM: 192.168.50.10 → /root/faust (via rsync)

## 🚨 RULE ZERO
You are in the LOCAL project directory. You CAN create and edit files here.
You CANNOT run anything here — no docker, no pytest. All execution happens on the VM after rsync.

## YOUR IMMEDIATE TASK (from Current Assignments)
Look in the "CURRENT ASSIGNMENTS" section below for any tasks tagged `CODEX-ENG`.

## AFTER COMPLETING WORK
1. Append your session log to `AGENTS_LOG.md`.
2. Update the checkboxes in `PROJECT_PLAN.md`.
3. Inform the human exactly what to do next and WHICH AGENT they should use next for the next task.
```

*(ARCHITECT and BUILDER prompts are temporarily hidden to reduce file size until their 3-hour timeout is over. When they return, re-add them here).*

---

## 🎯 CURRENT ASSIGNMENTS (PHASE 3: INTEGRATION & E2E)

The following tasks are active. Agents should claim their assigned task, complete it, check it off, and then hand over the session to the human, specifying who the human should use next.

### Priority 1: Frontend API Integration
- [x] **Task 3.1 — Axios & Auth Wiring (`RAPID-ENG`)**
  - **Location:** `frontend/src/services/api.ts` and `frontend/src/hooks/useAuth.ts`
  - **Goal:** Set up an Axios instance configured to point to `/api/v1` (with proxy in vite.config.ts). Implement real login/logout and token storage in `useAuth.ts`.

- [x] **Task 3.2 — Dashboard Data (`RAPID-ENG`)**
  - **Location:** `frontend/src/pages/DashboardPage.tsx` and related hooks
  - **Goal:** Fetch real data for `SeverityDonut`, `RiskTrendChart`, and `TopAssetsTable` via real FastAPI endpoints. 

### Priority 2: Remaining UI Screens
- [x] **Task 3.3 — Asset Inventory & Scan Config (`RAPID-ENG` or `CODEX-ENG`)**
  - **Location:** `frontend/src/pages/Assets.tsx` and `frontend/src/pages/Scans.tsx`
  - **Goal:** Implement the Asset Inventory and New Scan screens based on Stitch exports. Hook them up to the backend.

### Priority 3: End-to-End Testing
- [ ] **Task 3.4 — E2E Scan Execution (`BUILDER` or `CODEX-ENG`)**
  - **Goal:** Trigger a real scan from the frontend UI on a demo target (e.g. juice-shop). Verify the Celery worker picks it up, runs scanners, and findings appear in the database. Ensure AI remediation is generated.

- [ ] **Task 3.5 — Report Generation Verification (`BUILDER` or `CODEX-ENG`)**
  - **Goal:** Request a PDF report from the UI, ensure the WeasyPrint renderer generates it correctly, and the file downloads successfully to the client.
