# Platform adapters

## Stable interface

A platform adapter must produce a `RoundObservation` after a complete user → assistant → tool outcome round. A `SemanticExtractor` then returns zero or more `EventDraft` objects.

```python
class SemanticExtractor(Protocol):
    def extract(self, observation: RoundObservation) -> list[EventDraft]: ...
```

The generic adapter validates project/session/round identity, appends events, calculates a source hash over the observable round, and appends the receipt.

## ChatGPT Web target

A production ChatGPT Web adapter requires a browser extension or local companion for guaranteed post-round observation. A prompt-only custom GPT can request writes but cannot provide a hard persistence guarantee.

Planned components:

- browser content observer limited to explicitly authorized project chats;
- local mneme service;
- semantic extraction call with structured output;
- visible pause/error indicator when a round is not persisted;
- retrieval tool for bounded state capsules;
- explicit handover command.

## Claude Code / Cowork target

Claude Code can use lifecycle hooks to form completed rounds and persist tool provenance. A Skill should expose retrieval and handover commands; hooks should own guaranteed writes.

Cowork and Claude Web require a companion when unconditional post-round capture is required.

## Gemini / Antigravity target

Gemini skills are appropriate for retrieval and compilation but not assumed to run after every round. Antigravity can provide a stronger adapter when its request/response loop is controlled.

## OpenClaw target

OpenClaw plugin and context-engine hooks can support native observation, after-turn commits, bounded retrieval, risk checking, and pre-compaction safety snapshots. The human-facing compiler must remain user-triggered unless an explicit emergency policy says otherwise.

## Extractor requirements

A production extractor must:

1. emit no event when no semantic state changed;
2. quote or reference observable evidence for explicit claims;
3. label inference and confidence honestly;
4. propose normalized state operations;
5. identify candidate supersession and conflicts;
6. avoid storing secrets unless policy explicitly permits it;
7. remain idempotent for the same round source hash.
