from app.analytics.reference import POSITION_VALUE
from app.analytics.scoring import (
    compute_age_experience_score,
    compute_draft_grade,
    compute_position_value_score,
    compute_production_score,
    compute_risk_profile,
    percentile_rank,
)
from app.analytics.types import ProspectFeatures
from app.config import DraftGradeWeights


def make_wr(id_, name, receiving_yards, receptions=60, tds=6, ypr=13.0, target_share=20.0, age=21.0):
    return ProspectFeatures(
        id=id_,
        name=name,
        position="WR",
        college="Test State",
        age=age,
        class_year="Jr",
        draft_year=2026,
        stats={
            "receiving_yards": receiving_yards,
            "receptions": receptions,
            "receiving_tds": tds,
            "yards_per_reception": ypr,
            "target_share": target_share,
        },
        combine={"forty_yard_dash": 4.45, "vertical_jump": 36, "broad_jump": 122, "bench_press": 12, "three_cone": 6.9, "shuttle": 4.1},
        projected_picks=[40.0, 55.0],
    )


def test_percentile_rank_basic():
    assert percentile_rank(50, [10, 20, 30, 40, 50]) == 100.0
    assert percentile_rank(5, [10, 20, 30]) == 0.0
    assert percentile_rank(10, []) == 50.0


def test_production_score_rewards_better_stats():
    peers = [make_wr(2, "Peer A", 700), make_wr(3, "Peer B", 900), make_wr(4, "Peer C", 500)]
    star = make_wr(1, "Star", 1400)
    scrub = make_wr(5, "Scrub", 300)

    star_score, _ = compute_production_score(star, peers)
    scrub_score, _ = compute_production_score(scrub, peers)
    assert star_score > scrub_score


def test_age_experience_prefers_younger_and_more_experienced():
    young_senior = compute_age_experience_score(
        ProspectFeatures(id=1, name="A", position="WR", college="X", age=21, class_year="Sr", draft_year=2026)
    )
    old_freshman = compute_age_experience_score(
        ProspectFeatures(id=2, name="B", position="WR", college="X", age=24, class_year="Fr", draft_year=2026)
    )
    assert young_senior > old_freshman
    assert 0 <= young_senior <= 100
    assert 0 <= old_freshman <= 100


def test_position_value_matches_reference_table():
    assert compute_position_value_score("QB") == POSITION_VALUE["QB"]
    assert compute_position_value_score("RB") == POSITION_VALUE["RB"]
    # Unknown position falls back to a safe default rather than raising.
    assert compute_position_value_score("XYZ") == 60


def test_draft_grade_is_bounded_and_explainable():
    peers = [make_wr(i, f"Peer {i}", 500 + i * 40) for i in range(2, 8)]
    prospect = make_wr(1, "Featured", 1200)
    class_pool = peers + [prospect]

    breakdown, risk = compute_draft_grade(prospect, class_pool, DraftGradeWeights())

    assert 0 <= breakdown.score <= 100
    assert set(breakdown.components) == {
        "production", "athletic_profile", "age_experience",
        "position_value", "nfl_projection", "risk_adjustment",
    }
    for value in breakdown.components.values():
        assert 0 <= value <= 100
    assert set(breakdown.notes) == set(breakdown.components)
    assert 0 <= risk.overall_risk <= 100


def test_draft_grade_weights_are_normalized_even_if_misconfigured():
    peers = [make_wr(i, f"Peer {i}", 500 + i * 40) for i in range(2, 5)]
    prospect = make_wr(1, "Featured", 900)
    class_pool = peers + [prospect]

    lopsided = DraftGradeWeights(production=2.0, athletic_profile=2.0, age_experience=0, position_value=0, nfl_projection=0, risk_adjustment=0)
    breakdown, _ = compute_draft_grade(prospect, class_pool, lopsided)
    assert 0 <= breakdown.score <= 100


def test_risk_profile_buckets_and_bounds():
    peers = [make_wr(i, f"Peer {i}", 500 + i * 40) for i in range(2, 8)]
    prospect = make_wr(1, "Featured", 1200)
    prod_score, _ = compute_production_score(prospect, peers)

    risk = compute_risk_profile(prospect, prod_score, athletic_score=80.0)

    assert 0 <= risk.overall_risk <= 100
    assert risk.risk_level in {"LOWER RISK", "MODERATE RISK", "HIGHER RISK"}
    for factor in risk.factors.values():
        assert 0 <= factor["score"] <= 100
        assert factor["level"] in {"Low", "Moderate", "High"}


def test_risk_profile_never_labels_a_player_a_bust():
    peers = [make_wr(i, f"Peer {i}", 200) for i in range(2, 5)]
    worst_case = make_wr(1, "Struggling", 50, receptions=5, tds=0)
    prod_score, _ = compute_production_score(worst_case, peers)
    risk = compute_risk_profile(worst_case, prod_score, athletic_score=20.0)
    assert "bust" not in risk.risk_level.lower()
