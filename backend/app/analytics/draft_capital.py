"""
Draft Capital Model: pick valuation and pick-availability probability.

`traditional_value` is a smooth exponential approximation of the well-known
shape of "trade value chart" curves (steep early, flat late) — it is NOT a
reproduction of any team's or media outlet's proprietary chart, and is one
configurable valuation model among the several the roadmap calls for
(Traditional Value implemented; Historical Player Value and Custom Model are
future roadmap items — see docs/scoring_methodology.md).
"""
from __future__ import annotations

import math

# Calibrated so pick #1 = 1000 points and pick #32 ≈ 25% of pick #1, which
# roughly matches the decay shape of commonly published trade value charts.
_DECAY_K = 0.0455


def traditional_value(pick: int) -> float:
    pick = max(1, pick)
    return round(1000 * math.exp(-_DECAY_K * (pick - 1)), 1)


def nearest_round_label(value_points: float) -> str:
    """Expresses a value-point amount as an approximate equivalent pick, for
    human-readable trade cost descriptions."""
    thresholds = [
        (traditional_value(1), "a 1st-round pick (top of round)"),
        (traditional_value(16), "a mid/late 1st-round pick"),
        (traditional_value(48), "a 2nd-round pick"),
        (traditional_value(80), "a 3rd-round pick"),
        (traditional_value(112), "a 4th-round pick"),
        (traditional_value(144), "a 5th-round pick"),
        (traditional_value(176), "a 6th-round pick"),
        (traditional_value(208), "a 7th-round pick"),
    ]
    for threshold_value, label in thresholds:
        if value_points >= threshold_value:
            return label
    return "a late 7th-round pick"


def availability_probability(
    pick_number: int, consensus_pick: float | None, spread: float | None = None
) -> float:
    """Probability (0-1) that a prospect projected to `consensus_pick` is
    still available when a team is on the clock at `pick_number`, modeled as
    a logistic function centered on the consensus projection. Wider
    cross-source projection spread widens the uncertainty band."""
    if consensus_pick is None:
        return 0.5
    scale = max(4.0, spread or 8.0)
    x = (consensus_pick - pick_number) / scale
    return round(1 / (1 + math.exp(-x)), 3)
