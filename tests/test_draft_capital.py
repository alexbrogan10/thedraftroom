from app.analytics.draft_capital import availability_probability, traditional_value


def test_traditional_value_decreases_monotonically():
    values = [traditional_value(p) for p in [1, 16, 32, 64, 128, 262]]
    assert values == sorted(values, reverse=True)
    assert values[0] == 1000.0


def test_availability_probability_bounds():
    assert 0 <= availability_probability(12, 40.0, 8.0) <= 1
    assert availability_probability(1, None) == 0.5


def test_availability_probability_direction():
    """On the clock well before a player's projected slot, the player should
    be very likely still available; well after, very unlikely."""
    early = availability_probability(pick_number=5, consensus_pick=60.0, spread=8.0)
    late = availability_probability(pick_number=120, consensus_pick=60.0, spread=8.0)
    assert early > 0.9
    assert late < 0.1
    assert early > late
