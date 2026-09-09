from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.analytics.draft_capital import (
    availability_probability,
    nearest_round_label,
    traditional_value,
)
from app.analytics.team_fit import compute_team_fit
from app.database import get_db
from app.models.team import Team, TeamNeed
from app.schemas.draft import (
    RecommendedProspect,
    RecommendRequest,
    RecommendResponse,
    SimulatePick,
    SimulateRequest,
    SimulateResponse,
    TradeAnalysisRequest,
    TradeAnalysisResponse,
    TradeOption,
)
from app.schemas.team import BoardEntry
from app.services.analytics_service import (
    build_team_context,
    compute_value_for,
    load_draft_class,
)

router = APIRouter(prefix="/api/draft", tags=["draft"])


@router.get("/board", response_model=list[BoardEntry])
def get_league_board(draft_year: int = Query(2026), limit: int = 100, db: Session = Depends(get_db)):
    class_analytics = load_draft_class(db, draft_year)
    results = []
    for a in class_analytics[:limit]:
        value = compute_value_for(a)
        results.append(
            BoardEntry(
                prospect_id=a.prospect.id,
                name=a.prospect.name,
                position=a.prospect.position,
                college=a.prospect.college,
                league_rank=a.league_rank,
                team_rank=None,
                draft_grade=a.grade.score,
                team_fit=None,
                value_score=value.value_score,
                value_classification=value.classification,
                value_icon=value.icon,
                expected_rank=value.expected_rank,
                risk_score=a.risk.overall_risk,
                risk_level=a.risk.risk_level,
                reason=None,
            )
        )
    return results


def _ranked_team_board(db: Session, team: Team, draft_year: int, excluded_ids: set[int]):
    class_analytics = [a for a in load_draft_class(db, draft_year) if a.prospect.id not in excluded_ids]
    team_context = build_team_context(db, team, draft_year)
    scored = []
    for a in class_analytics:
        fit = compute_team_fit(a.features, team_context, draft_year)
        team_board_score = round(0.5 * a.grade.score + 0.5 * fit.score, 2)
        scored.append((a, fit, team_board_score))
    scored.sort(key=lambda e: e[2], reverse=True)
    return scored


def _reasoning(top, second) -> str:
    top_a, top_fit, _ = top
    second_a, second_fit, _ = second
    grade_gap = top_a.grade.score - second_a.grade.score
    fit_gap = top_fit.score - second_fit.score
    if grade_gap < 0 and fit_gap > abs(grade_gap):
        return (
            f"{top_a.prospect.name} is recommended because the team-fit advantage outweighs "
            f"the small difference in overall prospect grade compared to {second_a.prospect.name}."
        )
    if grade_gap >= 0:
        return (
            f"{top_a.prospect.name} is recommended based on the higher overall Draft Grade "
            f"and a comparable or better team fit than {second_a.prospect.name}."
        )
    return (
        f"{top_a.prospect.name} is recommended as the best balance of talent and organizational "
        f"fit available at this pick."
    )


@router.post("/recommend", response_model=RecommendResponse)
def recommend_pick(req: RecommendRequest, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == req.team_id).first()
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    scored = _ranked_team_board(db, team, req.draft_year, set(req.excluded_prospect_ids))
    if not scored:
        raise HTTPException(status_code=404, detail="No available prospects for this draft class")

    def to_out(entry, is_primary: bool) -> RecommendedProspect:
        a, fit, _ = entry
        value = compute_value_for(a)
        return RecommendedProspect(
            prospect_id=a.prospect.id,
            name=a.prospect.name,
            position=a.prospect.position,
            draft_grade=a.grade.score,
            team_fit=fit.score,
            value_score=value.value_score,
            risk_score=a.risk.overall_risk,
            is_primary=is_primary,
        )

    top3 = scored[:3]
    reasoning = _reasoning(top3[0], top3[1]) if len(top3) > 1 else "Best available prospect by combined talent and team fit."

    return RecommendResponse(
        pick_number=req.pick_number,
        recommended=to_out(top3[0], True),
        alternatives=[to_out(e, False) for e in top3[1:]],
        reasoning=reasoning,
    )


@router.post("/simulate", response_model=SimulateResponse)
def simulate_pick(req: SimulateRequest, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == req.team_id).first()
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    excluded = set(req.drafted_prospect_ids)
    scored = _ranked_team_board(db, team, req.draft_year, excluded)

    needs = (
        db.query(TeamNeed)
        .filter(TeamNeed.team_id == team.id, TeamNeed.season == req.draft_year)
        .order_by(TeamNeed.need_score.desc())
        .limit(3)
        .all()
    )

    best_available = []
    for a, fit, _ in scored[:5]:
        value = compute_value_for(a)
        best_available.append(
            SimulatePick(
                prospect_id=a.prospect.id,
                name=a.prospect.name,
                position=a.prospect.position,
                draft_grade=a.grade.score,
                team_fit=fit.score,
                value_score=value.value_score,
                risk_score=a.risk.overall_risk,
            )
        )

    return SimulateResponse(
        pick_number=req.pick_number,
        team_needs_snapshot=[n.position for n in needs],
        best_available=best_available,
        remaining_prospect_count=len(scored),
    )


@router.post("/trade-analysis", response_model=TradeAnalysisResponse)
def trade_analysis(req: TradeAnalysisRequest, db: Session = Depends(get_db)):
    class_analytics = load_draft_class(db, req.draft_year)
    match = next((a for a in class_analytics if a.prospect.id == req.target_prospect_id), None)
    if match is None:
        raise HTTPException(status_code=404, detail="Prospect not found in this draft class")

    consensus = match.features.consensus_projected_pick
    spread = None
    if len(match.features.projected_picks) >= 2:
        picks = match.features.projected_picks
        spread = (max(picks) - min(picks)) / 2

    current_value = traditional_value(req.current_pick)
    current_option = TradeOption(
        label=f"Stay at #{req.current_pick}",
        pick_number=req.current_pick,
        picks_moved=0,
        probability_target_available=availability_probability(req.current_pick, consensus, spread),
        cost_value_points=0.0,
        cost_description="No trade cost — current draft position.",
    )

    trade_up_options = []
    for pick in sorted(set(req.alternative_picks)):
        if pick >= req.current_pick:
            continue
        cost = round(traditional_value(pick) - current_value, 1)
        trade_up_options.append(
            TradeOption(
                label=f"Trade to #{pick}",
                pick_number=pick,
                picks_moved=req.current_pick - pick,
                probability_target_available=availability_probability(pick, consensus, spread),
                cost_value_points=cost,
                cost_description=f"Estimated cost: {nearest_round_label(cost)} (approximate, Traditional Value model).",
            )
        )

    return TradeAnalysisResponse(
        target_prospect_id=match.prospect.id,
        target_name=match.prospect.name,
        current_pick_option=current_option,
        trade_up_options=trade_up_options,
    )
