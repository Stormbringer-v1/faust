# 🔥 FAUST — Mission Control
> Every agent reads this file first. No exceptions.
> Last Updated: 2026-03-14

---

## What is Faust?

An open source, enterprise-grade vulnerability management platform.
Think Nessus / Rapid7 quality — completely free to self-host, AI-native.

**The gap we fill:** Everything that exists is either unaffordably expensive or unusably complex. We own the middle.

---

## Environments

| Location | Path | Access |
|---|---|---|
| Local machine (Mac) | `/Users/robertharutyunyan/Documents/antigravity/vuln-scanner` | Direct |
| Linux VM | `/root/faust` on `192.168.50.10` | `ssh -i ~/.ssh/key101 root@192.168.50.10` |
| GitHub | TBD — repo not yet created | — |

> **Rule:** All code runs and is tested on the VM. Local machine is for planning, design, and agent coordination only.

---

## Tech Stack (Locked)

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy (async), Celery, Redis, PostgreSQL |
| Frontend | React + TypeScript + Tailwind CSS |
| Scanning | Nmap, Nuclei, Trivy + Custom DAST engine (built by us) |
| AI | Pluggable — OpenAI / Anthropic / Google / local Ollama |
| Deploy | Docker Compose (self-hosted), Kubernetes (cloud SaaS later) |
| License | AGPL v3 |

---

## AI Agent Roster

| Agent | Tool | Primary Role |
|---|---|---|
| **Gemini 3.1 Pro** | Antigravity IDE / Gemini CLI | RAPID-ENG — Frontend, overall orchestration, scaffolding, logic implementation |
| **Codex 5.2** | OpenAI CLI | CODEX-ENG — Targeted coding tasks, parallel execution, integrations |

---

## Current Phase

### ✅ Done
- [x] Project named: **Faust**
- [x] License decided: **AGPL v3**
- [x] Tech stack decided
- [x] Architecture document created (`Faust-Architecture.md` in Obsidian)
- [x] Project plan initialized (`PROJECT_PLAN.md`)
- [x] Bootstrap script created (`bootstrap.sh`)
- [x] **Phase 1 — Foundation:** FastAPI app, DB, Auth, Core data models
- [x] **Phase 2 — Core Engine:** Scanners (Nmap/Nuclei/Trivy), AI remediation, UI scaffolding, NVD sync

### 🔄 In Progress
- [ ] Phase 3 — Integration & E2E Validation

### ⏳ Up Next (Phase 3)
- [ ] Connect React frontend hooks to FastAPI backend
- [ ] Build remaining UI screens (Assets Inventory, Scan Config, Remediation Details)
- [ ] E2E testing: trigger real scan, ensure DB population, check AI remediation
- [ ] Render and download PDF reports from UI

---

## Key Decisions (Never Revisit Without Good Reason)

| Decision | Choice | Reason |
|---|---|---|
| License | AGPL v3 | SaaS forks must open source their changes |
| Scanning strategy | Orchestrate best tools + custom DAST | Don't reinvent Nmap/Nuclei/Trivy |
| Vuln prioritization | CVSS + EPSS + CISA KEV combined | Smarter than raw CVSS alone |
| AI backend | Pluggable (no vendor lock-in) | Privacy, flexibility, local model support |
| MVP demo target | DVWA / Juice Shop (intentionally vulnerable apps) | Safe, legal, purpose-built for testing |
| Frontend design | Google Stitch mockups before implementation | Lock UX before coding |

---

## How to Work on Faust

1. **Read this file** (`FAUST.md`) — understand current state
2. **Read `AGENT_LOG.md`** — see what was last done
3. **Follow the direction in `PROJECT_PLAN.md`**
4. **Append your session summary** to `AGENT_LOG.md`
5. **Update this file** if phase status changes

---

## Important Files

| File | Location | Purpose |
|---|---|---|
| `FAUST.md` | vuln-scanner/ (this file) | Strategic overview — read first |
| `AGENT_LOG.md` | vuln-scanner/ | Detailed agent activity log |
| `PROJECT_PLAN.md` | vuln-scanner/ | Evolving project plan and agent assignment tracker |
| `Faust-Architecture.md` | Obsidian vault | Full architecture document |
| `bootstrap.sh` | vuln-scanner/ | VM repo scaffolding script |

---

*This file is the single source of truth for project status. Keep it current.*
