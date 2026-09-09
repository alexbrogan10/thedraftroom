"""
Core analytical scoring engine: Draft Grade, Risk Profile, and the shared
percentile utilities they're built on.

Design principle: every score is a documented, inspectable combination of
sub-scores — never an opaque single number. See docs/scoring_methodology.md.
"""
from __future__ import annotations

import statistics

from app.analytics.reference import (
    COMBINE_METRIC_WEIGHTS,
    LOWER_IS_BETTER,
    POSITION_VALUE,
    PRODUCTION_METRIC_WEIGHTS,
    get_competition_level,
)
from app.analytics.types import ProspectFeatures, RiskProfile, ScoreBreakdown
from app.config import DraftGradeWeights

# Position-level proxy for how volatile/uncertain draft projections have
# historically been for the position group. 0-100, higher = more uncertainty.
# A documented modeling assumption, not derived from this app's own dataset.
POSITION_PROJECTION_RISK = {
    "QB": 60, "RB": 45, "WR": 45, "TE": 40,
    "OT": 30, "IOL": 30, "EDGE": 35, "IDL": 35,
    "LB": 35, "CB": 45, "S": 40,
}


def percentile_rank(value: float, population: list[float]) -> float:
    """Percentage of the population at or below `value`. 50.0 with no peers."""
    if not population:
        return 50.0
    at_or_below = sum(1 for v in population if v <= value)
    return round(100 * at_or_below / len(population), 2)


def _weighted_percentile_score(
    values: dict[str, float],
    weights: dict[str, float],
    peer_values: dict[str, list[float]],
    invert: set[str] = frozenset(),
) -> tuple[float, dict[str, float]]:
    """Blend several metrics into one 0-100 "goodness" score using each
    metric's percentile rank among peers, weighted by |weight| and flipped
    for metrics where a lower raw value is better."""
    total_weight = 0.0
    weighted_sum = 0.0
    per_metric: dict[str, float] = {}

    for metric, weight in weights.items():
        if metric not in values or values[metric] is None:
            continue
        peers = peer_values.get(metric, [])
        pct = percentile_rank(values[metric], peers)
        goodness = (100 - pct) if (metric in invert) != (weight < 0) else pct
        per_metric[metric] = goodness
        weighted_sum += abs(weight) * goodness
        total_weight += abs(weight)

    if total_weight == 0:
        return 50.0, per_metric
    return round(weighted_sum / total_weight, 2), per_metric


def compute_production_score(
    prospect: ProspectFeatures, peer_group: list[ProspectFeatures]
) -> tuple[float, dict[str, float]]:
    weights = PRODUCTION_METRIC_WEIGHTS.get(prospect.position, {})
    peer_values = {
        metric: [p.stats[metric] for p in peer_group if metric in p.stats]
        for metric in weights
    }
    return _weighted_percentile_score(prospect.stats, weights, peer_values)


def compute_athletic_score(
    prospect: ProspectFeatures, peer_group: list[ProspectFeatures]
) -> tuple[float, dict[str, float]]:
    weights = COMBINE_METRIC_WEIGHTS.get(prospect.position, {})
    peer_values = {
        metric: [p.combine[metric] for p in peer_group if metric in p.combine]
        for metric in weights
    }
    return _weighted_percentile_score(
        prospect.combine, weights, peer_values, invert=LOWER_IS_BETTER
    )


def compute_age_experience_score(prospect: ProspectFeatures) -> float:
    age = prospect.age if prospect.age is not None else 21.5
    base = 100 - max(0, age - 20) * 12
    bonus = {
        "Fr": -8, "RS-Fr": -8, "So": -2, "RS-So": -2,
        "Jr": 3, "RS-Jr": 3, "Sr": 6, "RS-Sr": 6,
    }.get(prospect.class_year or "", 0)
    return round(min(100, max(0, base + bonus)), 2)


def compute_position_value_score(position: str) -> float:
    return float(POSITION_VALUE.get(position, 60))


