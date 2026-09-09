from pydantic import BaseModel, ConfigDict


class CombineResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    forty_yard_dash: float | None = None
    vertical_jump: float | None = None
    broad_jump: float | None = None
    bench_press: float | None = None
    three_cone: float | None = None
    shuttle: float | None = None


class ProspectStatisticOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    season: int
    metric_name: str
    metric_value: float


class DraftProjectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source: str
    projected_pick: int | None = None
    projected_round: int | None = None


class ProspectSummary(BaseModel):
    """Lightweight prospect row used in list/board views."""

    id: int
    name: str
    position: str
    college: str
    age: float | None = None
    class_year: str | None = None
    draft_year: int
    draft_grade: float
    team_fit: float | None = None
    value_score: float
    risk_score: float
    risk_level: str
    confidence: float
    projected_pick: float | None = None


class ProspectDetail(BaseModel):
    id: int
    name: str
    position: str
    college: str
    age: float | None = None
    height_inches: float | None = None
    weight_lbs: float | None = None
    class_year: str | None = None
    draft_year: int
    combine: CombineResultOut | None = None
    statistics: list[ProspectStatisticOut] = []
    projections: list[DraftProjectionOut] = []


class ScoreBreakdownOut(BaseModel):
    score: float
    components: dict[str, float]
    notes: dict[str, str]


class RiskFactorOut(BaseModel):
    score: float
    level: str


class RiskProfileOut(BaseModel):
    overall_risk: float
    risk_level: str
    factors: dict[str, RiskFactorOut]


class TeamFitOut(BaseModel):
    team_id: int
    team_abbreviation: str
    score: float
    components: dict[str, float]
    explanations: dict[str, str]


class ValueAssessmentOut(BaseModel):
    analytical_rank: int
    expected_rank: float | None
    differential: float | None
    value_score: float
    classification: str
    icon: str
    explanation: str


class ProspectAnalyticsOut(BaseModel):
    prospect_id: int
    draft_grade: ScoreBreakdownOut
    risk: RiskProfileOut
    value: ValueAssessmentOut


class HistoricalComparisonOut(BaseModel):
    player_name: str
    position: str
    college: str | None
    draft_year: int
    similarity: float
    note: str = (
        "These players had similar measurable and production profiles entering the NFL."
    )
