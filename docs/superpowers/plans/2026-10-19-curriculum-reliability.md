# Curriculum Reliability Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the AI Agent curriculum technically accurate, reproducible, and explicit about its evidence and operational boundaries.

**Architecture:** Implement the approved design as independently reviewable work packages. W0 establishes correction governance and an auditable lesson inventory; W1 corrects confirmed high-risk claims and examples; later packages add protocol, security, retrieval, evaluation, and capstone coverage. Preserve raw experiment observations while versioning corrections to their interpretation.

**Tech Stack:** Markdown/MDX, TypeScript/Vitest content checks, Python teaching examples, official protocol documentation, Git-based content baselines.

---

## Chunk 1: W0 — correction governance

**Files:** `CONTENT_GUIDE.md`, `docs/CONTENT-DEPTH.md`, `docs/CURRICULUM-REVIEW-TRACKER.md`, `scripts/verify-depth-fixes.mjs`.

- [x] Define correction records: stable ID, affected lesson, old claim, reason, new evidence, replacement claim, impact, and verification status.
- [x] Clarify that corrections may replace incorrect code, scores, and interpretations while preserving historical observations and explaining the change.
- [x] Inventory every registered lesson ID and mark each `not-reviewed`; do not imply that all lessons were manually audited.
- [x] Change the depth verifier to require an explicit Git base revision and fail when the requested baseline cannot be read.
- [x] Add/adjust a focused regression test for missing or invalid base revisions and expected content comparisons.
- [x] Run the focused test and content integrity suite.

## Chunk 2: W1 — confirmed high-risk corrections

**Files:**

- `src/content/chapters/mcp/03-stateless-2026.mdx`
- `src/content/chapters/mcp/04-build-a-server.mdx`
- `src/content/chapters/capstone/02-skeleton.mdx`
- `src/content/chapters/structured-output/02-json-schema-strict.mdx`
- `src/content/chapters/evaluation/02-pass-k.mdx`
- `src/content/chapters/evaluation/10-confidence.mdx`
- `src/content/chapters/human-in-the-loop/03-interrupt-and-resume.mdx`
- `src/content/chapters/agent-deployment/01-deployment-shape.mdx`
- `src/content/chapters/human-in-the-loop/01-automation-levels.mdx`
- `src/content/chapters/coding-agent/01-why-coding-agent.mdx`
- `src/content/chapters/retrieval/01-why-retrieval.mdx`
- `docs/ERRATA.md` (or the correction registry chosen in W0).

- [x] Reproduce/inspect the identified defects in the affected claims, derived values, and runnable examples before editing; ERR-006/007 now have a local SQLite fault/concurrency model with explicit production limitations.
- [x] Verify MCP 2026-07-28 claims against the cited official spec and official Python SDK 2.3.0, recording version/date.
- [x] Correct the teaching path and runnable examples; preserve original observations with clear provenance.
- [x] Add a correction record and targeted regression checks for each executable behavior or derived numeric result. ERR-006/007 checks cover crash boundaries and concurrent local workers; they do not claim production PostgreSQL or multi-process guarantees.
- [x] Run the affected examples, content tests, depth checks, and link checks where applicable. (Tests, depth, build, search index, and changed Python/MCP examples pass; site-wide link scan completed with 40 existing broken/blocked source links, with no failure reported for the newly verified MCP spec links.)

**W1 outcome (2026-10-19):** ERR-001–010 are verified within the scope stated in `docs/ERRATA.md`; ERR-006/007 are verified only for the registered SQLite teaching model. The audit tracker has 12 corrected lessons and 122 not reviewed. Do not treat this tranche as completion of the full design.

## Chunk 3: W2 — evidence and experiment registry

**Files:** experiment registry/claims/errata manifests, `tests/`, affected content metadata.

- [x] Model observations separately from interpretations and recommendations for the first five high-risk experiments; wider coverage remains pending.
- [x] Give all seven current claims and eight experiments reproducible locators/hashes, method, date, and scope; many published claims and numeric observations remain unregistered.
- [x] Validate registered lesson references, correction links, source ids, fence/script hashes, result links, and experiment IDs in CI with `pnpm verify:evidence`.
- [x] Add `pnpm verify:examples` for an explicit, hash-pinned Python allowlist with timeout, temporary directory, and sanitized environment.
- [x] Validate all registered result files against the published JSON Schema and execute two explicit Python suites in the sanitized, timeout-bounded runner; broader environment and evidence coverage remains pending.
- [x] Expand the initial registry beyond the four W1 claims: add three scoped claims and matching experiments for Retry-After, PostgreSQL backup verification limits, and provider fixture evidence. Full-book claim coverage remains pending.

