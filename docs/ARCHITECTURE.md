# Architecture

## Objective

Preserve the semantic mneme of long workflows across context degradation, compaction, platform boundaries, and fresh sessions. The system records decisions, constraints, evidence, corrections, authority, uncertainty, and rationale as structured state transitions.

## Runtime flow

```text
Completed platform round
        │
        ▼
Turn observer / adapter
        │
        ├── source hash and round receipt
        ▼
Semantic extractor
        │
        ├── zero or more EventDraft objects
        ▼
Append-only event ledger
        │
        ├── sequence + previous_hash + content_hash
        ▼
Deterministic state reducer
        │
        ├── authority checks and conflict records
        ▼
Current project state
        │
        ├── bounded retrieval capsule
        ├── machine safety snapshot
        └── user-authorized handover compiler
```

## Three persistence layers

### 1. Round receipts

A receipt proves that a completed round was inspected. It stores a source hash and zero or more event IDs. A low-value conversational exchange therefore produces a receipt but no semantic event.

### 2. Immutable semantic event ledger

The event ledger contains historical semantic deltas. Each event records subject, type, before/after meaning, rationale status, authority, provenance, privacy class, state operations, and supersession relationships.

The file is append-only JSONL. Each line hashes the full record except its own `content_hash`, and contains the previous record hash. Tampering, deletion, reordering, and insertion are detectable.

### 3. Materialized project state

The reducer replays non-superseded events and applies normalized state operations. This state contains the mission, current phase, active decisions, constraints, facts, assumptions, rejected approaches, unresolved questions, blockers, risks, completed outcomes, mneme warnings, and next authorized action.

The current state is not independently authoritative. It can be deleted and rebuilt from the event ledger.

## Authority and conflict semantics

The default authority order is:

```text
explicit user approval
> user instruction
> canonical artifact
> verified evidence
> accepted decision
> assistant proposal
> assistant inference
```

A new event may replace an active value when either:

1. it explicitly supersedes the source event; or
2. its authority is strictly higher.

A competing equal- or lower-authority value creates an unresolved `StateConflict`. The existing value remains active until a later authoritative event resolves the conflict. This prevents silent last-write-wins corruption.

Project-specific authority policy will become configurable in the next milestone. The current mapping is an explicit core default.

## Rationale fidelity

Rationale claims are typed as:

- `explicit`: directly stated and linked to evidence;
- `derived`: logically produced from explicit constraints or evidence;
- `inferred`: plausible reconstruction that remains uncertain.

The schema rejects explicit rationale without evidence and rejects inferred rationale with certainty `1.0`.

The engine does not claim access to hidden chain-of-thought. It stores observable decision justifications and provenance.

## Privacy model

Every event, provenance reference, and derived state item has a privacy class. An event is rejected when its privacy class is lower than any attached provenance reference:

```text
public < project_internal < sensitive < secret
```

The handover compiler accepts a maximum included class and removes higher-class state and events. Each generated file is hashed in `manifest.json`.

Encrypted transcript storage and cryptographic erasure are represented in the directory contract but are not yet implemented in `v0.1.0`.

## Context-risk sentinel

The sentinel combines authoritative runtime metrics, when available, with behavioral indicators such as forgotten constraints, reopened decisions, repeated user corrections, compaction count, tool-output growth, and unresolved state conflicts.

Untrusted token figures are not converted into exact context percentages. The sentinel can recommend a machine snapshot and ask for handover authorization, but the compiler itself remains user-gated.

## Retrieval policy

The full ledger is never injected by default. The capsule builder ranks current-state items by authority-oriented base priority plus query overlap, then enforces a strict character budget.

Vector search may later assist discovery but must never determine authority or supersession.

## Crash and concurrency properties

Event and receipt files use an exclusive advisory file lock, one append block, flush, and `fsync`. Their chains are independently verifiable.

Events and receipts are separate files, so a process crash between their appends can leave a valid event without a corresponding receipt. Verification detects malformed references but does not yet implement a two-file write-ahead transaction. A transaction journal is planned for the production storage milestone.
