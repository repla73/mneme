from __future__ import annotations

import json
from pathlib import Path

from mneme.adapter import RoundObservation
from mneme.handover import HandoverRequest
from mneme.models import EventDraft, ProjectState, RoundReceipt, SemanticEvent
from mneme.platform import PlatformManifest
from mneme.risk import ContextSignals, RiskReport

MODELS = {
    "event-draft": EventDraft,
    "semantic-event": SemanticEvent,
    "round-receipt": RoundReceipt,
    "round-observation": RoundObservation,
    "project-state": ProjectState,
    "context-signals": ContextSignals,
    "risk-report": RiskReport,
    "handover-request": HandoverRequest,
    "platform-manifest": PlatformManifest,
}

root = Path(__file__).resolve().parents[1] / "schemas"
root.mkdir(parents=True, exist_ok=True)
for name, model in MODELS.items():
    (root / f"{name}.schema.json").write_text(
        json.dumps(model.model_json_schema(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
print(f"exported {len(MODELS)} schemas to {root}")
