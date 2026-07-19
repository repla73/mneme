#!/usr/bin/env python3
"""Generate docs/PLATFORM-MATRIX.md from bundled capability manifests."""

from __future__ import annotations

from pathlib import Path

from mneme.platform import PlatformRegistry


CAPABILITIES = (
    ("completed_round_event", "Round"),
    ("tool_events", "Tools"),
    ("pre_compaction_event", "Pre-compact"),
    ("post_compaction_event", "Post-compact"),
    ("exact_context_metrics", "Context metrics"),
    ("background_write", "Background write"),
)


def main() -> None:
    manifests = PlatformRegistry.bundled().list()
    headers = ["Platform", "Evidence checked", "Surface", "Strategy", *(label for _, label in CAPABILITIES)]
    rows = []
    for manifest in manifests:
        row = [
            manifest.display_name,
            manifest.evidence_checked_at.isoformat(),
            manifest.surface_kind.value,
            manifest.strategy.value,
            *(getattr(manifest.capabilities, field).value for field, _ in CAPABILITIES),
        ]
        rows.append(row)

    lines = [
        "# Platform capability matrix",
        "",
        "Generated from `src/mneme/platforms/*.yaml`. Capability values are evidence-scoped contracts, not permanent vendor guarantees.",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    lines.extend(
        [
            "",
            "## Reliability labels",
            "",
            "- `native`: documented host lifecycle or extension support.",
            "- `companion`: guaranteed by Mneme-owned local software.",
            "- `cooperative`: depends on model/tool/skill selection.",
            "- `absent`: no supported mechanism was verified.",
            "- `unknown`: evidence is insufficient; the adapter must not assume support.",
            "",
            "Run `PYTHONPATH=src python scripts/generate_platform_matrix.py` after changing a manifest.",
        ]
    )
    Path("docs/PLATFORM-MATRIX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
