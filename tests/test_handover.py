from __future__ import annotations

import json
from pathlib import Path

import pytest

from mneme.handover import (
    HandoverAuthorizationError,
    HandoverCompiler,
    HandoverRequest,
)
from mneme.models import PrivacyClass, StateSection
from mneme.reducer import ProjectStateReducer

from conftest import make_event


def test_handover_requires_user_authorization(store, tmp_path: Path):
    store.append_events([make_event()])
    state = ProjectStateReducer().reduce("demo", store.read_events())
    with pytest.raises(HandoverAuthorizationError):
        HandoverCompiler().compile(
            state,
            store.read_events(),
            HandoverRequest(authorized_by_user=False, reason="test"),
            tmp_path,
        )


def test_handover_package_contains_provenance(store, tmp_path: Path):
    store.append_events([make_event()])
    state = ProjectStateReducer().reduce("demo", store.read_events())
    output = HandoverCompiler().compile(
        state,
        store.read_events(),
        HandoverRequest(authorized_by_user=True, reason="fresh session", target_platform="chatgpt"),
        tmp_path,
    )
    assert (output / "HANDOVER.md").exists()
    assert (output / "state.yaml").exists()
    assert (output / "events.jsonl").exists()
    assert (output / "provenance.json").exists()
    assert (output / "CHATGPT-BOOTSTRAP.md").exists()
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["files"]["HANDOVER.md"]["sha256"]


def test_privacy_filter_excludes_sensitive_state(store, tmp_path: Path):
    store.append_events(
        [
            make_event(),
            make_event(
                round_id="round-2",
                section=StateSection.CONSTRAINTS,
                key="secret-token",
                summary="Use a secret token.",
                privacy=PrivacyClass.SECRET,
            ),
        ]
    )
    state = ProjectStateReducer().reduce("demo", store.read_events())
    output = HandoverCompiler().compile(
        state,
        store.read_events(),
        HandoverRequest(
            authorized_by_user=True,
            reason="safe transfer",
            max_privacy_class=PrivacyClass.PROJECT_INTERNAL,
        ),
        tmp_path,
    )
    handover = (output / "HANDOVER.md").read_text(encoding="utf-8")
    events = (output / "events.jsonl").read_text(encoding="utf-8")
    assert "secret-token" not in handover
    assert "secret-token" not in events
