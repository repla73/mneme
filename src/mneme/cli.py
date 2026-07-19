"""Minimal command-line interface for the reference implementation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from .adapter import ExplicitEventExtractor, GenericRoundAdapter, RoundObservation
from .config import ProjectPolicy
from .handover import HandoverCompiler, HandoverRequest
from .models import EventDraft, PrivacyClass, ProjectState
from .platform import PlatformRegistry
from .reducer import ProjectStateReducer
from .retrieval import StateCapsuleBuilder
from .risk import ContextRiskSentinel, ContextSignals
from .storage import LedgerStore, ProjectPaths

app = typer.Typer(no_args_is_help=True, help="Mneme")


def _store(root: Path, project_id: str) -> LedgerStore:
    return LedgerStore(ProjectPaths(root=root, project_id=project_id))


@app.command()
def init(
    project_id: str,
    root: Annotated[Path, typer.Option()] = Path(".mneme"),
) -> None:
    store = _store(root, project_id)
    ProjectPolicy.load(store.paths.policy)
    typer.echo(str(store.paths.project_root))


@app.command("record-round")
def record_round(
    project_id: str,
    observation_file: Path,
    events_file: Path | None = None,
    root: Annotated[Path, typer.Option()] = Path(".mneme"),
) -> None:
    observation = RoundObservation.model_validate_json(observation_file.read_text(encoding="utf-8"))
    events: list[EventDraft] = []
    if events_file:
        raw = json.loads(events_file.read_text(encoding="utf-8"))
        events = [EventDraft.model_validate(item) for item in raw]
    adapter = GenericRoundAdapter(_store(root, project_id), ExplicitEventExtractor(events))
    created, receipt = adapter.ingest(observation)
    typer.echo(json.dumps({"events": [e.event_id for e in created], "receipt": receipt.round_id}))


@app.command()
def verify(
    project_id: str,
    root: Annotated[Path, typer.Option()] = Path(".mneme"),
) -> None:
    typer.echo(json.dumps(_store(root, project_id).verify(), indent=2))


@app.command()
def reduce(
    project_id: str,
    root: Annotated[Path, typer.Option()] = Path(".mneme"),
    snapshot: bool = False,
) -> None:
    store = _store(root, project_id)
    reducer = ProjectStateReducer()
    state = reducer.reduce(project_id, store.read_events())
    reducer.write_current(state, store.paths.state_current)
    output = {"state": str(store.paths.state_current), "version": state.state_version}
    if snapshot:
        output["snapshot"] = str(reducer.snapshot(state, store.paths.snapshots_dir))
    typer.echo(json.dumps(output, indent=2))


@app.command()
def capsule(
    project_id: str,
    query: str,
    root: Annotated[Path, typer.Option()] = Path(".mneme"),
    max_chars: int = 8_000,
) -> None:
    store = _store(root, project_id)
    state = ProjectState.model_validate_json(store.paths.state_current.read_text(encoding="utf-8"))
    typer.echo(StateCapsuleBuilder().build(state, query=query, max_chars=max_chars))


@app.command()
def risk(signals_file: Path) -> None:
    signals = ContextSignals.model_validate_json(signals_file.read_text(encoding="utf-8"))
    report = ContextRiskSentinel().assess(signals)
    typer.echo(report.model_dump_json(indent=2))


@app.command()
def handover(
    project_id: str,
    reason: str,
    target_platform: str = "generic",
    root: Annotated[Path, typer.Option()] = Path(".mneme"),
    authorized_by_user: Annotated[bool, typer.Option("--authorized-by-user")] = False,
    max_privacy_class: PrivacyClass = PrivacyClass.PROJECT_INTERNAL,
) -> None:
    store = _store(root, project_id)
    state = ProjectState.model_validate_json(store.paths.state_current.read_text(encoding="utf-8"))
    request = HandoverRequest(
        authorized_by_user=authorized_by_user,
        reason=reason,
        target_platform=target_platform,
        max_privacy_class=max_privacy_class,
    )
    output = HandoverCompiler().compile(
        state, store.read_events(), request, store.paths.handovers_dir
    )
    typer.echo(str(output))


@app.command("platforms")
def platforms() -> None:
    """List bundled platform adapter contracts."""
    rows = [
        {
            "platform_id": manifest.platform_id,
            "display_name": manifest.display_name,
            "surface": manifest.surface_kind.value,
            "strategy": manifest.strategy.value,
            "status": manifest.status.value,
        }
        for manifest in PlatformRegistry.bundled().list()
    ]
    typer.echo(json.dumps(rows, indent=2))


@app.command("platform")
def platform(platform_id: str) -> None:
    """Show one bundled platform adapter contract."""
    manifest = PlatformRegistry.bundled().get(platform_id)
    typer.echo(manifest.model_dump_json(indent=2))


if __name__ == "__main__":
    app()
