# Faust — Data Model

> Last Updated: 2026-03-14 by ARCHITECT

## Entity Relationship Diagram

```
┌──────────┐
│   User   │
│──────────│
│ id (PK)  │
│ email    │◄───────────────────────┐
│ role     │                        │
│ ...      │                        │
└────┬─────┘                        │
     │ 1:N (owner)                  │ N:1 (triaged_by)
     ▼                              │
┌──────────┐                        │
│ Project  │                        │
│──────────│                        │
│ id (PK)  │                        │
│ owner_id │──▶ User                │
│ name     │                        │
│ allowed_ │                        │
│ targets  │                        │
└─┬──┬──┬──┘                        │
  │  │  │                           │
  │  │  │ 1:N                       │
  │  │  └────────────┐              │
  │  │               ▼              │
  │  │         ┌──────────┐         │
  │  │         │  Report  │         │
  │  │         │──────────│         │
  │  │         │ id (PK)  │         │
  │  │         │ format   │         │
  │  │         │ status   │         │
  │  │         └──────────┘         │
  │  │                              │
  │  │ 1:N                          │
  │  ▼                              │
  │ ┌──────────┐                    │
  │ │   Scan   │                    │
  │ │──────────│                    │
  │ │ id (PK)  │                    │
  │ │ type     │                    │
  │ │ status   │                    │
  │ │ severity │                    │
  │ │ counts   │                    │
  │ └────┬─────┘                    │
  │      │ 1:N                      │
  │      ▼                          │
  │ ┌──────────────┐                │
  │ │   Finding    │                │
  │ │──────────────│                │
  │ │ id (PK)      │                │
  │ │ scan_id (FK) │──▶ Scan        │
  │ │ asset_id(FK) │──▶ Asset       │
  │ │ cve_id       │                │
  │ │ severity     │                │
  │ │ risk_score   │                │
  │ │ triaged_by   │────────────────┘
  │ │ ai_remed.    │
  │ └──────────────┘
  │
  │ 1:N
  ▼
┌──────────┐
│  Asset   │
│──────────│
│ id (PK)  │
│ type     │
│ ident.   │
│ ip/host  │
└──────────┘
```

## Tables

### users
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, gen_random_uuid() | |
| email | VARCHAR(320) | UNIQUE, NOT NULL, INDEX | RFC 5321 max |
| hashed_password | VARCHAR(128) | NOT NULL | bcrypt hash |
| full_name | VARCHAR(255) | NOT NULL | |
| role | VARCHAR(20) | NOT NULL, DEFAULT 'viewer' | admin\|analyst\|viewer |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | Soft deactivation |
| last_login | TIMESTAMPTZ | NULLABLE | |
| created_at | TIMESTAMPTZ | NOT NULL, server_default now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, onupdate now() | |

### projects
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| name | VARCHAR(255) | NOT NULL | |
| description | TEXT | NOT NULL, DEFAULT '' | |
| owner_id | UUID | FK→users.id, ON DELETE CASCADE | |
| allowed_targets | VARCHAR[] | NULLABLE | CIDR allowlist |
| created_at | TIMESTAMPTZ | NOT NULL | |
| updated_at | TIMESTAMPTZ | NOT NULL | |

### assets
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| project_id | UUID | FK→projects.id, ON DELETE CASCADE, INDEX | |
| asset_type | VARCHAR(30) | NOT NULL | host\|web_app\|cloud_resource\|container\|network |
| identifier | VARCHAR(500) | NOT NULL | IP, URL, ARN, CIDR |
| hostname | VARCHAR(255) | NULLABLE | |
| ip_address | VARCHAR(45) | NULLABLE | IPv6-safe |
| os_fingerprint | VARCHAR(255) | NULLABLE | From nmap |
| open_ports | TEXT | NULLABLE | JSON array |
| tags | TEXT | NULLABLE | JSON array |
| notes | TEXT | NOT NULL, DEFAULT '' | |
| finding_count | INTEGER | NOT NULL, DEFAULT 0 | Denormalized |
| created_at | TIMESTAMPTZ | NOT NULL | |
| updated_at | TIMESTAMPTZ | NOT NULL | |

**Unique constraint:** `(project_id, identifier)` — no duplicate assets per project.

