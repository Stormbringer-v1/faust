# ADR-003: Scanning Strategy

**Status:** Accepted  
**Date:** 2026-03-14  
**Decision Maker:** ARCHITECT

## Context

Faust needs to scan networks, web apps, cloud infrastructure, and containers.
We must decide: build our own scanners or orchestrate existing tools?

## Decision

**Orchestrate best-of-breed open-source scanners + build only what doesn't exist.**

| Scan Type | Tool | Why |
|-----------|------|-----|
| Network discovery & ports | Nmap | Industry standard, decades of development |
| Web app vulnerabilities | Nuclei (templates) | 8000+ community templates, fast |
| Cloud misconfiguration | Trivy | Covers AWS/GCP/Azure, actively maintained |
| Container images | Trivy | Also handles SBOM and container scanning |
| Custom DAST | Built by us | Nuclei doesn't cover authenticated crawling |

## Architecture

```
Scan Request → Celery Task → Scanner Dispatcher
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
               Nmap Runner   Nuclei Runner   Trivy Runner
                    │              │              │
                    ▼              ▼              ▼
               XML Parser    JSON Parser    JSON Parser
                    │              │              │
                    └──────────────┼──────────────┘
                                   ▼
                           Finding Creator
                                   │
                           ┌───────┼───────┐
                           ▼       ▼       ▼
                       NVD/EPSS  CISA KEV  Risk Score
                       Enrichment          Calculator
```

## Safety Controls

1. **Target validation:** All scan targets validated against `project.allowed_targets` CIDR list
2. **Timeouts:** Each scan has a configurable timeout (default 1 hour)
3. **Concurrency limits:** Max concurrent scans per project (default 5)
4. **Resource limits:** Celery workers have max-tasks-per-child to prevent memory leaks
5. **Scan isolation:** Each scan runs in its own Celery task with clean state
6. **Audit trail:** Every scan records who initiated it and when

## Consequences

- We depend on Nmap, Nuclei, and Trivy being installed in the container
- Scanner updates require container rebuilds
- Custom DAST is our primary differentiator and highest development cost
- Finding deduplication needed when multiple scanners find the same CVE
