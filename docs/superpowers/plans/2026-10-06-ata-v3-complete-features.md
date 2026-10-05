# ATA v3 Complete Thesis Features Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans task-by-task. TDD applies.

**Goal:** Complete media intelligence, revision workflow, evidence resolution, DOCX export, and persistent defense coaching without changing the operator's external database topology.

**Architecture:** Extend the existing project-scoped foundation with focused modules. Media calls use OpenRouter; revision and defense workflows use existing artifact/directive/defense tables; export is generated in-memory; evidence resolution is deterministic. No external auth/storage/database service is introduced.

**Tech Stack:** Python stdlib, python-docx, OpenRouter HTTP API, existing SQLite/PostgreSQL adapter, vanilla JS/CSS.

**Spec:** `docs/superpowers/specs/2026-10-05-ata-v3-product-overhaul-design.md`

## Global Constraints
- Do not change external database topology or require Supabase.
- Keep OpenRouter as the only AI provider integration.
- Every accepted revision creates a new artifact version; never overwrite.
- Evidence resolution must distinguish referenced from verified.
- Media provider failures must preserve the upload and return an honest error/pending state.
- Mobile must remain usable at 390px width.

## Review Focus
- Missing/invalid OpenRouter key must fail safely and not fabricate transcript/vision output.
- Image/audio size and unsupported formats must return actionable errors.
- Rejected revision must not create a new artifact version or mark a directive addressed.
- Evidence references with locators must only verify when a matching verified source/evidence exists.
- DOCX export must remain valid when no campus template is supplied.

---

### Task 1: OpenRouter media intelligence
- Test: `tests/test_media.py`
- Create/modify: `core/openrouter_client.py`, `core/file_parser.py`, `server.py`, `web/studio.js`
- Add deterministic request helpers and provider calls for transcription and vision.
- Verify with mocked HTTP tests and existing suite.

### Task 2: Supervisor revision engine
- Test: `tests/test_revisions.py`
- Create: `core/revisions.py`
- Modify: `core/db.py`, `core/roles.py`, `server.py`, `web/index.html`, `web/studio.js`, `web/studio.css`
- Propose revision against a selected artifact, show diff, accept/reject, and create immutable artifact version on acceptance.

### Task 3: Evidence resolver
- Test: `tests/test_evidence_resolution.py`
- Create: `core/evidence.py`
- Modify: `core/claims.py`, `core/db.py`, `server.py`, `web/index.html`, `web/studio.js`
- Resolve `[Brief: ...]` locators against verified sources/evidence and expose verified/partial/unsupported status.

### Task 4: DOCX manuscript export
- Test: `tests/test_docx_export.py`
- Create: `core/export_docx.py`
- Modify: `server.py`, `web/index.html`, `web/studio.js`
- Export latest ordered artifacts to a valid DOCX; optionally apply an uploaded DOCX template.

### Task 5: Defense coaching history
- Test: `tests/test_defense.py`
- Create: `core/defense.py`
- Modify: `core/db.py`, `server.py`, `web/index.html`, `web/studio.js`, `web/studio.css`
- Evaluate a student answer, persist score/feedback, expose history and weakness summary.

### Task 6: Regression, security, patch packaging
- Tests: full `python -m unittest discover -s tests -p 'test_*.py' -v`, `python -m py_compile ...`, `node --check web/studio.js`.
- Update README patch notes and build one cumulative ZIP from the original audited base.
