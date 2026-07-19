# Roadmap

## Milestone 1 — Core contracts (implemented)

- typed semantic events and rationale provenance;
- round receipts;
- append-only hash chains;
- deterministic reducer;
- authority conflict records;
- bounded state capsules;
- context-risk sentinel;
- privacy-filtered, user-authorized handovers;
- generic adapter and CLI;
- schema export and tests.

## Milestone 2 — Production semantic extraction

- model-independent extraction prompt and JSON-schema enforcement;
- two-pass extraction: candidate detection then semantic normalization;
- idempotency by source hash;
- contradiction and candidate-supersession analysis;
- confidence calibration fixtures;
- adversarial tests for fabricated rationale and overcapture.

## Milestone 3 — ChatGPT Web first adapter

- browser extension plus local service;
- explicit project/session binding;
- completed-round detection;
- durable status and retry queue;
- local encryption and secret redaction;
- state capsule retrieval action;
- user handover command and risk prompt.

## Milestone 4 — Additional adapters

- Codex hooks and Skill;
- Claude Code hooks and Skill;
- Gemini Web and Grok Web site observers in the shared browser companion;
- Antigravity native hook adapter;
- OpenClaw plugin/context-engine integration;
- Cursor hook/stream adapter;
- Pi extension;
- OpenCode plugin.

## Milestone 5 — Evaluation and hardening

- continuation benchmark using fresh agents;
- authority-conflict benchmark;
- rationale fidelity and provenance benchmark;
- selective forgetting and privacy deletion;
- write-ahead transaction journal;
- encrypted transcript vault and cryptographic erasure;
- configurable project authority rules;
- signed handover manifests.