### scans
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| project_id | UUID | FK→projects.id, INDEX | |
| initiated_by | UUID | FK→users.id, ON DELETE SET NULL | |
| scan_type | VARCHAR(20) | NOT NULL | network\|web_app\|cloud\|container\|full |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | Lifecycle state |
| targets | TEXT | NULLABLE | JSON array |
| scanner_config | TEXT | NULLABLE | JSON object |
| started_at | TIMESTAMPTZ | NULLABLE | |
| completed_at | TIMESTAMPTZ | NULLABLE | |
| finding_count | INTEGER | NOT NULL, DEFAULT 0 | Denormalized |
| critical_count | INTEGER | NOT NULL, DEFAULT 0 | |
| high_count | INTEGER | NOT NULL, DEFAULT 0 | |
| medium_count | INTEGER | NOT NULL, DEFAULT 0 | |
| low_count | INTEGER | NOT NULL, DEFAULT 0 | |
| info_count | INTEGER | NOT NULL, DEFAULT 0 | |
| error_message | TEXT | NULLABLE | If status=failed |
| celery_task_id | VARCHAR(255) | NULLABLE | For task tracking |
| created_at | TIMESTAMPTZ | NOT NULL | |
| updated_at | TIMESTAMPTZ | NOT NULL | |

### findings
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| scan_id | UUID | FK→scans.id, ON DELETE CASCADE, INDEX | |
| asset_id | UUID | FK→assets.id, ON DELETE CASCADE, INDEX | |
| title | VARCHAR(500) | NOT NULL | |
| description | TEXT | NOT NULL | |
| severity | VARCHAR(20) | NOT NULL, INDEX | critical\|high\|medium\|low\|info |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'open', INDEX | Triage state |
| cve_id | VARCHAR(20) | NULLABLE, INDEX | CVE-YYYY-NNNNN |
| cwe_id | VARCHAR(10) | NULLABLE | CWE-NNN |
| references | TEXT | NULLABLE | JSON array of URLs |
| cvss_score | FLOAT | NULLABLE | 0.0–10.0 |
| cvss_vector | VARCHAR(100) | NULLABLE | CVSS v3.1 string |
| epss_score | FLOAT | NULLABLE | 0.0–1.0 |
| epss_percentile | FLOAT | NULLABLE | |
| is_cisa_kev | BOOLEAN | NOT NULL, DEFAULT false | KEV catalog flag |
| risk_score | FLOAT | NULLABLE | Faust composite 0–100 |
| scanner_name | VARCHAR(50) | NULLABLE | nmap\|nuclei\|trivy\|dast |
| scanner_rule_id | VARCHAR(255) | NULLABLE | |
| evidence | TEXT | NULLABLE | JSON object |
| raw_output | TEXT | NULLABLE | Scanner raw output |
| ai_remediation | TEXT | NULLABLE | Markdown remediation |
| ai_provider | VARCHAR(30) | NULLABLE | |
| ai_generated_at | TIMESTAMPTZ | NULLABLE | |
| triaged_by | UUID | FK→users.id, ON DELETE SET NULL | |
| triaged_at | TIMESTAMPTZ | NULLABLE | |
| triage_notes | TEXT | NULLABLE | |
| created_at | TIMESTAMPTZ | NOT NULL | |
| updated_at | TIMESTAMPTZ | NOT NULL | |

### reports
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| project_id | UUID | FK→projects.id, ON DELETE CASCADE, INDEX | |
| generated_by | UUID | FK→users.id, ON DELETE SET NULL | |
| title | VARCHAR(255) | NOT NULL | |
| report_format | VARCHAR(10) | NOT NULL, DEFAULT 'pdf' | pdf\|html\|json\|csv |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | |
| summary_json | TEXT | NULLABLE | JSON snapshot |
| file_path | VARCHAR(500) | NULLABLE | Generated file location |
| error_message | TEXT | NULLABLE | |
| created_at | TIMESTAMPTZ | NOT NULL | |
| updated_at | TIMESTAMPTZ | NOT NULL | |

## Risk Scoring Formula

The Faust composite risk score (0–100) combines three signals:

```
risk_score = (cvss_weight × cvss_normalized) + 
             (epss_weight × epss_normalized) + 
             (kev_weight × kev_flag)

Where:
  cvss_normalized = cvss_score × 10     (0–100 scale)
  epss_normalized = epss_score × 100    (0–100 scale)
  kev_flag = 100 if is_cisa_kev else 0

Default weights:
  cvss_weight = 0.4
  epss_weight = 0.35
  kev_weight  = 0.25
```

This ensures that a CVE in the CISA KEV catalog with high EPSS always ranks near the top, even if its CVSS is moderate.
