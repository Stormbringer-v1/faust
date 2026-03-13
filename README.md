<div align="center">

# 🔥 Faust

### Enterprise-grade vulnerability management. Free. Forever.

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Status](https://img.shields.io/badge/status-early_development-orange)]()

**Faust** is an open source vulnerability management platform that combines the power of enterprise tools like Nessus and Rapid7 with the accessibility of free software — and wraps it in AI-native remediation guidance anyone can understand.

[Getting Started](#getting-started) · [Documentation](./docs) · [Contributing](#contributing) · [Roadmap](#roadmap)

</div>

---

## Why Faust?

The vulnerability management market is broken:

- **Enterprise tools** (Nessus, Rapid7, Qualys) — powerful but cost $3k–$50k+/year
- **Open source tools** (OpenVAS, etc.) — free but complex, ugly, and built only for security experts

**Faust fills the gap**: enterprise-level scanning, beautiful UX, AI-powered remediation, completely free to self-host.

---

## Features

- 🌐 **Network scanning** — Nmap-powered discovery and CVE correlation
- 🕸️ **Web app scanning** — Nuclei templates + custom DAST engine
- ☁️ **Cloud infrastructure** — AWS, GCP, Azure misconfiguration detection (Trivy)
- 🤖 **AI remediation** — Plain-English fix guidance, not just CVE numbers
- 📊 **Smart prioritization** — CVSS + EPSS + CISA KEV risk scoring
- 📄 **Executive reporting** — PDF/HTML reports anyone can understand
- 🔌 **Plugin system** — Community-extensible scanning modules
- 🏠 **Self-hostable** — Single `docker compose up` deployment

---

## Getting Started

```bash
# Clone the repo
git clone https://github.com/yourusername/faust.git
cd faust

# Start with Docker Compose
cp docker/.env.example docker/.env
docker compose -f docker/docker-compose.yml up -d

# Open in browser
open http://localhost:3000
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, Celery, PostgreSQL, Redis |
| Frontend | React, TypeScript, Tailwind CSS |
| Scanning | Nmap, Nuclei, Trivy + Custom DAST Engine |
| AI | Pluggable — OpenAI, Anthropic, Google, or local (Ollama) |
| Infrastructure | Docker, Docker Compose, Kubernetes |

---

## Roadmap

- **Phase 1** — Core platform, network scanning, AI remediation, basic reporting
- **Phase 2** — Web app scanning, cloud scanning, scheduling, notifications
- **Phase 3** — Full DAST engine, RBAC, SSO, compliance reporting
- **Phase 4** — Cloud-hosted SaaS offering

---

## Contributing

Faust is in early development. Contributions are welcome — see [CONTRIBUTING.md](./CONTRIBUTING.md).

---

## License

[AGPL v3](./LICENSE) — Free to use and self-host. SaaS deployments must open source their changes.

