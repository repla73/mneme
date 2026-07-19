"""Capability-driven platform adapter registry."""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from importlib.resources import files
from pathlib import Path
from typing import Iterable

import yaml
from pydantic import Field, model_validator

from .models import StrictModel


class SurfaceKind(StrEnum):
    WEB = "web"
    CODING_AGENT = "coding_agent"
    AGENT_RUNTIME = "agent_runtime"


class SupportLevel(StrEnum):
    NATIVE = "native"
    COMPANION = "companion"
    COOPERATIVE = "cooperative"
    ABSENT = "absent"
    UNKNOWN = "unknown"


class AdapterStrategy(StrEnum):
    BROWSER_COMPANION = "browser_companion"
    NATIVE_HOOKS = "native_hooks"
    PLUGIN = "plugin"
    CLI_STREAM = "cli_stream"
    SKILL_ONLY = "skill_only"
    HYBRID = "hybrid"


class ImplementationStatus(StrEnum):
    PLANNED = "planned"
    DESIGN_READY = "design_ready"
    IMPLEMENTING = "implementing"
    AVAILABLE = "available"
    BLOCKED = "blocked"


class CapabilitySet(StrictModel):
    user_prompt_event: SupportLevel
    completed_round_event: SupportLevel
    tool_events: SupportLevel
    pre_compaction_event: SupportLevel
    post_compaction_event: SupportLevel
    exact_context_metrics: SupportLevel
    persistent_transcript: SupportLevel
    custom_commands: SupportLevel
    external_tool_api: SupportLevel
    local_extension_runtime: SupportLevel
    background_write: SupportLevel
    user_authorization_prompt: SupportLevel


class PlatformManifest(StrictModel):
    schema_version: str = "1.0"
    platform_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    display_name: str = Field(min_length=1)
    surface_kind: SurfaceKind
    strategy: AdapterStrategy
    status: ImplementationStatus
    evidence_checked_at: date
    capabilities: CapabilitySet
    capture_contract: list[str] = Field(min_length=1)
    handover_contract: list[str] = Field(min_length=1)
    limitations: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_strategy(self) -> "PlatformManifest":
        if self.surface_kind == SurfaceKind.WEB:
            if self.capabilities.completed_round_event == SupportLevel.NATIVE:
                raise ValueError("web manifests may not claim a native completed-round hook")
            if self.strategy not in {
                AdapterStrategy.BROWSER_COMPANION,
                AdapterStrategy.HYBRID,
                AdapterStrategy.SKILL_ONLY,
            }:
                raise ValueError("web manifests require a browser, hybrid, or skill strategy")
        if self.strategy == AdapterStrategy.NATIVE_HOOKS:
            if self.capabilities.local_extension_runtime != SupportLevel.NATIVE:
                raise ValueError("native hook strategy requires a native extension runtime")
        return self


class PlatformRegistry:
    def __init__(self, manifests: Iterable[PlatformManifest]):
        by_id: dict[str, PlatformManifest] = {}
        for manifest in manifests:
            if manifest.platform_id in by_id:
                raise ValueError(f"duplicate platform_id: {manifest.platform_id}")
            by_id[manifest.platform_id] = manifest
        self._by_id = by_id

    @classmethod
    def bundled(cls) -> "PlatformRegistry":
        directory = files("mneme").joinpath("platforms")
        manifests = []
        for resource in sorted(directory.iterdir(), key=lambda item: item.name):
            if resource.name.endswith(".yaml"):
                manifests.append(PlatformManifest.model_validate(yaml.safe_load(resource.read_text())))
        return cls(manifests)

    @classmethod
    def from_directory(cls, directory: Path) -> "PlatformRegistry":
        manifests = [
            PlatformManifest.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
            for path in sorted(directory.glob("*.yaml"))
        ]
        return cls(manifests)

    def get(self, platform_id: str) -> PlatformManifest:
        try:
            return self._by_id[platform_id]
        except KeyError as exc:
            raise KeyError(f"unknown platform: {platform_id}") from exc

    def list(self) -> list[PlatformManifest]:
        return [self._by_id[key] for key in sorted(self._by_id)]
