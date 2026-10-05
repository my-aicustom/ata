# ATA v3 Product Overhaul — Design

## Objective

ATA is a Thesis Operating System, not a menu of AI personas. A student should be able to enter from any thesis state, tell ATA where they are, and receive the next best action while the system internally selects the correct role, evidence checks, method gate, and revision workflow.

## Product principles

1. Outcome-driven UI. The primary choices are thesis states: start, title, proposal, data, writing, revision, defense. Internal roles remain implementation details.
2. Evidence-first. Literature candidates are discovered through academic APIs, then verified. LLM output is never a source of record.
3. Method-aware gates. Survey thresholds must not be applied to interview, content analysis, DSR, or system experiments.
4. Versioned artifacts. Chapters and outputs are saved as immutable versions rather than silently overwritten chat text.
5. Project isolation. No global active thesis. Every project is scoped to a browser session and project id.
6. Deployment honesty. SQLite is acceptable for local/self-hosted durable storage. Vercel production must use DATABASE_URL with managed PostgreSQL.
7. Student remains the argument owner. ATA can expand, critique, and coach, but it does not fabricate evidence or replace academic responsibility.

## Architecture

### Session / project layer

An opaque HttpOnly `ata_session` cookie isolates anonymous browser workspaces. Each session can own multiple thesis projects. `project_state` stores the active project per session, replacing the v2 global `.active_instance` file.

### Persistence

The schema is project-scoped: directives, sources, evidence, claims, consistency rows, gate assessments, artifacts, revision tasks, defense scores, and AI usage logs all carry `project_id`.

Backends:
- SQLite in `ATA_DATA_DIR` for local/self-hosted use.
- PostgreSQL through `DATABASE_URL` for Vercel or multi-instance production.

### Orchestration

The UI maps a user-visible thesis state to an internal role. A deterministic planner evaluates G1–G6 and returns the next best action. This avoids exposing `Topic Framer`, `Stats Reviewer`, etc. as the primary navigation model.

### Literature pipeline

Search calls OpenAlex and Crossref directly. Search results are stored as `candidate`, never `verified`. Citation verification is a separate deterministic step. The LLM synthesizes supplied/verified records; it does not invent discovery results.

### Method-aware quality gates

G4 is routed by method:
- survey: loading, AVE, HTMT, CR;
- interview: saturation, triangulation, codebook, member check;
- content analysis: Krippendorff alpha + locked period/codebook;
- system experiment: repeated runs, reproducibility, raw logs, locked plan;
- DSR: artifact definition, locked evaluation criteria, evaluation, traceability;
- fallback: explicit auditable QC evidence.

G2 uses configurable project/domain targets instead of hardcoded LKPP/SINTA assumptions.

### Artifact engine

Each save creates a new `(project_id, kind, title, version)` record. This is the foundation for revision diff/accept-reject workflows and campus export later.

### File intake

The patch removes the shell dependency on `markitdown` for core PDF/DOCX parsing. PDF extraction preserves page markers. Images and audio are explicitly labeled as requiring a multimodal/transcription provider; ATA does not pretend they were interpreted.

## UI

The desktop layout uses a narrow project rail, a dominant central thesis conversation, and a right Thesis Workbench. The workbench exposes user outcomes: supervisor directives, literature/evidence, manuscript artifacts, quality gates, and defense.

The initial screen asks: **“Posisi tesis Anda sekarang?”** rather than presenting an agent list.

## Migration

`scripts/migrate_v2_to_v3.py` imports the existing v2 SQLite directives, sources, and consistency rows into one isolated v3 project. It never deletes the old database.

## Completion extension (approved scope)

This cumulative patch now adds the provider-dependent thesis features that can run on the existing OpenRouter key and local application stack, while leaving deployment database configuration to the operator:
- real OpenRouter audio transcription for thesis voice notes;
- multimodal screenshot/image interpretation for supervisor notes and research material;
- revision proposals with before/after diff and accept/reject workflow;
- claim-to-source/evidence resolution with locator-aware verification;
- DOCX manuscript export, with optional campus template input;
- defense evaluation history and weakness-oriented coaching.

Still external/operator-owned: object storage for very large production uploads, login/cross-device identity, and deployment-specific PostgreSQL/PostgREST wiring. The patch must not require a new managed database service.
