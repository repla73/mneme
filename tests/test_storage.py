from __future__ import annotations

import json

import pytest

from mneme.adapter import ExplicitEventExtractor, GenericRoundAdapter, RoundObservation
from mneme.models import RoundReceiptDraft
from mneme.storage import IntegrityError, LedgerError

from conftest import make_event


def test_empty_round_receipt_is_recorded(store):
    observation = RoundObservation(
        project_id="demo",
        session_id="session-1",
        round_id="round-empty",
        user_text="Thanks.",
        assistant_text="Acknowledged.",
    )
    events, receipt = GenericRoundAdapter(store, ExplicitEventExtractor([])).ingest(observation)
    assert events == []
    assert receipt.semantic_event_ids == []
    assert store.verify()["status"] == "valid"


def test_append_and_verify_hash_chains(store):
    created = store.append_events([make_event()])
    store.append_receipt(
        RoundReceiptDraft(
            project_id="demo",
            session_id="session-1",
            round_id="round-1",
            source_hash="a" * 64,
            semantic_event_ids=[created[0].event_id],
        )
    )
    result = store.verify()
    assert result["events"] == 1
    assert result["receipts"] == 1


def test_tampering_is_detected(store):
    store.append_events([make_event()])
    path = store.paths.events
    record = json.loads(path.read_text(encoding="utf-8"))
    record["summary"] = "tampered"
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    with pytest.raises(IntegrityError, match="content_hash mismatch"):
        store.verify()


def test_unknown_supersession_is_rejected(store):
    with pytest.raises(LedgerError, match="unknown events"):
        store.append_events([make_event(supersedes=["EV-missing"])])


def test_duplicate_round_receipt_is_rejected(store):
    receipt = RoundReceiptDraft(
        project_id="demo",
        session_id="session-1",
        round_id="round-1",
        source_hash="b" * 64,
    )
    store.append_receipt(receipt)
    with pytest.raises(LedgerError, match="already processed"):
        store.append_receipt(receipt)


def test_project_id_blocks_path_traversal(tmp_path):
    from mneme.storage import LedgerStore, ProjectPaths

    with pytest.raises(LedgerError, match="safe characters"):
        LedgerStore(ProjectPaths(tmp_path, "../../escape"))
