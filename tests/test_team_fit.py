from app.analytics.team_fit import TeamContext, compute_team_fit
from app.analytics.types import ProspectFeatures


def make_prospect(position="CB", age=21.5):
    return ProspectFeatures(
        id=1, name="Prospect", position=position, college="Test State",
        age=age, class_year="Jr", draft_year=2026,
    )


def make_team(**overrides):
    defaults = dict(
        team_id=1, name="Test Team", abbreviation="TST",
        offensive_scheme="West Coast Offense", defensive_scheme="Man Press",
        needs_by_position={"CB": {2026: 80.0, 2027: 85.0}},
        roster_counts_by_position={"CB": 1},
        roster_avg_age_by_position={"CB": 29.0},
    )
    defaults.update(overrides)
    return TeamContext(**defaults)


def test_team_fit_score_is_bounded():
    fit = compute_team_fit(make_prospect(), make_team(), current_season=2026)
    assert 0 <= fit.score <= 100
    for value in fit.components.values():
        assert 0 <= value <= 100
    assert set(fit.explanations) == set(fit.components)


def test_higher_current_need_increases_fit():
    low_need = compute_team_fit(
        make_prospect(), make_team(needs_by_position={"CB": {2026: 20.0}}), current_season=2026
    )
    high_need = compute_team_fit(
        make_prospect(), make_team(needs_by_position={"CB": {2026: 90.0}}), current_season=2026
    )
    assert high_need.score > low_need.score


def test_existing_roster_depth_reduces_fit():
    """Mirrors the spec example: a talented prospect should score lower on a
    team that already has significant depth at his position."""
    thin_roster = compute_team_fit(
        make_prospect(), make_team(roster_counts_by_position={"CB": 0}), current_season=2026
    )
    deep_roster = compute_team_fit(
        make_prospect(), make_team(roster_counts_by_position={"CB": 3}), current_season=2026
    )
    assert thin_roster.components["roster_depth"] > deep_roster.components["roster_depth"]
    assert thin_roster.score > deep_roster.score


def test_scheme_fit_rewards_matching_scheme():
    man_scheme = compute_team_fit(
        make_prospect(position="CB"), make_team(defensive_scheme="Man Press"), current_season=2026
    )
    mismatched_scheme = compute_team_fit(
        make_prospect(position="CB"), make_team(defensive_scheme="4-3 Zone"), current_season=2026
    )
    assert man_scheme.components["scheme_fit"] >= mismatched_scheme.components["scheme_fit"]
