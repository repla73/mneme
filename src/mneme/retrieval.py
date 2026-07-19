"""Bounded current-state capsule generation for prompt injection."""

from __future__ import annotations

import re
from collections.abc import Iterable

from .models import ProjectState, StateItem


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_./-]+", text.lower()))


def _iter_items(state: ProjectState) -> Iterable[tuple[str, StateItem]]:
    for name in ("mission", "current_phase", "next_authorized_action"):
        item = getattr(state, name)
        if item:
            yield name, item
    for name in (
        "authority_sources",
        "active_decisions",
        "constraints",
        "blockers",
        "risks",
        "open_questions",
        "verified_facts",
        "assumptions",
        "rejected_approaches",
        "continuity_warnings",
        "scope_included",
        "scope_excluded",
        "completed_outcomes",
    ):
        for item in getattr(state, name).values():
            yield name, item


BASE_PRIORITY = {
    "mission": 100,
    "current_phase": 95,
    "next_authorized_action": 95,
    "authority_sources": 90,
    "active_decisions": 88,
    "constraints": 86,
    "blockers": 84,
    "continuity_warnings": 82,
    "risks": 78,
    "open_questions": 75,
    "verified_facts": 65,
    "assumptions": 55,
    "rejected_approaches": 50,
    "scope_included": 45,
    "scope_excluded": 45,
    "completed_outcomes": 30,
}


class StateCapsuleBuilder:
    def build(self, state: ProjectState, query: str, max_chars: int = 8_000) -> str:
        query_tokens = _tokens(query)
        ranked: list[tuple[int, str, StateItem]] = []
        for section, item in _iter_items(state):
            item_text = f"{item.key} {item.summary} {item.rationale or ''} {item.details}"
            overlap = len(query_tokens & _tokens(item_text))
            score = BASE_PRIORITY[section] + overlap * 15
            ranked.append((score, section, item))
        ranked.sort(key=lambda row: (-row[0], row[1], row[2].key))

        header = (
            f"PROJECT STATE v{state.state_version} | {state.project_id} | "
            f"hash={state.state_hash[:12]}\n"
        )
        output = header
        for _, section, item in ranked:
            line = f"- [{section}] {item.key}: {item.summary}"
            if item.rationale:
                line += f" Why: {item.rationale}"
            line += f" (source={item.source_event})\n"
            if len(output) + len(line) > max_chars:
                break
            output += line
        return output.rstrip()
