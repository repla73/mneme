from __future__ import annotations

from mneme.models import EventType, StateSection
from mneme.reducer import ProjectStateReducer

from conftest import make_event


def test_reducer_materializes_current_state(store):
    event = store.append_events([make_event()])[0]
    state = ProjectStateReducer().reduce("demo", store.read_events())
    assert state.active_decisions["ledger"].source_event == event.event_id
    assert state.state_hash


def test_supersession_removes_old_event_effects(store):
    old = store.append_events(
        [make_event(summary="Generate one final summary.", rationale="Initial proposal.")]
    )[0]
    replacement = make_event(
        round_id="round-2",
        summary="Maintain a semantic ledger continuously.",
        rationale="Final summaries are too late.",
        event_type=EventType.DECISION_SUPERSEDED,
        supersedes=[old.event_id],
    )
    store.append_events([replacement])
    state = ProjectStateReducer().reduce("demo", store.read_events())
    assert state.active_decisions["ledger"].summary == "Maintain a semantic ledger continuously."
    assert state.state_version == 1


def test_remove_operation_clears_collection_item(store):
    first = store.append_events([make_event(section=StateSection.CONSTRAINTS, key="immutable")])[0]
    removal = make_event(
        round_id="round-2",
        event_type=EventType.CONSTRAINT_REMOVED,
        section=StateSection.CONSTRAINTS,
        key="immutable",
        action="remove",
        supersedes=[first.event_id],
    )
    store.append_events([removal])
    state = ProjectStateReducer().reduce("demo", store.read_events())
    assert "immutable" not in state.constraints


def test_competing_equal_authority_values_create_conflict(store):
    store.append_events([make_event(summary="Use final summaries.")])
    store.append_events([make_event(round_id="round-2", summary="Use continuous memory.")])
    state = ProjectStateReducer().reduce("demo", store.read_events())
    assert state.active_decisions["ledger"].summary == "Use final summaries."
    assert len(state.conflicts) == 1
    conflict = next(iter(state.conflicts.values()))
    assert conflict.incoming_summary == "Use continuous memory."


def test_higher_authority_can_replace_without_silent_conflict(store):
    low = make_event(summary="Use final summaries.")
    low.authority.level = "assistant_proposal"
    store.append_events([low])
    high = make_event(round_id="round-2", summary="Use continuous memory.")
    store.append_events([high])
    state = ProjectStateReducer().reduce("demo", store.read_events())
    assert state.active_decisions["ledger"].summary == "Use continuous memory."
    assert state.conflicts == {}