def compute_nfl_projection_score(
    production_score: float,
    athletic_score: float,
    prospect: ProspectFeatures,
    draft_class: list[ProspectFeatures],
) -> tuple[float, str]:
    """
    MVP heuristic projection: a transparent blend of demonstrated production,
    measured athleticism, and where the broader scouting community (consensus
    of `draft_projections` sources) expects the player drafted, on the theory
    that consensus projection already encodes tape/scouting information this
    app does not itself observe.

    This is deliberately a heuristic, not a trained model, for the MVP. Phase
    4 replaces/augments it with a scikit-learn outcome-probability model
    trained on historical, pre-draft-only features (see app/ml/).
    """
    consensus = prospect.consensus_projected_pick
    all_picks = [
        p.consensus_projected_pick
        for p in draft_class
        if p.consensus_projected_pick is not None
    ]
    if consensus is not None and all_picks:
        # Earlier projected pick = better; invert so goodness rises with rank.
        consensus_pct = 100 - percentile_rank(consensus, all_picks)
        note = "blend of production, athletic testing, and scouting consensus"
    else:
        consensus_pct = (production_score + athletic_score) / 2
        note = "blend of production and athletic testing (no consensus projection available)"

    score = round(0.4 * production_score + 0.3 * athletic_score + 0.3 * consensus_pct, 2)
    return score, note


def compute_risk_profile(
    prospect: ProspectFeatures,
    production_score: float,
    athletic_score: float,
    weights_context: dict | None = None,
) -> RiskProfile:
    weights = PRODUCTION_METRIC_WEIGHTS.get(prospect.position, {})
    completeness = (
        len([m for m in weights if m in prospect.stats]) / len(weights)
        if weights
        else 0.5
    )
    production_risk = round(
        max(0, min(100, 100 - (0.6 * completeness * 100 + 0.4 * production_score))), 1
    )

    if len(prospect.projected_picks) >= 2:
        spread = statistics.pstdev(prospect.projected_picks)
        projection_risk = round(min(100, (spread / 30) * 100), 1)
    elif len(prospect.projected_picks) == 1:
        projection_risk = 50.0
    else:
        projection_risk = 65.0

    competition_level = get_competition_level(prospect.college)
    competition_risk = round(100 - competition_level, 1)

    athletic_dependency_risk = round(
        max(15.0, min(100.0, (athletic_score - production_score) * 2)), 1
    )

    position_risk = float(POSITION_PROJECTION_RISK.get(prospect.position, 40))

    factors = {
        "production_risk": production_risk,
        "projection_risk": projection_risk,
        "competition_risk": competition_risk,
        "athletic_dependency_risk": athletic_dependency_risk,
        "position_risk": position_risk,
    }
    overall = round(sum(factors.values()) / len(factors), 1)

    def level(v: float) -> str:
        if v < 34:
            return "Low"
        if v < 67:
            return "Moderate"
        return "High"

    return RiskProfile(
        overall_risk=overall,
        risk_level={"Low": "LOWER RISK", "Moderate": "MODERATE RISK", "High": "HIGHER RISK"}[
            level(overall)
        ],
        factors={k: {"score": v, "level": level(v)} for k, v in factors.items()},
    )


def compute_draft_grade(
    prospect: ProspectFeatures,
    draft_class: list[ProspectFeatures],
    weights: DraftGradeWeights,
) -> tuple[ScoreBreakdown, RiskProfile]:
    """Assembles the full explainable Draft Grade (0-100) for one prospect
    against its draft class peer group (same position, same draft year)."""
    peer_group = [
        p for p in draft_class if p.position == prospect.position and p.id != prospect.id
    ]

    production_score, production_detail = compute_production_score(prospect, peer_group)
    athletic_score, athletic_detail = compute_athletic_score(prospect, peer_group)
    age_score = compute_age_experience_score(prospect)
    position_value_score = compute_position_value_score(prospect.position)
    nfl_projection_score, projection_note = compute_nfl_projection_score(
        production_score, athletic_score, prospect, draft_class
    )
    risk_profile = compute_risk_profile(prospect, production_score, athletic_score)
    risk_adjustment_score = round(100 - risk_profile.overall_risk, 2)

    w = weights.normalized()
    components = {
        "production": production_score,
        "athletic_profile": athletic_score,
        "age_experience": age_score,
        "position_value": position_value_score,
        "nfl_projection": nfl_projection_score,
        "risk_adjustment": risk_adjustment_score,
    }
    grade = round(sum(components[k] * w[k] for k in components), 2)

    breakdown = ScoreBreakdown(
        score=grade,
        components=components,
        notes={
            "production": f"percentile within {prospect.position} peers in the {prospect.draft_year} class",
            "athletic_profile": "percentile on position-weighted combine testing",
            "age_experience": "younger age and more proven experience score higher",
            "position_value": "static positional value/scarcity assumption (configurable)",
            "nfl_projection": projection_note,
            "risk_adjustment": "100 minus overall Risk Score",
        },
    )
    return breakdown, risk_profile
