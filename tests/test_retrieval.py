from mneme.reducer import ProjectStateReducer
from mneme.retrieval import StateCapsuleBuilder

from conftest import make_event


def test_capsule_is_bounded_and_contains_authoritative_state(store):
    store.append_events([make_event()])
    state = ProjectStateReducer().reduce("demo", store.read_events())
    capsule = StateCapsuleBuilder().build(state, "ledger decision", max_chars=300)
    assert len(capsule) <= 300
    assert "append-only semantic ledger" in capsule
    assert "source=" in capsule
