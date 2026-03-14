# ADR-001: License — AGPL v3

**Status:** Accepted  
**Date:** 2026-03-14  
**Decision Maker:** ARCHITECT

## Context

Faust is an open-source vulnerability management platform that will compete 
with commercial tools (Nessus, Rapid7, Qualys). We need a license that:
1. Keeps the project free for self-hosting
2. Prevents proprietary forks from SaaS companies
3. Encourages community contributions

## Decision

Use **GNU Affero General Public License v3 (AGPL-3.0)**.

## Rationale

- **AGPL vs GPL:** Standard GPL has a "SaaS loophole" — companies can modify 
  the code and offer it as a service without releasing their changes. 
  AGPL closes this by requiring source code disclosure for network use.
- **AGPL vs MIT/Apache:** Permissive licenses would allow proprietary forks 
  that compete with the community version without contributing back.
- **Precedent:** Grafana, MongoDB, and GitLab CE all use AGPL or similar 
  copyleft licenses for their open-source offerings.

## Consequences

- SaaS deployments must open-source their changes
- Enterprise customers who want proprietary modifications may request 
  a commercial license (future revenue stream)
- Contributors must agree to CLA or DCO
