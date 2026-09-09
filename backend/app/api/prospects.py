from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.analytics.scoring import compute_production_score
from app.analytics.team_fit import compute_team_fit
from app.database import get_db
from app.ml.comparisons import HistoricalCandidate, find_similar_players
from app.ml.outcome_model import models_available, predict_probabilities
from app.models.historical import HistoricalDraftResult
from app.models.prospect import Prospect
from app.models.team import Team
from app.schemas.prospect import (
    CombineResultOut,
    DraftProjectionOut,
    HistoricalComparisonOut,
    ProspectAnalyticsOut,
    ProspectDetail,
    ProspectStatisticOut,
    ProspectSummary,
    RiskProfileOut,
    ScoreBreakdownOut,
    TeamFitOut,
    ValueAssessmentOut,
)
from app.services.analytics_service import (
    build_team_context,
    compute_value_for,
    load_draft_class,
)

router = APIRouter(prefix="/api/prospects", tags=["prospects"])


def _get_prospect_or_404(db: Session, prospect_id: int) -> Prospect:
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if prospect is None:
        raise HTTPException(status_code=404, detail="Prospect not found")
    return prospect


@router.get("", response_model=list[ProspectSummary])
def list_prospects(
    db: Session = Depends(get_db),
    draft_year: int = Query(2026),
    position: str | None = None,
    college: str | None = None,
    min_age: float | None = None,
    max_age: float | None = None,
    min_draft_grade: float | None = None,
    max_risk: float | None = None,
    projected_round: int | None = None,
    sort_by: str = Query("draft_grade", pattern="^(draft_grade|team_fit|value_score|risk_score|projected_pick)$"),
    descending: bool = True,
    limit: int = 200,
):
    class_analytics = load_draft_class(db, draft_year)

    rows = []
    for a in class_analytics:
        if position and a.prospect.position != position:
            continue
        if college and college.lower() not in a.prospect.college.lower():
            continue
        if min_age is not None and (a.prospect.age or 0) < min_age:
            continue
        if max_age is not None and (a.prospect.age or 99) > max_age:
            continue
        if min_draft_grade is not None and a.grade.score < min_draft_grade:
            continue
        if max_risk is not None and a.risk.overall_risk > max_risk:
            continue
        if projected_round is not None:
            rounds = [p.projected_round for p in a.prospect.projections if p.projected_round]
            if not rounds or min(rounds) != projected_round:
                continue

        value = compute_value_for(a)
        confidence = round(
            100 - (a.risk.factors["production_risk"]["score"] * 0.4
                   + a.risk.factors["projection_risk"]["score"] * 0.6) / 1, 1
        )
        confidence = max(0.0, min(100.0, confidence))
        rows.append(
            ProspectSummary(
                id=a.prospect.id,
                name=a.prospect.name,
                position=a.prospect.position,
                college=a.prospect.college,
                age=a.prospect.age,
                class_year=a.prospect.class_year,
                draft_year=a.prospect.draft_year,
                draft_grade=a.grade.score,
                team_fit=None,
                value_score=value.value_score,
                risk_score=a.risk.overall_risk,
                risk_level=a.risk.risk_level,
                confidence=confidence,
                projected_pick=a.features.consensus_projected_pick,
            )
        )

    key_map = {
        "draft_grade": lambda r: r.draft_grade,
        "team_fit": lambda r: r.team_fit or 0,
        "value_score": lambda r: r.value_score,
        "risk_score": lambda r: r.risk_score,
        "projected_pick": lambda r: r.projected_pick or 999,
    }
    rows.sort(key=key_map[sort_by], reverse=descending)
    return rows[:limit]


@router.get("/{prospect_id}", response_model=ProspectDetail)
def get_prospect(prospect_id: int, db: Session = Depends(get_db)):
    prospect = _get_prospect_or_404(db, prospect_id)
    return ProspectDetail(
        id=prospect.id,
        name=prospect.name,
        position=prospect.position,
        college=prospect.college,
        age=prospect.age,
        height_inches=prospect.height_inches,
        weight_lbs=prospect.weight_lbs,
        class_year=prospect.class_year,
        draft_year=prospect.draft_year,
        combine=CombineResultOut.model_validate(prospect.combine_result)
        if prospect.combine_result
        else None,
        statistics=[ProspectStatisticOut.model_validate(s) for s in prospect.statistics],
        projections=[DraftProjectionOut.model_validate(p) for p in prospect.projections],
    )


@router.get("/{prospect_id}/analytics", response_model=ProspectAnalyticsOut)
def get_prospect_analytics(prospect_id: int, db: Session = Depends(get_db)):
    prospect = _get_prospect_or_404(db, prospect_id)
    class_analytics = load_draft_class(db, prospect.draft_year)
    match = next((a for a in class_analytics if a.prospect.id == prospect_id), None)
    if match is None:
        raise HTTPException(status_code=404, detail="Prospect analytics unavailable")

    value = compute_value_for(match)
    return ProspectAnalyticsOut(
        prospect_id=prospect_id,
        draft_grade=ScoreBreakdownOut(
            score=match.grade.score, components=match.grade.components, notes=match.grade.notes
        ),
        risk=RiskProfileOut(
            overall_risk=match.risk.overall_risk,
            risk_level=match.risk.risk_level,
            factors=match.risk.factors,
        ),
        value=ValueAssessmentOut(
            analytical_rank=value.analytical_rank,
            expected_rank=value.expected_rank,
            differential=value.differential,
            value_score=value.value_score,
            classification=value.classification,
            icon=value.icon,
            explanation=value.explanation,
        ),
    )


