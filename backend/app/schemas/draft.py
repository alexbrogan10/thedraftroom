from pydantic import BaseModel


class RecommendRequest(BaseModel):
    team_id: int
    draft_year: int = 2026
    pick_number: int
    excluded_prospect_ids: list[int] = []


class RecommendedProspect(BaseModel):
    prospect_id: int
    name: str
    position: str
    draft_grade: float
    team_fit: float
    value_score: float
    risk_score: float
    is_primary: bool


class RecommendResponse(BaseModel):
    pick_number: int
    recommended: RecommendedProspect
    alternatives: list[RecommendedProspect]
    reasoning: str


class SimulateRequest(BaseModel):
    team_id: int
    draft_year: int = 2026
    pick_number: int
    drafted_prospect_ids: list[int] = []


class SimulatePick(BaseModel):
    prospect_id: int
    name: str
    position: str
    draft_grade: float
    team_fit: float
    value_score: float
    risk_score: float


class SimulateResponse(BaseModel):
    pick_number: int
    team_needs_snapshot: list[str]
    best_available: list[SimulatePick]
    remaining_prospect_count: int


class TradeOption(BaseModel):
    label: str
    pick_number: int
    picks_moved: int
    probability_target_available: float
    cost_value_points: float
    cost_description: str


class TradeAnalysisRequest(BaseModel):
    draft_year: int = 2026
    current_pick: int
    target_prospect_id: int
    alternative_picks: list[int] = []


class TradeAnalysisResponse(BaseModel):
    target_prospect_id: int
    target_name: str
    current_pick_option: TradeOption
    trade_up_options: list[TradeOption]
