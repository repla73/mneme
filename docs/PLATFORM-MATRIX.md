# Platform capability matrix

Generated from `src/mneme/platforms/*.yaml`. Capability values are evidence-scoped contracts, not permanent vendor guarantees.

| Platform | Evidence checked | Surface | Strategy | Round | Tools | Pre-compact | Post-compact | Context metrics | Background write |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Google Antigravity | 2026-07-20 | coding_agent | native_hooks | native | native | native | unknown | unknown | native |
| ChatGPT Web | 2026-07-20 | web | browser_companion | companion | companion | absent | absent | absent | companion |
| Claude Code | 2026-07-20 | coding_agent | native_hooks | native | native | native | native | unknown | native |
| OpenAI Codex | 2026-07-20 | coding_agent | native_hooks | native | native | native | native | unknown | native |
| Cursor | 2026-07-20 | coding_agent | hybrid | native | native | unknown | unknown | unknown | native |
| Gemini Web | 2026-07-20 | web | browser_companion | companion | companion | absent | absent | absent | companion |
| Grok Web | 2026-07-20 | web | browser_companion | companion | companion | absent | absent | absent | companion |
| OpenClaw | 2026-07-20 | agent_runtime | plugin | native | native | native | native | native | native |
| OpenCode | 2026-07-20 | coding_agent | plugin | native | native | native | unknown | unknown | native |
| Pi Coding Agent | 2026-07-20 | coding_agent | plugin | native | native | native | native | unknown | native |

## Reliability labels

- `native`: documented host lifecycle or extension support.
- `companion`: guaranteed by Mneme-owned local software.
- `cooperative`: depends on model/tool/skill selection.
- `absent`: no supported mechanism was verified.
- `unknown`: evidence is insufficient; the adapter must not assume support.

Run `PYTHONPATH=src python scripts/generate_platform_matrix.py` after changing a manifest.
