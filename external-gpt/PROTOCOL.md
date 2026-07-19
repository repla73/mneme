# External agent protocol

## Purpose

Provide a bounded, evidence-led workflow for agents that design, implement, review, or ratify changes in Mneme.

## Required sequence

1. Read `AGENTS.md` and only the governing documents relevant to the task.
2. Inspect the exact code, manifests, and tests affected by the requested change.
3. State blocking ambiguities or contract conflicts before implementation.
4. Make the smallest coherent change that preserves the core invariants.
5. Add permanent tests and run the relevant validation commands.
6. Report changed files, verified behavior, unresolved risks, and the next authorized action.

## Evidence rules

- Repository state and test output override conversational assumptions.
- Platform capability claims require current primary documentation in the relevant manifest.
- Inference must be labeled as inference.
- Do not claim commands, tests, commits, pushes, or reviews occurred without direct evidence.

## Scope rules

- Do not modify unrelated files.
- Do not duplicate the core engine for a platform adapter.
- Do not publish secrets, private transcripts, account identifiers, tokens, or environment-specific paths.
- Do not automatically generate a human handover without explicit user authorization.