@router.get("/{prospect_id}/risk", response_model=RiskProfileOut)
def get_prospect_risk(prospect_id: int, db: Session = Depends(get_db)):
    analytics = get_prospect_analytics(prospect_id, db)
    return analytics.risk


@router.get("/{prospect_id}/team-fit", response_model=TeamFitOut)
def get_prospect_team_fit(
    prospect_id: int, team_id: int = Query(...), season: int | None = None, db: Session = Depends(get_db)
):
    prospect = _get_prospect_or_404(db, prospect_id)
    team = db.query(Team).filter(Team.id == team_id).first()
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    class_analytics = load_draft_class(db, prospect.draft_year)
    match = next((a for a in class_analytics if a.prospect.id == prospect_id), None)

    current_season = season or prospect.draft_year
    team_context = build_team_context(db, team, current_season)
    fit = compute_team_fit(match.features, team_context, current_season)

    return TeamFitOut(
        team_id=team.id,
        team_abbreviation=team.abbreviation,
        score=fit.score,
        components=fit.components,
        explanations=fit.explanations,
    )


@router.get("/{prospect_id}/comparisons", response_model=list[HistoricalComparisonOut])
def get_prospect_comparisons(prospect_id: int, db: Session = Depends(get_db)):
    prospect = _get_prospect_or_404(db, prospect_id)
    class_analytics = load_draft_class(db, prospect.draft_year)
    match = next((a for a in class_analytics if a.prospect.id == prospect_id), None)

    peer_group = [
        a.features for a in class_analytics
        if a.prospect.position == prospect.position and a.prospect.id != prospect.id
    ]
    production_score, _ = compute_production_score(match.features, peer_group)

    prospect_record = {
        "position": prospect.position,
        "age": prospect.age,
        "height_inches": prospect.height_inches,
        "weight_lbs": prospect.weight_lbs,
        "forty_yard_dash": prospect.combine_result.forty_yard_dash if prospect.combine_result else None,
        "college_production_score": production_score,
    }

    historical_rows = (
        db.query(HistoricalDraftResult)
        .filter(HistoricalDraftResult.position == prospect.position)
        .all()
    )
    candidates = [
        HistoricalCandidate(
            player_name=h.player_name,
            position=h.position,
            college=h.college,
            draft_year=h.draft_year,
            age=h.age,
            height_inches=h.height_inches,
            weight_lbs=h.weight_lbs,
            forty_yard_dash=h.forty_yard_dash,
            college_production_score=h.college_production_score,
        )
        for h in historical_rows
    ]

    results = find_similar_players(prospect_record, candidates, top_n=3)
    return [
        HistoricalComparisonOut(
            player_name=r.player_name,
            position=r.position,
            college=r.college,
            draft_year=r.draft_year,
            similarity=r.similarity,
        )
        for r in results
    ]


@router.get("/{prospect_id}/outcome-prediction")
def get_prospect_outcome_prediction(prospect_id: int, db: Session = Depends(get_db)):
    """
    Model-estimated probabilities (NOT guarantees) that this prospect reaches
    each outcome tier, from a scikit-learn model trained only on pre-draft
    information. See docs/model_documentation.md.
    """
    prospect = _get_prospect_or_404(db, prospect_id)
    if not models_available():
        return {
            "available": False,
            "message": "Outcome prediction models have not been trained yet.",
        }

    class_analytics = load_draft_class(db, prospect.draft_year)
    match = next((a for a in class_analytics if a.prospect.id == prospect_id), None)
    peer_group = [
        a.features for a in class_analytics
        if a.prospect.position == prospect.position and a.prospect.id != prospect.id
    ]
    production_score, _ = compute_production_score(match.features, peer_group)

    consensus_pick = match.features.consensus_projected_pick
    draft_round = round((consensus_pick - 1) // 32 + 1) if consensus_pick else None

    feature_row = {
        "age": prospect.age,
        "height_inches": prospect.height_inches,
        "weight_lbs": prospect.weight_lbs,
        "forty_yard_dash": prospect.combine_result.forty_yard_dash if prospect.combine_result else None,
        "college_production_score": production_score,
        "draft_pick": consensus_pick,
        "draft_round": draft_round,
        "position": prospect.position,
    }
    probabilities = predict_probabilities(feature_row)
    return {
        "available": probabilities is not None,
        "probabilities": probabilities,
        "note": "Model estimate based on pre-draft data only. Not a guarantee of NFL outcome.",
    }
