from mneme.reducer import ProjectStateReducer

from conftest import make_event


def test_replay_is_deterministic_except_generation_time(store):
    store.append_events([make_event()])
    events = store.read_events()
    first = ProjectStateReducer().reduce("demo", events)
    second = ProjectStateReducer().reduce("demo", events)
    assert first.state_hash == second.state_hash
    assert first.model_dump(exclude={"generated_at"}) == second.model_dump(exclude={"generated_at"})
