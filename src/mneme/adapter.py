"""Platform-neutral adapter contracts and a generic explicit-event adapter."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from .canonical import sha256_hex
from .models import EventDraft, RoundReceipt, RoundReceiptDraft, SemanticEvent
from .storage import LedgerStore


class RoundObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str
    session_id: str
    round_id: str
    user_text: str
    assistant_text: str
    tool_evidence_refs: list[str] = Field(default_factory=list)
    user_message_ref: str | None = None
    assistant_message_ref: str | None = None


class SemanticExtractor(Protocol):
    def extract(self, observation: RoundObservation) -> list[EventDraft]:
        """Return zero or more semantic deltas for one completed round."""


class ExplicitEventExtractor:
    """Reference extractor used when an adapter already has typed event candidates."""

    def __init__(self, events: list[EventDraft]):
        self.events = events

    def extract(self, observation: RoundObservation) -> list[EventDraft]:
        return list(self.events)


class GenericRoundAdapter:
    def __init__(self, store: LedgerStore, extractor: SemanticExtractor):
        self.store = store
        self.extractor = extractor

    def ingest(self, observation: RoundObservation) -> tuple[list[SemanticEvent], RoundReceipt]:
        if observation.project_id != self.store.paths.project_id:
            raise ValueError("observation project_id does not match store")
        drafts = self.extractor.extract(observation)
        for draft in drafts:
            if (
                draft.project_id != observation.project_id
                or draft.session_id != observation.session_id
                or draft.round_id != observation.round_id
            ):
                raise ValueError("extracted event identity does not match observation")
        events = self.store.append_events(drafts)
        source_hash = sha256_hex(
            {
                "project_id": observation.project_id,
                "session_id": observation.session_id,
                "round_id": observation.round_id,
                "user_text": observation.user_text,
                "assistant_text": observation.assistant_text,
                "tool_evidence_refs": observation.tool_evidence_refs,
            }
        )
        receipt = self.store.append_receipt(
            RoundReceiptDraft(
                project_id=observation.project_id,
                session_id=observation.session_id,
                round_id=observation.round_id,
                source_hash=source_hash,
                semantic_event_ids=[event.event_id for event in events],
                user_message_ref=observation.user_message_ref,
                assistant_message_ref=observation.assistant_message_ref,
            )
        )
        return events, receipt
