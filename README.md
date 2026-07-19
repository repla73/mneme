# Mneme

Mneme is a local-first semantic continuity engine for long AI workflows. It preserves **why the work evolved**, not merely what messages were exchanged.

The engine observes completed conversation rounds, writes minimal processing receipts, stores meaningful semantic changes in an append-only hash-chained ledger, derives a compact current project state, detects authority conflicts, estimates context-degradation risk, and compiles handovers only after explicit user authorization.

## Architecture

Mneme has one platform-neutral core and capability-driven adapters:

- Browser companion: ChatGPT Web, Gemini Web, and Grok Web.
- Native adapters: Codex, Claude Code, Antigravity, OpenClaw, Cursor, Pi, and OpenCode.

Platform editions are not forks. Each adapter normalizes its host lifecycle into the same round, event, provenance, authorization, and risk contracts.

## Current milestone

`v0.1.0` includes:

- immutable semantic events and zero-event round receipts;
- deterministic state reduction and explicit conflict records;
- typed explicit, derived, and inferred rationale;
- privacy-aware provenance and handovers;
- bounded state capsules and context-risk assessment;
- user-authorized handover compilation;
- a platform capability registry for ten target surfaces;
- CLI, schemas, examples, documentation, and tests.

The production semantic extractor and runtime adapters remain the next implementation milestones.

## Invariants

- Inspect every completed round; emit events only for semantic changes.
- Never rewrite history; supersede immutable events.
- Derive current state from the ledger.
- Never silently resolve competing active authority.
- Keep full history out of ordinary prompt context.
- Keep facts, user decisions, model proposals, and inferences distinct.
- Require user authorization for human-facing handovers.
- Permit automatic machine safety snapshots before compaction or degradation.

## Quick start

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .

mneme init demo --root .mneme
mneme record-round demo examples/round-observation.json \
  --events-file examples/events.json --root .mneme
mneme verify demo --root .mneme
mneme reduce demo --root .mneme --snapshot
mneme capsule demo "What governs the ledger architecture?" --root .mneme
mneme risk examples/risk-signals.json
mneme handover demo "Transfer to a fresh session" \
  --target-platform chatgpt-web --root .mneme --authorized-by-user
mneme platforms
mneme platform openclaw
```

## Repository layout

```text
src/mneme/                 Core engine and bundled platform manifests
adapters/                  Platform adapter implementation boundaries
docs/                      Architecture and contracts
schemas/                   Exported JSON schemas
examples/                  Minimal event and risk fixtures
tests/                     Permanent invariant tests
```

See `docs/ARCHITECTURE.md`, `docs/EVENT-CONTRACT.md`, `docs/PLATFORM-ARCHITECTURE.md`, and `docs/ADAPTERS.md`.
