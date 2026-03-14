# 🔥 FAUST — Mission Control
> Every agent reads this file first. No exceptions.
> Last Updated: 2026-03-14

---

## What is Faust?

An open source, enterprise-grade vulnerability management platform.
Think Nessus / Rapid7 quality — completely free to self-host, AI-native.

**The Gap:** Security tools are either unaffordably expensive (Nessus/Rapid7) or unusable for non-experts (OpenVAS). Faust provides a premium, automated experience for everyone.

---

## Environments

| Location | Path | Access | Role |
|---|---|---|---|
| Local (Mac) | `/Users/robertharutyunyan/Documents/antigravity/vuln-scanner` | Direct | Code Editing & Coordination |
| Linux VM | `/root/faust` on `192.168.50.10` | `ssh -i ~/.ssh/key101 root@192.168.50.10` | Execution, Building & Testing |

> [!IMPORTANT]
> **RULE ZERO:** No execution occurs on the local machine. All `docker`, `npm`, `pip`, and `pytest` commands must run on the VM after an `rsync`.

---

## Tech Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy (async), Celery, Redis, PostgreSQL
- **Frontend:** React + TypeScript + Tailwind CSS
- **Scanners:** Nmap, Nuclei, Trivy (Custom DAST engine in progress)
- **AI:** Multi-provider (OpenAI, Anthropic, Google, local Ollama)
- **Infrastructure:** Docker Compose

---

## Current Status: Phase 3 — Integration & E2E Validation

### ✅ Milestone 1: Foundation & Core Engine
- [x] Backend API & Database Schema
- [x] AI Remediation & Triage Engines
- [x] Multi-Scanner Support (Nmap/Nuclei/Trivy)
- [x] Frontend Scaffolding & Design System

### 🔄 Milestone 2: Integration & E2E (Active)
- [x] Frontend Auth & API Wiring
- [x] Dashboard Data Fetching
- [x] Asset Inventory & Scan Management
- [x] E2E Nmap Scan Pipeline (API → Celery → DB)
- [ ] E2E Report Generation (PDF/Blob download)
- [ ] E2E Nuclei/Trivy runs

---

## Key Files

| File | Purpose |
|---|---|
| [FAUST.md](file:///Users/robertharutyunyan/Documents/antigravity/vuln-scanner/FAUST.md) | Strategic overview and mission control |
| [PROJECT_PLAN.md](file:///Users/robertharutyunyan/Documents/antigravity/vuln-scanner/PROJECT_PLAN.md) | Active task tracking and agent prompts |
| [AGENTS_LOG.md](file:///Users/robertharutyunyan/Documents/antigravity/vuln-scanner/AGENTS_LOG.md) | Chronological work journal |

---
*This file is the single source of truth for the project. Keep it precise.*