## Chunk 4: W3–W5 — learning path and operational coverage

**Files:** curriculum chapter `meta.ts`/`body.ts`, new MDX lessons, `projects.ts`, tests, project examples.

- [x] Add the read-only first-loop path without changing prerequisite edges; API/prompt/tool/loop navigation and the offline-tested example are present.
- [x] Add the provider contract lesson with a current official-source comparison, capability-matrix criteria, and offline response-state classifier; online provider behavior remains unverified.
- [x] Add the index lifecycle lesson with a SQLite model covering source revisions, tombstones, stale generation rejection, and atomic pointer publication; vector-service and multi-process behavior remain unverified.
- [x] Add permission filtering before context hydration, with an official PostgreSQL RLS boundary note and local cross-tenant/revocation negative tests; identity-provider and production RLS behavior remain unverified.
- [x] Add execution ownership with lease expiry, monotonically increasing epochs, stale worker rejection, and checkpoint recovery in a SQLite teaching model; PostgreSQL multi-process and external side-effect behavior remain unverified.
- [x] Add remote authorization coverage for MCP 2026-07-28 HTTP OAuth resource/audience checks, token-passthrough prohibition, and stdio credential separation; offline decision-model tests pass, real IdP interoperability remains unverified.
- [x] Add identity and tenancy authorization with trusted principal context, per-request membership/resource checks, deny-by-default behavior, and a local SQLite cross-tenant negative suite; production identity and RLS remain unverified.
- [x] Add provider migration contract coverage and an offline fixture classifier; live endpoint migration evidence remains pending.
- [x] Add recovery drills covering worker/action fault boundaries, evidence, and PostgreSQL restore verification limits; real database restore and live dependency drills remain pending.
- [x] Add capstone acceptance rubric and evidence classifier; true-model, production integration, and independent handoff evidence remain pending.
- [x] Register five stage project specifications and link them to chapters with one consistent after-sales order support domain.
- [x] Build the stage 2 offline lexical retrieval baseline with versioned citations, tenant/principal filtering, validity/deletion handling, abstention, and separate recall/citation/answer metrics; real embeddings remain a separate unverified experiment.
- [x] Build the stage 3 provider-backed MCP agent, verify the MCP Python SDK 2.3.0 stdio peer with `tools/list`/`tools/call`, and record a true-model tool round-trip against synthetic fixtures.
- [x] Build and accept the stage 4 PostgreSQL multi-process synthetic service with durable approval recovery, action reconciliation, manual resolution, and registered evidence; provider-quality and production-system guarantees remain unverified.
- [ ] Integrate and independently hand off the stage 5 capstone, including true-model and failure-drill evidence.
- [x] Keep offline control-flow validation separate from true-model evidence; the offline suite is hash-pinned and the live report is gitignored under `verify-output/stage3-mcp/`.

**2026-10-20 Stage 4 acceptance:** The required `uv run pytest -m integration -q` gate now exercises the full runtime through two independently started API processes and a temporary real PostgreSQL service; missing Docker/database fails the gate. Readiness requires migrations `0001`–`0004`. PostgreSQL integration, synthetic/offline tests, and provider observations use separate evidence classifications. The registered Stage 4 result is sanitized and remains `needs-review` until a human completes the first review. No Stage 4 true-model call was made; full true-model capstone acceptance, independent handoff, frozen holdout quality evaluation, and release/rollback remain Stage 5 work. The 144-lesson factual audit is still open.

## Chunk 5: W6 — final audit and publishable handoff

- [ ] Review all 144 registered lessons against the five teaching elements and source rules.
- [ ] Run tests, typecheck, lint, depth checks, build, search-index generation, and link checks.
- [ ] Re-run visual checks for changed pages and verify the production static output.
- [ ] Update progress and roadmap documents with completed work and remaining verified limitations.

## Chunk boundaries

W0 and W1 are separate deliverables. W2 can be reviewed independently before new numeric claims are written. W3–W5 should be split further into focused plans when started because their lesson, runtime, and project changes have different test surfaces.
