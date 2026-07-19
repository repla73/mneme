from datetime import date

from mneme.platform import (
    AdapterStrategy,
    PlatformRegistry,
    SupportLevel,
    SurfaceKind,
)


def test_bundled_registry_contains_target_platforms():
    registry = PlatformRegistry.bundled()
    assert {manifest.platform_id for manifest in registry.list()} == {
        "antigravity",
        "chatgpt-web",
        "claude-code",
        "codex",
        "cursor",
        "gemini-web",
        "grok-web",
        "openclaw",
        "opencode",
        "pi",
    }


def test_web_platforms_use_companion_capture_not_native_hooks():
    registry = PlatformRegistry.bundled()
    for platform_id in ("chatgpt-web", "gemini-web", "grok-web"):
        manifest = registry.get(platform_id)
        assert manifest.surface_kind == SurfaceKind.WEB
        assert manifest.strategy == AdapterStrategy.BROWSER_COMPANION
        assert manifest.capabilities.completed_round_event == SupportLevel.COMPANION


def test_native_hook_platforms_claim_native_extension_runtime():
    registry = PlatformRegistry.bundled()
    for platform_id in ("codex", "claude-code", "antigravity"):
        manifest = registry.get(platform_id)
        assert manifest.capabilities.local_extension_runtime == SupportLevel.NATIVE


def test_every_manifest_has_primary_source_and_capture_contract():
    for manifest in PlatformRegistry.bundled().list():
        assert manifest.source_urls
        assert all(url.startswith("https://") for url in manifest.source_urls)
        assert manifest.capture_contract
        assert manifest.handover_contract


def test_every_manifest_records_evidence_date():
    for manifest in PlatformRegistry.bundled().list():
        assert manifest.evidence_checked_at == date(2026, 7, 20)
