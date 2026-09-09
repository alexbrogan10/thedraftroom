from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.analytics.team_fit import compute_team_fit
from app.database import get_db
from app.models.team import Team, TeamNeed
from app.schemas.team import BoardEntry, TeamNeedOut, TeamOut
from app.services.analytics_service import (
    build_team_board_reason,
    build_team_context,
    compute_value_for,
    load_draft_class,
)

router = APIRouter(prefix="/api/teams", tags=["teams"])


@router.get("", response_model=list[TeamOut])
def list_teams(db: Session = Depends(get_db)):
    return db.query(Team).order_by(Team.name).all()


@router.get("/{team_id}/needs", response_model=list[TeamNeedOut])
def get_team_needs(team_id: int, season: int | None = None, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    query = db.query(TeamNeed).filter(TeamNeed.team_id == team_id)
    if season is not None:
        query = query.filter(TeamNeed.season == season)
    needs = query.order_by(TeamNeed.season, TeamNeed.need_score.desc()).all()
    return [TeamNeedOut(position=n.position, season=n.season, need_score=n.need_score) for n in needs]


@router.get("/{team_id}/draft-board", response_model=list[BoardEntry])
def get_team_draft_board(
    team_id: int,
    draft_year: int = Query(2026),
    limit: int = 50,
    db: Session = Depends(get_db),
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    class_analytics = load_draft_class(db, draft_year)
    team_context = build_team_context(db, team, draft_year)

    entries = []
    for a in class_analytics:
        fit = compute_team_fit(a.features, team_context, draft_year)
        team_board_score = round(0.5 * a.grade.score + 0.5 * fit.score, 2)
        entries.append((a, fit, team_board_score))

    entries.sort(key=lambda e: e[2], reverse=True)

    results = []
    for team_rank, (a, fit, _) in enumerate(entries[:limit], start=1):
        reason = build_team_board_reason(
            a.prospect.name, a.prospect.position, team.name, a.league_rank, team_rank, fit.components
        )
        value = compute_value_for(a)
        results.append(
            BoardEntry(
                prospect_id=a.prospect.id,
                name=a.prospect.name,
                position=a.prospect.position,
                college=a.prospect.college,
                league_rank=a.league_rank,
                team_rank=team_rank,
                draft_grade=a.grade.score,
                team_fit=fit.score,
                value_score=value.value_score,
                value_classification=value.classification,
                value_icon=value.icon,
                expected_rank=value.expected_rank,
                risk_score=a.risk.overall_risk,
                risk_level=a.risk.risk_level,
                reason=reason,
            )
        )
    return results
