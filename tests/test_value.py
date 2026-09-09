from app.analytics.value import classify_differential, compute_value_assessment


def test_classify_differential_bands():
    assert classify_differential(30)[0] == "Significant Value"
    assert classify_differential(15)[0] == "Potential Value"
    assert classify_differential(0)[0] == "Fair Value"
    assert classify_differential(-15)[0] == "Potential Reach"
    assert classify_differential(-30)[0] == "Significant Reach"


def test_value_assessment_direction_is_intuitive():
    """A prospect ranked much better than its expected draft range should be
    flagged as a value, with a positive differential and a score above 50."""
    undervalued = compute_value_assessment(analytical_rank=22, expected_rank=55)
    assert undervalued.differential == 33
    assert undervalued.value_score > 50
    assert "undervalued" in undervalued.explanation.lower()

    overvalued = compute_value_assessment(analytical_rank=55, expected_rank=22)
    assert overvalued.differential == -33
    assert overvalued.value_score < 50
    assert "reach" in overvalued.explanation.lower()


def test_value_assessment_handles_missing_projection():
    result = compute_value_assessment(analytical_rank=10, expected_rank=None)
    assert result.classification == "Fair Value"
    assert result.differential is None
    assert result.value_score == 50.0


def test_value_score_is_bounded():
    extreme = compute_value_assessment(analytical_rank=1, expected_rank=300)
    assert 0 <= extreme.value_score <= 100
