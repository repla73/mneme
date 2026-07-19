# Platform architecture

Mneme is one continuity engine with multiple adapters. Platform editions are not forks.

## Selection rule

A separate adapter is justified only when the platform changes one or more of these contracts:

1. how a completed round is observed;
2. how tool evidence and provenance are obtained;
3. whether compaction lifecycle events exist;
4. whether exact context metrics are available;
5. how a user authorizes a handover;
6. where local code may run and persist data.

## Adapter families

### Browser companion

ChatGPT Web, Gemini Web, and Grok Web share one browser-extension runtime. Each site receives a small observer module because DOM structures and conversation identifiers differ. The extension sends normalized round observations to a local Mneme service. Web-product memory, Gems, GPTs, Skills, Actions, and similar features remain cooperative interfaces, not the event authority.

### Native lifecycle adapters

Codex, Claude Code, Antigravity, OpenClaw, Cursor, Pi, and OpenCode expose hooks, plugins, structured streams, or extension APIs. Their adapters should capture lifecycle events directly and avoid browser automation.

### Core boundary

Every adapter must emit the same `RoundObservation`, `EventDraft`, provenance, authorization, and risk-signal contracts. Platform-specific data must be normalized before it enters the immutable ledger.

## Reliability classes

- **Native:** guaranteed by a documented platform lifecycle or extension API.
- **Companion:** guaranteed by Mneme-owned local software outside the platform.
- **Cooperative:** depends on the model choosing a tool, skill, or instruction path.
- **Absent:** no supported mechanism is known.
- **Unknown:** current evidence is insufficient; the adapter must not infer support.

## Release model

- `mneme-core`: Python engine and local service.
- `mneme-browser`: shared browser companion with site modules.
- `mneme-<platform>`: native adapter package where lifecycle requirements differ.
- Platform manifests are versioned compatibility contracts and must cite primary documentation.
