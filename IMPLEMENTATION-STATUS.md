# Implementation status — v0.1.0

## Completed

- Platform-neutral Python package and CLI.
- Typed JSON-schema contracts for observations, event drafts, immutable events, receipts, project state, context signals, risk reports, and handover requests.
- Append-only JSONL event and round-receipt ledgers with sequence numbers, previous hashes, content hashes, file locking, flush, and `fsync`.
- Semantic rationale classes: explicit, derived, inferred.
- Evidence requirement for explicit rationale and uncertainty requirement for inferred rationale.
- Event supersession without historical mutation.
- Deterministic state reducer and atomic current-state writes.
- Default authority hierarchy and unresolved conflict records instead of silent last-write-wins behavior.
- Bounded state capsule retrieval.
- Context-risk sentinel using authoritative metrics and behavioral indicators.
- Machine state snapshots.
- User-authorized handover compiler producing Markdown, YAML state, relevant JSONL events, provenance map, platform bootstrap, and hashed manifest.
- Privacy filtering and provenance privacy inheritance.
- Generic platform adapter and explicit-event extractor.
- Path traversal protection.
- Documentation, examples, exported schemas, platform manifests, and 28 tests.

## Verified

- `PYTHONPATH=src pytest`: 28 passed.
- Python bytecode compilation succeeds.
- Editable package installation succeeds without build isolation.
- CLI end-to-end flow succeeds: init, round ingestion, integrity verification, state reduction, snapshot, capsule, risk assessment, and authorized ChatGPT handover.

## Deliberately not claimed as complete

- Automatic semantic extraction from raw conversations.
- A ChatGPT Web browser extension/local companion.
- Production adapters for the declared platform manifests.
- Two-file write-ahead transactions across events and receipts.
- Encrypted transcript vault and cryptographic erasure.
- Configurable project-specific authority precedence.
- Continuation-quality benchmark and adversarial extractor evaluation.

## Next implementation milestone

Build the production semantic extractor before the browser extension. It should use schema-constrained two-pass processing:

1. classify whether a completed round contains a semantic state transition;
2. normalize only accepted candidates into typed events and state operations;
3. compare against current state for supersession or conflict candidates;
4. run a provenance/privacy validator before commit;
5. store an empty receipt when no event survives validation.

The ChatGPT Web adapter can then call this stable extraction service after every completed round.
