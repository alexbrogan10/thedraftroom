"""Bridges ORM data to the pure analytics engine, and assembles API-ready
results (Draft Grade board, team-specific board, per-prospect analytics)."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.analytics.reference import get_competition_level
from app.analytics.scoring import compute_draft_grade
from app.analytics.team_fit import TeamContext, compute_team_fit
from app.analytics.types import ProspectFeatures, RiskProfile, ScoreBreakdown
from app.analytics.value import ValueAssessment, compute_value_assessment
from app.config import get_draft_grade_weights
from app.models.historical import Player
from app.models.prospect import Prospect
from app.models.team import Team, TeamNeed, TeamRoster, TeamScheme

ROUND_PICK_ESTIMATE = {1: 16, 2: 48, 3: 80, 4: 112, 5: 144, 6: 176, 7: 208}


def _prospect_to_features(prospect: Prospect) -> ProspectFeatures:
    latest_by_metric: dict[str, tuple[int, float]] = {}
    for stat in prospect.statistics:
        current = latest_by_metric.get(stat.metric_name)
        if current is None or stat.season > current[0]:
            latest_by_metric[stat.metric_name] = (stat.season, stat.metric_value)
    stats = {k: v for k, (_, v) in latest_by_metric.items()}
    seasons = {s.season for s in prospect.statistics}

    combine = {}
    if prospect.combine_result:
        cr = prospect.combine_result
        for field in (
            "forty_yard_dash", "vertical_jump", "broad_jump",
            "bench_press", "three_cone", "shuttle",
        ):
            value = getattr(cr, field)
            if value is not None:
                combine[field] = value

    picks = []
    for proj in prospect.projections:
        if proj.projected_pick is not None:
            picks.append(float(proj.projected_pick))
        elif proj.projected_round is not None:
            picks.append(float(ROUND_PICK_ESTIMATE.get(proj.projected_round, 200)))

    return ProspectFeatures(
        id=prospect.id,
        name=prospect.name,
        position=prospect.position,
        college=prospect.college,
        age=prospect.age,
        class_year=prospect.class_year,
        draft_year=prospect.draft_year,
        stats=stats,
        stat_seasons=len(seasons),
        combine=combine,
        projected_picks=picks,
    )


@dataclass
class ProspectAnalytics:
    prospect: Prospect
    features: ProspectFeatures
    grade: ScoreBreakdown
    risk: RiskProfile
    league_rank: int = 0


def load_draft_class(db: Session, draft_year: int) -> list[ProspectAnalytics]:
    prospects = (
        db.query(Prospect)
        .filter(Prospect.draft_year == draft_year)
        .all()
    )
    weights = get_draft_grade_weights()
    features_list = [_prospect_to_features(p) for p in prospects]

    results: list[ProspectAnalytics] = []
    for prospect, features in zip(prospects, features_list):
        grade, risk = compute_draft_grade(features, features_list, weights)
        results.append(ProspectAnalytics(prospect=prospect, features=features, grade=grade, risk=risk))

    results.sort(key=lambda r: r.grade.score, reverse=True)
    for i, r in enumerate(results, start=1):
        r.league_rank = i
    return results


def get_expected_rank(features: ProspectFeatures) -> float | None:
    return features.consensus_projected_pick


def compute_value_for(analytics: ProspectAnalytics) -> ValueAssessment:
    expected_rank = get_expected_rank(analytics.features)
    return compute_value_assessment(analytics.league_rank, expected_rank)


def build_team_context(db: Session, team: Team, current_season: int) -> TeamContext:
    scheme = db.query(TeamScheme).filter(TeamScheme.team_id == team.id).first()
    needs = (
        db.query(TeamNeed)
        .filter(TeamNeed.team_id == team.id, TeamNeed.season >= current_season)
        .all()
    )
    needs_by_position: dict[str, dict[int, float]] = defaultdict(dict)
    for n in needs:
        needs_by_position[n.position][n.season] = n.need_score

    roster_rows = (
        db.query(TeamRoster, Player)
        .join(Player, TeamRoster.player_id == Player.id)
        .filter(TeamRoster.team_id == team.id, TeamRoster.season == current_season)
        .all()
    )
    counts: dict[str, int] = defaultdict(int)
    ages: dict[str, list[float]] = defaultdict(list)
    for roster_entry, player in roster_rows:
        counts[player.position] += 1
        if player.age is not None:
            ages[player.position].append(player.age)
    avg_ages = {pos: sum(vals) / len(vals) for pos, vals in ages.items()}

    return TeamContext(
        team_id=team.id,
        name=team.name,
        abbreviation=team.abbreviation,
        offensive_scheme=scheme.offensive_scheme if scheme else "Zone Run",
        defensive_scheme=scheme.defensive_scheme if scheme else "4-3 Zone",
        needs_by_position=dict(needs_by_position),
        roster_counts_by_position=dict(counts),
        roster_avg_age_by_position=avg_ages,
    )


def build_team_board_reason(
    prospect_name: str,
    position: str,
    team_name: str,
    league_rank: int,
    team_rank: int,
    fit_components: dict[str, float],
) -> str:
    if team_rank < league_rank:
        if fit_components.get("scheme_fit", 0) >= 85:
            return f"{prospect_name} fills an immediate need at {position} and projects as a strong scheme fit with {team_name}."
        return f"{prospect_name} fills a significant organizational need at {position} for {team_name}."
    if team_rank > league_rank:
        if fit_components.get("roster_depth", 100) < 50:
            return (
                f"{prospect_name} is highly talented but provides less organizational value to "
                f"{team_name} because the roster currently has significant depth at {position}."
            )
        return f"{prospect_name} grades well overall but is a lower priority need for {team_name} at this time."
    return f"{team_name}'s evaluation of {prospect_name} is closely aligned with the league-wide analytical ranking."
