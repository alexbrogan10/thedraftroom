from pydantic import BaseModel


class TeamOut(BaseModel):
    id: int
    name: str
    abbreviation: str
    conference: str
    division: str


class TeamNeedOut(BaseModel):
    position: str
    season: int
    need_score: float


class BoardEntry(BaseModel):
    prospect_id: int
    name: str
    position: str
    college: str
    league_rank: int
    team_rank: int | None = None
    draft_grade: float
    team_fit: float | None = None
    value_score: float
    value_classification: str
    value_icon: str
    expected_rank: float | None = None
    risk_score: float
    risk_level: str
    reason: str | None = None


class DraftRecommendation(BaseModel):
    prospect_id: int
    name: str
    position: str
    draft_grade: float
    team_fit: float
    value_score: float
    risk_score: float
    rank: int
    is_primary: bool
    reasoning: str
