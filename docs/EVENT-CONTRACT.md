# Semantic event contract

## Event emission gate

An extractor should emit an event only when a completed round changes how a future agent should understand, govern, or continue the work.

Typical triggers:

- objective or scope changed;
- constraint added or removed;
- decision proposed, accepted, rejected, corrected, or superseded;
- ambiguity resolved;
- assumption recorded or invalidated;
- evidence changed a belief;
- authority changed;
- blocker or risk opened or resolved;
- action authorized or completed;
- mneme degradation detected.

Acknowledgements, stylistic edits, repeated information, and ordinary execution chatter should normally produce no semantic event.

## Event anatomy

```yaml
project_id: demo
session_id: chat-001
round_id: chat-001-round-0018
event_type: decision_accepted
subject: ledger persistence
summary: Use a local append-only semantic ledger.
semantic_delta:
  before: Final summaries were the mneme mechanism.
  after: Meaningful state transitions are captured continuously.
why:
  trigger: Long-session context became unreliable.
  rationale:
    - text: A fresh session must recover decisions without transcript replay.
      status: explicit
      evidence_refs: [conversation:user:18]
      confidence: 1.0
authority:
  actor: user
  level: explicit_user_approval
  source_ref: conversation:user:18
privacy_class: project_internal
supersedes: []
state_operations:
  - action: upsert
    section: active_decisions
    key: immutable-ledger
    value:
      summary: Record semantic state changes in an append-only ledger.
      rationale: Historical rationale must remain auditable.
```

The store adds `event_id`, `sequence`, `created_at`, `previous_hash`, and `content_hash`.

## Supersession

Events are never edited. A correction appends a new event with the old event ID in `supersedes`.

Supersession references must point backward to existing event IDs. The reducer excludes superseded event effects while retaining those records for audit and historical explanation.

## State operations

Events carry normalized operations so the reducer does not have to reinterpret narrative text. The supported actions are `set`, `upsert`, and `remove`. Supported sections are defined by `StateSection` in `models.py`.

This separation allows a future LLM extractor to propose semantic events while deterministic code controls state mutation.
