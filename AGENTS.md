# Mneme agent contract

This repository implements a provenance-aware continuity engine. All agents modifying it must preserve the following invariants.

## Authority

1. `docs/ARCHITECTURE.md` defines the core semantic model.
2. `docs/EVENT-CONTRACT.md` defines persisted event behavior.
3. `src/mneme/platforms/*.yaml` are the versioned platform capability contracts.
4. Tests are permanent evidence for implemented behavior; do not weaken them to make a change pass.

## Core invariants

- Inspect every completed round, but emit semantic events only for material state changes.
- Store observable rationale and provenance; never claim access to hidden chain-of-thought.
- Append and supersede; never rewrite ledger history.
- Derive current state deterministically from the ledger.
- Preserve unresolved authority conflicts instead of silently applying last-write-wins.
- Keep the full ledger out of ordinary model context.
- Require explicit user authorization for human-facing handovers.
- Permit automatic machine safety snapshots when degradation or compaction risk rises.
- Keep platform-specific behavior behind adapters. Do not fork core semantics per vendor.

## Change discipline

- Update a platform manifest and its primary-source evidence when a capability claim changes.
- Add or update tests for every behavior change.
- Run `pytest`, bytecode compilation, and relevant CLI smoke tests before publishing.
- Keep secrets, personal identifiers, raw transcripts, and generated runtime state out of Git.
- Use feature branches and draft pull requests after repository initialization.

See `external-gpt/PROTOCOL.md` for the repository workflow used by external review agents.
