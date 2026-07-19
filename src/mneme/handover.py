"""User-authorized handover package compiler with privacy filtering and provenance."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import yaml
from pydantic import BaseModel, ConfigDict, Field

from .canonical import canonical_json, hash_file, utc_now
from .models import PrivacyClass, ProjectState, SemanticEvent, StateItem


PRIVACY_RANK = {
    PrivacyClass.PUBLIC: 0,
    PrivacyClass.PROJECT_INTERNAL: 1,
    PrivacyClass.SENSITIVE: 2,
    PrivacyClass.SECRET: 3,
}


class HandoverAuthorizationError(PermissionError):
    pass


class HandoverRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    authorized_by_user: bool = False
    reason: str = Field(min_length=1)
    target_platform: str = "generic"
    max_privacy_class: PrivacyClass = PrivacyClass.PROJECT_INTERNAL
    include_recent_events: int = Field(default=20, ge=0, le=500)


class HandoverCompiler:
    def compile(
        self,
        state: ProjectState,
        events: list[SemanticEvent],
        request: HandoverRequest,
        output_root: Path,
    ) -> Path:
        if not request.authorized_by_user:
            raise HandoverAuthorizationError(
                "human-facing handover compilation requires explicit user authorization"
            )

        output_dir = output_root / (
            f"handover-v{state.state_version:06d}-{state.state_hash[:12]}-"
            f"{self._safe_platform(request.target_platform)}"
        )
        if output_dir.exists():
            raise FileExistsError(f"handover already exists: {output_dir}")
        output_dir.mkdir(parents=True)

        filtered_state = self._filter_state(state, request.max_privacy_class)
        relevant_events = self._relevant_events(
            filtered_state,
            events,
            request.max_privacy_class,
            request.include_recent_events,
        )

        markdown_path = output_dir / "HANDOVER.md"
        state_path = output_dir / "state.yaml"
        events_path = output_dir / "events.jsonl"
        provenance_path = output_dir / "provenance.json"
        bootstrap_path = output_dir / f"{request.target_platform.upper()}-BOOTSTRAP.md"

        markdown_path.write_text(
            self._render_markdown(filtered_state, request), encoding="utf-8"
        )
        state_path.write_text(
            yaml.safe_dump(
                filtered_state.model_dump(mode="json"),
                sort_keys=False,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        events_path.write_text(
            "".join(canonical_json(event) + "\n" for event in relevant_events),
            encoding="utf-8",
        )
        provenance_path.write_text(
            json.dumps(self._provenance_map(filtered_state), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        bootstrap_path.write_text(
            self._render_bootstrap(filtered_state, request.target_platform), encoding="utf-8"
        )

        manifest = {
            "schema_version": "1.0",
            "compiled_at": utc_now().isoformat(),
            "project_id": state.project_id,
            "state_version": state.state_version,
            "state_hash": state.state_hash,
            "authorization_reason": request.reason,
            "target_platform": request.target_platform,
            "max_privacy_class": request.max_privacy_class.value,
            "files": {},
        }
        for path in (markdown_path, state_path, events_path, provenance_path, bootstrap_path):
            manifest["files"][path.name] = {"sha256": hash_file(path), "bytes": path.stat().st_size}
        (output_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return output_dir

    @staticmethod
    def _safe_platform(platform: str) -> str:
        safe = "".join(char.lower() if char.isalnum() else "-" for char in platform).strip("-")
        return safe or "generic"

    @staticmethod
    def _allowed(item: StateItem, maximum: PrivacyClass) -> bool:
        return PRIVACY_RANK[item.privacy_class] <= PRIVACY_RANK[maximum]

    def _filter_state(self, state: ProjectState, maximum: PrivacyClass) -> ProjectState:
        data = state.model_dump(mode="python")
        for attr in ("mission", "current_phase", "next_authorized_action"):
            item = getattr(state, attr)
            if item is not None and not self._allowed(item, maximum):
                data[attr] = None
        for attr in (
            "scope_included",
            "scope_excluded",
            "authority_sources",
            "active_decisions",
            "constraints",
            "verified_facts",
            "assumptions",
            "rejected_approaches",
            "open_questions",
            "blockers",
            "risks",
            "completed_outcomes",
            "continuity_warnings",
        ):
            data[attr] = {
                key: value.model_dump(mode="python")
                for key, value in getattr(state, attr).items()
                if self._allowed(value, maximum)
            }
        return ProjectState.model_validate(data)

    def _relevant_events(
        self,
        state: ProjectState,
        events: list[SemanticEvent],
        maximum: PrivacyClass,
        recent_count: int,
    ) -> list[SemanticEvent]:
        source_ids = set(self._source_event_ids(state))
        for conflict in state.conflicts.values():
            source_ids.update({conflict.existing_event, conflict.incoming_event})
        allowed = [
            event
            for event in events
            if PRIVACY_RANK[event.privacy_class] <= PRIVACY_RANK[maximum]
        ]
        recent_ids = {event.event_id for event in allowed[-recent_count:]} if recent_count else set()
        selected = [event for event in allowed if event.event_id in source_ids | recent_ids]
        selected_ids = {event.event_id for event in selected}
        changed = True
        while changed:
            changed = False
            for event in allowed:
                if event.event_id in selected_ids:
                    for target in event.supersedes:
                        if target not in selected_ids:
                            selected_ids.add(target)
                            changed = True
        return [event for event in allowed if event.event_id in selected_ids]

    @staticmethod
    def _source_event_ids(state: ProjectState) -> Iterable[str]:
        for attr in ("mission", "current_phase", "next_authorized_action"):
            item = getattr(state, attr)
            if item:
                yield item.source_event
        for attr in (
            "scope_included",
            "scope_excluded",
            "authority_sources",
            "active_decisions",
            "constraints",
            "verified_facts",
            "assumptions",
            "rejected_approaches",
            "open_questions",
            "blockers",
            "risks",
            "completed_outcomes",
            "continuity_warnings",
        ):
            for item in getattr(state, attr).values():
                yield item.source_event

    def _render_markdown(self, state: ProjectState, request: HandoverRequest) -> str:
        lines = [
            f"# Context Handover — {state.project_id}",
            "",
            f"State version: `{state.state_version}`  ",
            f"State hash: `{state.state_hash}`  ",
            f"Compilation reason: {request.reason}",
            "",
        ]
        self._single(lines, "Mission", state.mission)
        self._single(lines, "Current phase", state.current_phase)
        self._collection(lines, "Active decisions", state.active_decisions)
        self._collection(lines, "Constraints", state.constraints)
        self._collection(lines, "Authority", state.authority_sources)
        self._collection(lines, "Rejected approaches", state.rejected_approaches)
        self._collection(lines, "Verified facts", state.verified_facts)
        self._collection(lines, "Unverified assumptions", state.assumptions)
        self._collection(lines, "Open questions", state.open_questions)
        self._collection(lines, "Blockers", state.blockers)
        self._collection(lines, "Risks", state.risks)
        self._collection(lines, "Continuity warnings", state.continuity_warnings)
        self._conflicts(lines, state)
        self._collection(lines, "Completed outcomes", state.completed_outcomes)
        self._single(lines, "Next authorized action", state.next_authorized_action)
        lines.extend(
            [
                "## Continuation rules",
                "",
                "- Treat `state.yaml` as the current materialized view and `events.jsonl` as its evidence slice.",
                "- Do not revive rejected or superseded approaches without new evidence or explicit authority.",
                "- Preserve uncertainty labels; do not convert assumptions or inferred rationale into facts.",
                "- Verify the next action against current authority before making persistent changes.",
                "",
            ]
        )
        return "\n".join(lines)

    @staticmethod
    def _conflicts(lines: list[str], state: ProjectState) -> None:
        if not state.conflicts:
            return
        lines.extend(["## Unresolved state conflicts", ""])
        for conflict in sorted(state.conflicts.values(), key=lambda item: item.conflict_id):
            lines.append(
                f"- **{conflict.section.value}.{conflict.key}:** "
                f"`{conflict.existing_event}` says “{conflict.existing_summary}”; "
                f"`{conflict.incoming_event}` says “{conflict.incoming_summary}”. "
                f"Resolution required: {conflict.reason}."
            )
        lines.append("")

    @staticmethod
    def _single(lines: list[str], title: str, item: StateItem | None) -> None:
        if not item:
            return
        lines.extend([f"## {title}", "", f"**{item.summary}**"])
        if item.rationale:
            lines.append(f"\nWhy: {item.rationale}")
        lines.extend([f"\nSource event: `{item.source_event}`", ""])

    @staticmethod
    def _collection(lines: list[str], title: str, items: dict[str, StateItem]) -> None:
        if not items:
            return
        lines.extend([f"## {title}", ""])
        for key, item in sorted(items.items()):
            line = f"- **{key}:** {item.summary}"
            if item.rationale:
                line += f" — Why: {item.rationale}"
            line += f" (`{item.source_event}`)"
            lines.append(line)
        lines.append("")

    def _provenance_map(self, state: ProjectState) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for attr in ("mission", "current_phase", "next_authorized_action"):
            item = getattr(state, attr)
            if item:
                mapping[attr] = item.source_event
        for attr in (
            "scope_included",
            "scope_excluded",
            "authority_sources",
            "active_decisions",
            "constraints",
            "verified_facts",
            "assumptions",
            "rejected_approaches",
            "open_questions",
            "blockers",
            "risks",
            "completed_outcomes",
            "continuity_warnings",
        ):
            for key, item in getattr(state, attr).items():
                mapping[f"{attr}.{key}"] = item.source_event
        for conflict_id, conflict in state.conflicts.items():
            mapping[f"conflicts.{conflict_id}.existing"] = conflict.existing_event
            mapping[f"conflicts.{conflict_id}.incoming"] = conflict.incoming_event
        return mapping

    @staticmethod
    def _render_bootstrap(state: ProjectState, platform: str) -> str:
        return f"""# {platform.title()} continuation bootstrap

Load `HANDOVER.md`, then use `state.yaml` as the current project state and `events.jsonl` only when provenance or historical rationale is needed.

Rules:
1. Preserve the mission, active constraints, authority order, and rejected approaches.
2. Do not treat assumptions or inferred rationale as verified facts.
3. Continue only from the documented next authorized action.
4. Ask for authority only when a materially unresolved decision blocks progress.
5. Record new semantic decisions through the mneme adapter rather than rewriting prior events.

Project: `{state.project_id}`
State: `v{state.state_version}`
State hash: `{state.state_hash}`
"""
