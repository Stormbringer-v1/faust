# 🛡️ FAUST — Project Plan
> **VM Reference:** `192.168.50.10` | Backend: `http://192.168.50.10:8000`

---

## 🚨 RULE ZERO
**NOTHING RUNS LOCALLY.** 
1. Edit code here.
2. `rsync` to VM.
3. Run `docker compose`, `npm`, or `pytest` on the VM.

---

## 🤖 AGENT ROSTER

| Role | Tool | Focus | Status |
|---|---|---|---|
| **ARCHITECT** | Claude Opus | Security, Architecture, DB Models | 🟢 Active |
| **BUILDER** | Claude Sonnet | Integration, API, Complex Logic | 🟢 Active |
| **RAPID-ENG** | Gemini Pro | Frontend, Quick Transitions, Scaffolding | 🟢 Active |
| **CODEX-ENG** | Codex | Parallel tasks, Parsing, Data | 🟢 Active |

---

## 🎯 CURRENT ASSIGNMENTS (PHASE 3)

### Priority 1: Integration (Core Flows)
- [x] **Task 3.1 — Auth & Storage:** Wired `useAuth` hook and Axios instance with JWT refresh.
- [x] **Task 3.2 — Dashboard Data:** Fetching real stats (Severity, Risk, Assets) from FastAPI.
- [x] **Task 3.3 — Asset & Scan Management:** Functional UI for Inventory and Scan triggers.

### Priority 3: UI/UX & Auth Fixes (NEW)
- [ ] **Task 3.7 — Auth Input Visibility:** Add `text-slate-900` to Input components in `Login.tsx` and ensure labels/placeholders have correct contrast.
- [ ] **Task 3.8 — Database Auth Sync:** Resolve `InvalidPasswordError` by manually aligning the DB user password with the `.env` file on the VM.

---

## 🔍 RESOLVED CRITICAL ISSUES
- **Auth Fix (2026-03-14):** Fixed DB password mismatch (`InvalidPasswordError`) and Login form empty payload bug.
- **Layout Fix (2026-03-14):** Constrained dashboard horizontal sprawl and aligned Project Selector.
- **Theme Fix (2026-03-14):** Definied `brand` palette in `index.css` to fix invisible Primary buttons.

---

## 📝 AGENT PROMPT TEMPLATE
*When starting a session, copy this into your prompt:*

```text
You are [ROLE] on Project FAUST.
1. Read FAUST.md (Mission Control).
2. Read AGENTS_LOG.md (Recent History).
3. Read PROJECT_PLAN.md (Current Task).
4. Work ONLY in the local directory.
5. Record your session in AGENTS_LOG.md.
```
