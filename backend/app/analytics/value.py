"""Hidden Value Finder: compares each prospect's analytical draft-class rank
against its expected (consensus) draft position."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ValueAssessment:
    analytical_rank: int
    expected_rank: float | None
    differential: float | None  # positive = model ranks the player ahead of consensus
    value_score: float
    classification: str
    icon: str
    explanation: str


_BANDS = [
    (25, "Significant Value", "🔥"),
    (10, "Potential Value", "🟢"),
    (-9, "Fair Value", "⚪"),
    (-24, "Potential Reach", "🟠"),
]


def classify_differential(differential: float) -> tuple[str, str]:
    for threshold, label, icon in _BANDS:
        if differential >= threshold:
            return label, icon
    return "Significant Reach", "🔴"


def compute_value_assessment(analytical_rank: int, expected_rank: float | None) -> ValueAssessment:
    if expected_rank is None:
        return ValueAssessment(
            analytical_rank=analytical_rank,
            expected_rank=None,
            differential=None,
            value_score=50.0,
            classification="Fair Value",
            icon="⚪",
            explanation="No consensus draft projection is available for this prospect, "
            "so no value differential can be computed.",
        )

    differential = round(expected_rank - analytical_rank, 1)
    classification, icon = classify_differential(differential)
    value_score = round(max(0.0, min(100.0, 50 + differential)), 1)

    if differential > 0:
        direction = (
            f"The model identifies this prospect as potentially undervalued relative to the "
            f"expected draft range — ranked #{analytical_rank} analytically versus an expected "
            f"range near #{expected_rank:.0f}."
        )
    elif differential < 0:
        direction = (
            f"The model ranks this prospect lower than the expected draft range — "
            f"#{analytical_rank} analytically versus an expected range near #{expected_rank:.0f} — "
            f"suggesting possible reach risk at that range."
        )
    else:
        direction = "The analytical rank and expected draft range are closely aligned."

    return ValueAssessment(
        analytical_rank=analytical_rank,
        expected_rank=expected_rank,
        differential=differential,
        value_score=value_score,
        classification=classification,
        icon=icon,
        explanation=direction,
    )
