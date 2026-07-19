"""Local-first append-only storage with independently verifiable hash chains."""

from __future__ import annotations

import json
import os
import re
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Sequence, TypeVar

from pydantic import BaseModel, ValidationError

from .canonical import canonical_json, sha256_hex, utc_now
from .models import EventDraft, RoundReceipt, RoundReceiptDraft, SemanticEvent

try:  # pragma: no cover - platform fallback
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None

T = TypeVar("T", bound=BaseModel)


class LedgerError(RuntimeError):
    pass


class IntegrityError(LedgerError):
    pass


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    project_id: str

    @property
    def project_root(self) -> Path:
        return self.root / "projects" / self.project_id

    @property
    def ledger_dir(self) -> Path:
        return self.project_root / "ledger"

    @property
    def events(self) -> Path:
        return self.ledger_dir / "events.jsonl"

    @property
    def receipts(self) -> Path:
        return self.ledger_dir / "round-receipts.jsonl"

    @property
    def state_dir(self) -> Path:
        return self.project_root / "state"

    @property
    def state_current(self) -> Path:
        return self.state_dir / "current.json"

    @property
    def snapshots_dir(self) -> Path:
        return self.state_dir / "snapshots"

    @property
    def handovers_dir(self) -> Path:
        return self.project_root / "handovers"

    @property
    def policy(self) -> Path:
        return self.project_root / "policy.yaml"

    def initialize(self) -> None:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", self.project_id):
            raise LedgerError(
                "project_id must be 1-128 safe characters: letters, digits, dot, underscore, or hyphen"
            )
        for path in (
            self.ledger_dir,
            self.state_dir,
            self.snapshots_dir,
            self.handovers_dir,
            self.project_root / "provenance",
            self.project_root / "transcripts" / "encrypted",
        ):
            path.mkdir(parents=True, exist_ok=True)
        self.events.touch(exist_ok=True)
        self.receipts.touch(exist_ok=True)


@contextmanager
def _exclusive_file(path: Path) -> Iterator[object]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8", newline="\n") as handle:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield handle
        finally:
            handle.flush()
            os.fsync(handle.fileno())
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _record_hash(record: BaseModel) -> str:
    payload = record.model_dump(mode="python", exclude={"content_hash"})
    return sha256_hex(payload)


def _event_id(sequence: int) -> str:
    return f"EV-{sequence:08d}-{uuid.uuid4().hex[:12]}"


class LedgerStore:
    def __init__(self, paths: ProjectPaths):
        self.paths = paths
        self.paths.initialize()

    def _load_lines(self, path: Path, model: type[T]) -> list[T]:
        records: list[T] = []
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    records.append(model.model_validate_json(line))
                except (ValidationError, json.JSONDecodeError) as exc:
                    raise IntegrityError(f"invalid record at {path}:{line_number}: {exc}") from exc
        return records

    def read_events(self) -> list[SemanticEvent]:
        return self._load_lines(self.paths.events, SemanticEvent)

    def read_receipts(self) -> list[RoundReceipt]:
        return self._load_lines(self.paths.receipts, RoundReceipt)

    def append_events(self, drafts: Sequence[EventDraft]) -> list[SemanticEvent]:
        if not drafts:
            return []
        for draft in drafts:
            if draft.project_id != self.paths.project_id:
                raise LedgerError("event project_id does not match store")

        with _exclusive_file(self.paths.events) as handle:
            handle.seek(0)
            existing = [
                SemanticEvent.model_validate_json(line)
                for line in handle
                if line.strip()
            ]
            known_ids = {event.event_id for event in existing}
            previous_hash = existing[-1].content_hash if existing else None
            sequence = len(existing)
            created: list[SemanticEvent] = []

            for draft in drafts:
                unknown = set(draft.supersedes) - (known_ids | {e.event_id for e in created})
                if unknown:
                    raise LedgerError(f"supersedes unknown events: {sorted(unknown)}")
                sequence += 1
                payload = draft.model_dump(mode="python")
                event = SemanticEvent(
                    **payload,
                    event_id=_event_id(sequence),
                    sequence=sequence,
                    created_at=utc_now(),
                    previous_hash=previous_hash,
                    content_hash="0" * 64,
                )
                event.content_hash = _record_hash(event)
                previous_hash = event.content_hash
                created.append(event)

            handle.seek(0, os.SEEK_END)
            block = "".join(canonical_json(event) + "\n" for event in created)
            handle.write(block)
            return created

    def append_receipt(self, draft: RoundReceiptDraft) -> RoundReceipt:
        if draft.project_id != self.paths.project_id:
            raise LedgerError("receipt project_id does not match store")
        event_ids = {event.event_id for event in self.read_events()}
        unknown = set(draft.semantic_event_ids) - event_ids
        if unknown:
            raise LedgerError(f"receipt references unknown events: {sorted(unknown)}")

        with _exclusive_file(self.paths.receipts) as handle:
            handle.seek(0)
            existing = [RoundReceipt.model_validate_json(line) for line in handle if line.strip()]
            if any(receipt.round_id == draft.round_id for receipt in existing):
                raise LedgerError(f"round already processed: {draft.round_id}")
            previous_hash = existing[-1].content_hash if existing else None
            receipt = RoundReceipt(
                **draft.model_dump(mode="python"),
                sequence=len(existing) + 1,
                completed_at=utc_now(),
                previous_hash=previous_hash,
                content_hash="0" * 64,
            )
            receipt.content_hash = _record_hash(receipt)
            handle.seek(0, os.SEEK_END)
            handle.write(canonical_json(receipt) + "\n")
            return receipt

    def verify(self) -> dict[str, int | str]:
        events = self.read_events()
        receipts = self.read_receipts()
        self._verify_chain(events, "events")
        self._verify_chain(receipts, "receipts")

        event_ids = {event.event_id for event in events}
        if len(event_ids) != len(events):
            raise IntegrityError("duplicate event ids")
        for event in events:
            unknown = set(event.supersedes) - event_ids
            if unknown:
                raise IntegrityError(f"event {event.event_id} supersedes unknown ids: {unknown}")
            for target in event.supersedes:
                target_event = next(item for item in events if item.event_id == target)
                if target_event.sequence >= event.sequence:
                    raise IntegrityError("events may supersede only earlier events")

        receipt_rounds: set[str] = set()
        for receipt in receipts:
            if receipt.round_id in receipt_rounds:
                raise IntegrityError(f"duplicate round receipt: {receipt.round_id}")
            receipt_rounds.add(receipt.round_id)
            unknown = set(receipt.semantic_event_ids) - event_ids
            if unknown:
                raise IntegrityError(f"receipt references unknown events: {unknown}")

        return {
            "status": "valid",
            "events": len(events),
            "receipts": len(receipts),
            "event_head": events[-1].content_hash if events else "",
            "receipt_head": receipts[-1].content_hash if receipts else "",
        }

    @staticmethod
    def _verify_chain(records: Sequence[BaseModel], name: str) -> None:
        previous_hash = None
        for expected_sequence, record in enumerate(records, start=1):
            if getattr(record, "sequence") != expected_sequence:
                raise IntegrityError(f"{name} sequence gap at {expected_sequence}")
            if getattr(record, "previous_hash") != previous_hash:
                raise IntegrityError(f"{name} previous_hash mismatch at {expected_sequence}")
            expected_hash = _record_hash(record)
            if getattr(record, "content_hash") != expected_hash:
                raise IntegrityError(f"{name} content_hash mismatch at {expected_sequence}")
            previous_hash = expected_hash
