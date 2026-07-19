"""Deterministic reducer from immutable semantic events to current project state."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from .canonical import canonical_json, sha256_hex, utc_now
from .models import (
    ProjectState,
    SemanticEvent,
    StateAction,
    StateConflict,
    StateItem,
    StateSection,
)


class ReductionError(RuntimeError):
    pass


SINGULAR_SECTIONS = {
    StateSection.MISSION: "mission",
    StateSection.CURRENT_PHASE: "current_phase",
    StateSection.NEXT_AUTHORIZED_ACTION: "next_authorized_action",
}

COLLECTION_SECTIONS = {
    StateSection.SCOPE_INCLUDED: "scope_included",
    StateSection.SCOPE_EXCLUDED: "scope_excluded",
    StateSection.AUTHORITY_SOURCES: "authority_sources",
    StateSection.ACTIVE_DECISIONS: "active_decisions",
    StateSection.CONSTRAINTS: "constraints",
    StateSection.VERIFIED_FACTS: "verified_facts",
    StateSection.ASSUMPTIONS: "assumptions",
    StateSection.REJECTED_APPROACHES: "rejected_approaches",
    StateSection.OPEN_QUESTIONS: "open_questions",
    StateSection.BLOCKERS: "blockers",
    StateSection.RISKS: "risks",
    StateSection.COMPLETED_OUTCOMES: "completed_outcomes",
    StateSection.CONTINUITY_WARNINGS: "continuity_warnings",
}


AUTHORITY_PRIORITY = {
    "assistant_inference": 10,
    "assistant_proposal": 20,
    "accepted_decision": 30,
    "verified_evidence": 40,
    "canonical_artifact": 50,
    "user_instruction": 60,
    "explicit_user_approval": 70,
}


class ProjectStateReducer:
    def reduce(self, project_id: str, events: list[SemanticEvent]) -> ProjectState:
        ordered = sorted(events, key=lambda event: event.sequence)
        if any(event.project_id != project_id for event in ordered):
            raise ReductionError("event project mismatch")

        event_by_id = {event.event_id: event for event in ordered}
        superseded: set[str] = set()
        for event in ordered:
            for target in event.supersedes:
                if target not in event_by_id:
                    raise ReductionError(f"unknown superseded event: {target}")
                if event_by_id[target].sequence >= event.sequence:
                    raise ReductionError("supersession must point backward")
                superseded.add(target)

        state = ProjectState(
            project_id=project_id,
            state_version=0,
            derived_through_sequence=0,
            generated_at=utc_now(),
        )

        for event in ordered:
            if event.event_id in superseded:
                continue
            for operation in event.state_operations:
                self._apply(state, event, operation)
            state.state_version += 1
            state.derived_through_sequence = event.sequence
            state.derived_through_event = event.event_id

        state.generated_at = utc_now()
        state_payload = state.model_dump(mode="python", exclude={"state_hash", "generated_at"})
        state.state_hash = sha256_hex(state_payload)
        return state

    @staticmethod
    def _apply(state: ProjectState, event: SemanticEvent, operation: object) -> None:
        section = operation.section
        if section in SINGULAR_SECTIONS:
            attr = SINGULAR_SECTIONS[section]
            existing = getattr(state, attr)
            if operation.action == StateAction.REMOVE:
                if existing and not ProjectStateReducer._may_replace(existing, event):
                    ProjectStateReducer._record_conflict(state, section, operation.key, existing, event, "lower or equal authority attempted removal without explicit supersession")
                    return
                setattr(state, attr, None)
                return
            incoming = ProjectStateReducer._item(event, operation.key, operation.value)
            if existing and existing.summary != incoming.summary and not ProjectStateReducer._may_replace(existing, event):
                ProjectStateReducer._record_conflict(state, section, operation.key, existing, event, "competing singular state values lack authoritative supersession")
                return
            setattr(state, attr, incoming)
            return

        if section not in COLLECTION_SECTIONS:
            raise ReductionError(f"unsupported section: {section}")
        attr = COLLECTION_SECTIONS[section]
        collection = deepcopy(getattr(state, attr))
        existing = collection.get(operation.key)
        if operation.action == StateAction.REMOVE:
            if existing and not ProjectStateReducer._may_replace(existing, event):
                ProjectStateReducer._record_conflict(state, section, operation.key, existing, event, "lower or equal authority attempted removal without explicit supersession")
                return
            collection.pop(operation.key, None)
        else:
            incoming = ProjectStateReducer._item(event, operation.key, operation.value)
            if existing and existing.summary != incoming.summary and not ProjectStateReducer._may_replace(existing, event):
                ProjectStateReducer._record_conflict(state, section, operation.key, existing, event, "competing active values lack authoritative supersession")
                return
            collection[operation.key] = incoming
        setattr(state, attr, collection)

    @staticmethod
    def _may_replace(existing: StateItem, incoming_event: SemanticEvent) -> bool:
        if existing.source_event in incoming_event.supersedes:
            return True
        existing_priority = AUTHORITY_PRIORITY[existing.authority.level.value]
        incoming_priority = AUTHORITY_PRIORITY[incoming_event.authority.level.value]
        return incoming_priority > existing_priority

    @staticmethod
    def _record_conflict(
        state: ProjectState,
        section: StateSection,
        key: str,
        existing: StateItem,
        incoming_event: SemanticEvent,
        reason: str,
    ) -> None:
        incoming_summary = incoming_event.summary
        for operation in incoming_event.state_operations:
            if operation.section == section and operation.key == key and operation.value is not None:
                incoming_summary = operation.value.summary
                break
        conflict_id = f"{section.value}:{key}:{existing.source_event}:{incoming_event.event_id}"
        state.conflicts[conflict_id] = StateConflict(
            conflict_id=conflict_id,
            section=section,
            key=key,
            existing_event=existing.source_event,
            incoming_event=incoming_event.event_id,
            existing_summary=existing.summary,
            incoming_summary=incoming_summary,
            reason=reason,
        )

    @staticmethod
    def _item(event: SemanticEvent, key: str, value: object) -> StateItem:
        if value is None:
            raise ReductionError("state value missing")
        return StateItem(
            key=key,
            summary=value.summary,
            details=value.details,
            rationale=value.rationale,
            status=value.status,
            confidence=value.confidence,
            source_event=event.event_id,
            authority=event.authority,
            privacy_class=event.privacy_class,
            updated_at=event.created_at,
        )

    def write_current(self, state: ProjectState, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(canonical_json(state) + "\n", encoding="utf-8")
        temporary.replace(path)

    def snapshot(self, state: ProjectState, directory: Path) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / f"state-v{state.state_version:06d}-{state.state_hash[:12]}.json"
        if not target.exists():
            target.write_text(canonical_json(state) + "\n", encoding="utf-8")
        return target
