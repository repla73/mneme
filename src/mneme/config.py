"""Project policy loading and defaults."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from .models import PrivacyClass


class ProjectPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capsule_max_chars: int = Field(default=8_000, ge=500, le=100_000)
    handover_max_privacy_class: PrivacyClass = PrivacyClass.PROJECT_INTERNAL
    handover_recent_events: int = Field(default=20, ge=0, le=500)
    state_snapshot_every_events: int = Field(default=25, ge=1)
    risk_warning_rounds_without_checkpoint: int = Field(default=80, ge=1)

    @classmethod
    def load(cls, path: Path) -> "ProjectPolicy":
        if not path.exists():
            policy = cls()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                yaml.safe_dump(policy.model_dump(mode="json"), sort_keys=False),
                encoding="utf-8",
            )
            return policy
        return cls.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
