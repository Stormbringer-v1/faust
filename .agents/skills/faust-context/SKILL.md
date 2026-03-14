---
name: faust-context
description: >
  Always load project context before any task. Reads FAUST.md for project spec
  and AGENTS_LOG.md for recent work history. Triggers on any code task.
---

# FAUST Project Context Loader

## 🚨 RULE ZERO — VM ONLY
ALL commands, builds, tests, Docker, installs, and ANY execution happen ONLY on the
prepared VM. NOTHING runs on the local laptop. The local machine is a thin client only.
If you are about to suggest or run something locally — STOP. Use the VM.

## Before any task:
1. Read `FAUST.md` in the project root
2. Read `AGENTS_LOG.md` in the project root
3. Identify your agent role based on the model you are running as:
   - Gemini 3.1 Pro → RAPID-ENG
   - Claude Opus 4.6 → ARCHITECT
   - Claude Sonnet 4.6 → BUILDER
4. Check the last 5 entries in AGENTS_LOG.md for context
5. Proceed with the task

## After completing any task:
1. Append a new entry to `AGENTS_LOG.md` with:
   - ISO timestamp
   - Your agent ID
   - Summary of work done
   - Files touched
   - Open items or blockers
