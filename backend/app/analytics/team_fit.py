"""Team Fit engine: how well a prospect fits one specific organization,
independent of the prospect's league-wide talent grade."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.analytics.reference import POSITION_VALUE, compute_scheme_fit
from app.analytics.types import ProspectFeatures, TeamFitBreakdown

DEFAULT_TEAM_FIT_WEIGHTS = {
    "current_need": 0.30,
    "future_need": 0.15,
    "roster_depth": 0.15,
    "scheme_fit": 0.20,
    "development_timeline": 0.10,
    "positional_value": 0.10,
}


@dataclass
class TeamContext:
    team_id: int
    name: str
    abbreviation: str
    offensive_scheme: str
    defensive_scheme: str
    needs_by_position: dict[str, dict[int, float]] = field(default_factory=dict)
    roster_counts_by_position: dict[str, int] = field(default_factory=dict)
    roster_avg_age_by_position: dict[str, float] = field(default_factory=dict)


def compute_team_fit(
    prospect: ProspectFeatures,
    team: TeamContext,
    current_season: int,
    weights: dict[str, float] | None = None,
) -> TeamFitBreakdown:
    w = weights or DEFAULT_TEAM_FIT_WEIGHTS
    position = prospect.position
    season_needs = team.needs_by_position.get(position, {})

    current_need = season_needs.get(current_season, 50.0)
    future_seasons = [s for s in season_needs if s > current_season]
    future_need = (
        sum(season_needs[s] for s in future_seasons) / len(future_seasons)
        if future_seasons
        else current_need
    )

    existing_count = team.roster_counts_by_position.get(position, 1)
    roster_depth = max(0.0, 100 - existing_count * 25)

    scheme_fit = compute_scheme_fit(position, team.offensive_scheme, team.defensive_scheme)

    prospect_age = prospect.age if prospect.age is not None else 22.0
    roster_avg_age = team.roster_avg_age_by_position.get(position, 27.0)
    development_timeline = max(
        0.0, min(100.0, 70 + (roster_avg_age - 27) * 4 - (prospect_age - 22) * 3)
    )

    positional_value = float(POSITION_VALUE.get(position, 60))

    components = {
        "current_need": round(current_need, 1),
        "future_need": round(future_need, 1),
        "roster_depth": round(roster_depth, 1),
        "scheme_fit": round(scheme_fit, 1),
        "development_timeline": round(development_timeline, 1),
        "positional_value": round(positional_value, 1),
    }
    score = round(sum(components[k] * w[k] for k in components), 1)

    explanations = {
        "current_need": f"{team.abbreviation}'s current-season need at {position} ({current_need:.0f}/100).",
        "future_need": f"Projected {position} need over the following seasons ({future_need:.0f}/100).",
        "roster_depth": f"{existing_count} {position}(s) currently on the roster — more room scores higher.",
        "scheme_fit": f"Fit with {team.name}'s scheme "
        f"({team.offensive_scheme if position in {'QB','RB','WR','TE','OT','IOL'} else team.defensive_scheme}).",
        "development_timeline": "Compares prospect age to the roster's age at this position — "
        "favors young prospects behind aging veterans.",
        "positional_value": f"League-wide positional value assumption for {position} ({positional_value:.0f}/100).",
    }

    return TeamFitBreakdown(score=score, components=components, explanations=explanations)
