"""Context-degradation risk estimation without fabricated precision."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class RiskLevel(StrEnum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class ContextSignals(BaseModel):
    model_config = ConfigDict(extra="forbid")

    used_tokens: int | None = Field(default=None, ge=0)
    context_window: int | None = Field(default=None, gt=0)
    token_metrics_authoritative: bool = False
    compaction_count: int = Field(default=0, ge=0)
    rounds_since_checkpoint: int = Field(default=0, ge=0)
    accumulated_tool_result_chars: int = Field(default=0, ge=0)
    reopened_settled_questions: int = Field(default=0, ge=0)
    forgotten_constraints: int = Field(default=0, ge=0)
    user_memory_corrections: int = Field(default=0, ge=0)
    unresolved_state_conflicts: int = Field(default=0, ge=0)


class RiskReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    level: RiskLevel
    score: int = Field(ge=0, le=100)
    reasons: list[str]
    recommendation: str
    authoritative_usage_ratio: float | None = None


class ContextRiskSentinel:
    def assess(self, signals: ContextSignals) -> RiskReport:
        score = 0
        reasons: list[str] = []
        usage_ratio: float | None = None

        if (
            signals.token_metrics_authoritative
            and signals.used_tokens is not None
            and signals.context_window is not None
        ):
            usage_ratio = signals.used_tokens / signals.context_window
            if usage_ratio >= 0.85:
                score += 60
                reasons.append("authoritative context usage is at or above the red threshold")
            elif usage_ratio >= 0.70:
                score += 35
                reasons.append("authoritative context usage is at or above the warning threshold")
        elif signals.used_tokens is not None or signals.context_window is not None:
            reasons.append("token figures are non-authoritative and were not used as an exact meter")

        score += min(signals.compaction_count * 12, 24)
        score += min(signals.rounds_since_checkpoint // 40 * 8, 16)
        score += min(signals.accumulated_tool_result_chars // 200_000 * 6, 18)
        score += min(signals.reopened_settled_questions * 15, 30)
        score += min(signals.forgotten_constraints * 20, 40)
        score += min(signals.user_memory_corrections * 12, 36)
        score += min(signals.unresolved_state_conflicts * 18, 36)
        score = min(score, 100)

        if signals.rounds_since_checkpoint >= 40:
            reasons.append(f"rounds since checkpoint: {signals.rounds_since_checkpoint}")
        if signals.accumulated_tool_result_chars >= 200_000:
            reasons.append(
                f"accumulated tool-result characters: {signals.accumulated_tool_result_chars}"
            )

        behavioral = {
            "compaction_count": signals.compaction_count,
            "reopened settled questions": signals.reopened_settled_questions,
            "forgotten constraints": signals.forgotten_constraints,
            "user memory corrections": signals.user_memory_corrections,
            "unresolved state conflicts": signals.unresolved_state_conflicts,
        }
        reasons.extend(f"{name}: {value}" for name, value in behavioral.items() if value)

        if score >= 60:
            level = RiskLevel.RED
            recommendation = (
                "Preserve a machine safety snapshot, avoid starting a large new work unit, "
                "and request user authorization to compile a handover."
            )
        elif score >= 30:
            level = RiskLevel.YELLOW
            recommendation = (
                "Rebuild and verify consolidated state; suggest a checkpoint when convenient."
            )
        else:
            level = RiskLevel.GREEN
            recommendation = "Continue normally; no handover prompt is required."

        return RiskReport(
            level=level,
            score=score,
            reasons=reasons,
            recommendation=recommendation,
            authoritative_usage_ratio=usage_ratio,
        )
