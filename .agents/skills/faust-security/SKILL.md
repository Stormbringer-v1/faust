---
name: faust-security
description: >
  Security review checklist for vulnerability scanner code. Triggers on any
  code that handles: auth, scanning, user input, API endpoints, database queries.
---

# FAUST Security Review Checklist

## 🚨 RULE ZERO — VM ONLY
All scanning, testing, and execution happens ONLY on the prepared VM. Never local.

When writing or reviewing code that touches security-sensitive areas:

## Input Validation
- All user inputs sanitized (SQLAlchemy parameterized queries, Pydantic validation)
- No raw SQL queries — always use ORM or parameterized statements
- File uploads: validate type, size, content (no path traversal)

## Authentication & Authorization
- JWT tokens with proper expiry and refresh rotation
- Role-based access control (admin | analyst | viewer)
- Rate limiting on auth endpoints
- Password hashing with bcrypt (min cost 12)

## Scanning Engine
- Scan targets validated (no scanning unauthorized networks)
- Scan results stored with integrity checks
- Plugin sandbox: plugins cannot access host filesystem directly
- Timeout and resource limits on all scan operations

## API Security
- CORS configured for specific origins only
- All endpoints require authentication (except /health and /auth/*)
- Response bodies never leak internal errors or stack traces
- Pagination enforced on all list endpoints
