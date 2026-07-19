from __future__ import annotations

from pathlib import Path

import pytest

from mneme.models import (
    Authority,
    AuthorityLevel,
    EventDraft,
    EventType,
    PrivacyClass,
    RationaleClaim,
    RationaleStatus,
    SemanticDelta,
    StateAction,
    StateOperation,
    StateSection,
    StateValue,
    WhyRecord,
)
from mneme.storage import LedgerStore, ProjectPaths


@pytest.fixture
def store(tmp_path: Path) -> LedgerStore:
    return LedgerStore(ProjectPaths(tmp_path / ".continuity", "demo"))


def make_event(
    *,
    round_id: str = "round-1",
    subject: str = "architecture",
    event_type: EventType = EventType.DECISION_ACCEPTED,
    section: StateSection = StateSection.ACTIVE_DECISIONS,
    key: str = "ledger",
    summary: str = "Use an append-only semantic ledger.",
    rationale: str = "Preserve why decisions were made.",
    privacy: PrivacyClass = PrivacyClass.PROJECT_INTERNAL,
    supersedes: list[str] | None = None,
    action: StateAction = StateAction.UPSERT,
) -> EventDraft:
    value = None
    if action != StateAction.REMOVE:
        value = StateValue(summary=summary, rationale=rationale)
    return EventDraft(
        project_id="demo",
        session_id="session-1",
        round_id=round_id,
        event_type=event_type,
        subject=subject,
        summary=summary,
        semantic_delta=SemanticDelta(after=summary),
        why=WhyRecord(
            trigger="Long sessions degrade.",
            rationale=[
                RationaleClaim(
                    text=rationale,
                    status=RationaleStatus.EXPLICIT,
                    evidence_refs=[f"message:{round_id}"],
                )
            ],
        ),
        authority=Authority(
            actor="user",
            level=AuthorityLevel.EXPLICIT_USER_APPROVAL,
            source_ref=f"message:{round_id}",
        ),
        confidence=1.0,
        privacy_class=privacy,
        supersedes=supersedes or [],
        state_operations=[
            StateOperation(action=action, section=section, key=key, value=value)
        ],
    )
