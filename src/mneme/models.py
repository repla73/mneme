"""Typed contracts for semantic events, receipts, and materialized project state."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class EventType(StrEnum):
    OBJECTIVE_CHANGED = "objective_changed"
    SCOPE_CHANGED = "scope_changed"
    CONSTRAINT_ADDED = "constraint_added"
    CONSTRAINT_REMOVED = "constraint_removed"
    DECISION_PROPOSED = "decision_proposed"
    DECISION_ACCEPTED = "decision_accepted"
    DECISION_REJECTED = "decision_rejected"
    DECISION_SUPERSEDED = "decision_superseded"
    CLARIFICATION_RESOLVED = "clarification_resolved"
    ASSUMPTION_RECORDED = "assumption_recorded"
    ASSUMPTION_INVALIDATED = "assumption_invalidated"
    EVIDENCE_ADDED = "evidence_added"
    AUTHORITY_CHANGED = "authority_changed"
    BLOCKER_OPENED = "blocker_opened"
    BLOCKER_RESOLVED = "blocker_resolved"
    ACTION_AUTHORIZED = "action_authorized"
    ACTION_COMPLETED = "action_completed"
    CORRECTION_ISSUED = "correction_issued"
    RISK_IDENTIFIED = "risk_identified"
    RISK_RESOLVED = "risk_resolved"
    CONTINUITY_WARNING = "continuity_warning"


class RationaleStatus(StrEnum):
    EXPLICIT = "explicit"
    DERIVED = "derived"
    INFERRED = "inferred"


class AuthorityLevel(StrEnum):
    EXPLICIT_USER_APPROVAL = "explicit_user_approval"
    USER_INSTRUCTION = "user_instruction"
    CANONICAL_ARTIFACT = "canonical_artifact"
    VERIFIED_EVIDENCE = "verified_evidence"
    ACCEPTED_DECISION = "accepted_decision"
    ASSISTANT_PROPOSAL = "assistant_proposal"
    ASSISTANT_INFERENCE = "assistant_inference"


class PrivacyClass(StrEnum):
    PUBLIC = "public"
    PROJECT_INTERNAL = "project_internal"
    SENSITIVE = "sensitive"
    SECRET = "secret"


class StateAction(StrEnum):
    SET = "set"
    UPSERT = "upsert"
    REMOVE = "remove"


class StateSection(StrEnum):
    MISSION = "mission"
    CURRENT_PHASE = "current_phase"
    SCOPE_INCLUDED = "scope_included"
    SCOPE_EXCLUDED = "scope_excluded"
    AUTHORITY_SOURCES = "authority_sources"
    ACTIVE_DECISIONS = "active_decisions"
    CONSTRAINTS = "constraints"
    VERIFIED_FACTS = "verified_facts"
    ASSUMPTIONS = "assumptions"
    REJECTED_APPROACHES = "rejected_approaches"
    OPEN_QUESTIONS = "open_questions"
    BLOCKERS = "blockers"
    RISKS = "risks"
    COMPLETED_OUTCOMES = "completed_outcomes"
    NEXT_AUTHORIZED_ACTION = "next_authorized_action"
    CONTINUITY_WARNINGS = "continuity_warnings"


class ProvenanceRef(StrictModel):
    privacy_class: PrivacyClass = PrivacyClass.PROJECT_INTERNAL
    ref_id: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    locator: str | None = None
    content_hash: str | None = None
    excerpt: str | None = None


class SemanticDelta(StrictModel):
    before: str | None = None
    after: str = Field(min_length=1)


class RationaleClaim(StrictModel):
    text: str = Field(min_length=1)
    status: RationaleStatus
    evidence_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_claim(self) -> "RationaleClaim":
        if self.status == RationaleStatus.INFERRED and self.confidence >= 1.0:
            raise ValueError("inferred rationale must not claim certainty")
        if self.status == RationaleStatus.EXPLICIT and not self.evidence_refs:
            raise ValueError("explicit rationale requires at least one evidence reference")
        return self


class RejectedAlternative(StrictModel):
    alternative: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)


class WhyRecord(StrictModel):
    trigger: str = Field(min_length=1)
    rationale: list[RationaleClaim] = Field(min_length=1)
    alternatives_rejected: list[RejectedAlternative] = Field(default_factory=list)
    consequences: list[str] = Field(default_factory=list)


class Authority(StrictModel):
    actor: str = Field(min_length=1)
    level: AuthorityLevel
    source_ref: str | None = None


class StateValue(StrictModel):
    summary: str = Field(min_length=1)
    details: dict[str, Any] = Field(default_factory=dict)
    rationale: str | None = None
    status: str = "active"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class StateOperation(StrictModel):
    action: StateAction
    section: StateSection
    key: str = Field(min_length=1)
    value: StateValue | None = None

    @model_validator(mode="after")
    def validate_operation(self) -> "StateOperation":
        if self.action in {StateAction.SET, StateAction.UPSERT} and self.value is None:
            raise ValueError("set/upsert operations require value")
        if self.action == StateAction.REMOVE and self.value is not None:
            raise ValueError("remove operations must not include value")
        return self


class EventDraft(StrictModel):
    project_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    round_id: str = Field(min_length=1)
    event_type: EventType
    subject: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    semantic_delta: SemanticDelta | None = None
    why: WhyRecord | None = None
    constraints: list[str] = Field(default_factory=list)
    authority: Authority
    provenance: list[ProvenanceRef] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    privacy_class: PrivacyClass = PrivacyClass.PROJECT_INTERNAL
    supersedes: list[str] = Field(default_factory=list)
    state_operations: list[StateOperation] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    @field_validator("supersedes")
    @classmethod
    def unique_supersedes(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("supersedes must not contain duplicates")
        return value

    @model_validator(mode="after")
    def privacy_covers_provenance(self) -> "EventDraft":
        rank = {
            PrivacyClass.PUBLIC: 0,
            PrivacyClass.PROJECT_INTERNAL: 1,
            PrivacyClass.SENSITIVE: 2,
            PrivacyClass.SECRET: 3,
        }
        if any(rank[ref.privacy_class] > rank[self.privacy_class] for ref in self.provenance):
            raise ValueError("event privacy_class must cover all provenance references")
        return self


class SemanticEvent(EventDraft):
    schema_version: str = "1.0"
    event_id: str = Field(min_length=1)
    sequence: int = Field(ge=1)
    created_at: datetime
    previous_hash: str | None = None
    content_hash: str = Field(min_length=64, max_length=64)


class RoundReceiptDraft(StrictModel):
    project_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    round_id: str = Field(min_length=1)
    source_hash: str = Field(min_length=64, max_length=64)
    semantic_event_ids: list[str] = Field(default_factory=list)
    user_message_ref: str | None = None
    assistant_message_ref: str | None = None
    observer_version: str = "generic-adapter/0.1"
    notes: str | None = None


class RoundReceipt(RoundReceiptDraft):
    schema_version: str = "1.0"
    sequence: int = Field(ge=1)
    completed_at: datetime
    previous_hash: str | None = None
    content_hash: str = Field(min_length=64, max_length=64)


class StateItem(StrictModel):
    key: str
    summary: str
    details: dict[str, Any] = Field(default_factory=dict)
    rationale: str | None = None
    status: str = "active"
    confidence: float = Field(ge=0.0, le=1.0)
    source_event: str
    authority: Authority
    privacy_class: PrivacyClass
    updated_at: datetime


class StateConflict(StrictModel):
    conflict_id: str
    section: StateSection
    key: str
    existing_event: str
    incoming_event: str
    existing_summary: str
    incoming_summary: str
    reason: str
    status: str = "unresolved"


class ProjectState(StrictModel):
    schema_version: str = "1.0"
    project_id: str
    state_version: int = Field(ge=0)
    derived_through_sequence: int = Field(ge=0)
    derived_through_event: str | None = None
    generated_at: datetime
    state_hash: str = ""
    mission: StateItem | None = None
    current_phase: StateItem | None = None
    next_authorized_action: StateItem | None = None
    scope_included: dict[str, StateItem] = Field(default_factory=dict)
    scope_excluded: dict[str, StateItem] = Field(default_factory=dict)
    authority_sources: dict[str, StateItem] = Field(default_factory=dict)
    active_decisions: dict[str, StateItem] = Field(default_factory=dict)
    constraints: dict[str, StateItem] = Field(default_factory=dict)
    verified_facts: dict[str, StateItem] = Field(default_factory=dict)
    assumptions: dict[str, StateItem] = Field(default_factory=dict)
    rejected_approaches: dict[str, StateItem] = Field(default_factory=dict)
    open_questions: dict[str, StateItem] = Field(default_factory=dict)
    blockers: dict[str, StateItem] = Field(default_factory=dict)
    risks: dict[str, StateItem] = Field(default_factory=dict)
    completed_outcomes: dict[str, StateItem] = Field(default_factory=dict)
    continuity_warnings: dict[str, StateItem] = Field(default_factory=dict)
    conflicts: dict[str, StateConflict] = Field(default_factory=dict)
