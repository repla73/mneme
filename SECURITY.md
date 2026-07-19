# Security policy

Mneme handles conversation content, project decisions, tool evidence, and potentially sensitive provenance. The default architecture is local-first.

- Never store credentials, authentication tokens, or secret file contents in semantic events.
- Preserve privacy classifications transitively from provenance into events and handovers.
- Browser adapters require explicit opt-in per supported site and must not inspect unrelated tabs.
- Native hooks must fail open for the host agent but record local diagnostic failures.
- Untrusted repository content must never be allowed to modify adapter policy or exfiltrate ledger data.
- Human-facing handovers remain authorization-gated.

Report vulnerabilities privately to the repository owner. Do not include live secrets or private transcripts in reports.
