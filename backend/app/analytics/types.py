"""Plain-data inputs/outputs for the analytics engine. Kept independent of
SQLAlchemy so scoring logic is pure and unit-testable without a database."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProspectFeatures:
    id: int
    name: str
    position: str
    college: str
    age: float | None
    class_year: str | None
    draft_year: int
    stats: dict[str, float] = field(default_factory=dict)
    stat_seasons: int = 0
    combine: dict[str, float] = field(default_factory=dict)
    projected_picks: list[float] = field(default_factory=list)

    @property
    def consensus_projected_pick(self) -> float | None:
        if not self.projected_picks:
            return None
        return sum(self.projected_picks) / len(self.projected_picks)


@dataclass
class ScoreBreakdown:
    score: float
    components: dict[str, float]
    notes: dict[str, str] = field(default_factory=dict)


@dataclass
class RiskProfile:
    overall_risk: float
    risk_level: str
    factors: dict[str, dict]  # factor -> {"score": float, "level": str}


@dataclass
class TeamFitBreakdown:
    score: float
    components: dict[str, float]
    explanations: dict[str, str]
