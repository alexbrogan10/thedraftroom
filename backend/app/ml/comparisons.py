"""
Historical Player Comparison engine.

Compares a current prospect against historical players using ONLY
measurables and production information that would have been known before
that historical player's NFL career began (age, height, weight, 40 time,
college production percentile). No post-draft NFL outcome data is used as an
input feature here — this is a pre-draft similarity search, not an outcome
prediction (see app/ml/outcome_model.py and docs/model_documentation.md for
the leakage-prevention rules that govern outcome prediction specifically).

Method: StandardScaler to normalize feature scales, then cosine similarity
between the prospect's feature vector and each historical player's, restricted
to the same position group so comparisons stay meaningful.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

FEATURE_FIELDS = ["age", "height_inches", "weight_lbs", "forty_yard_dash", "college_production_score"]


@dataclass
class HistoricalCandidate:
    player_name: str
    position: str
    college: str | None
    draft_year: int
    age: float | None
    height_inches: float | None
    weight_lbs: float | None
    forty_yard_dash: float | None
    college_production_score: float | None


@dataclass
class ComparisonResult:
    player_name: str
    position: str
    college: str | None
    draft_year: int
    similarity: float  # 0-100


def _vectorize(records: list[dict]) -> np.ndarray:
    matrix = np.array([[r.get(f) for f in FEATURE_FIELDS] for r in records], dtype=float)
    col_means = np.nanmean(matrix, axis=0)
    col_means = np.where(np.isnan(col_means), 0, col_means)
    inds = np.where(np.isnan(matrix))
    matrix[inds] = np.take(col_means, inds[1])
    return matrix


def find_similar_players(
    prospect_record: dict,
    candidates: list[HistoricalCandidate],
    top_n: int = 3,
) -> list[ComparisonResult]:
    same_position = [c for c in candidates if c.position == prospect_record["position"]]
    if not same_position:
        return []

    rows = [prospect_record] + [
        {
            "age": c.age,
            "height_inches": c.height_inches,
            "weight_lbs": c.weight_lbs,
            "forty_yard_dash": c.forty_yard_dash,
            "college_production_score": c.college_production_score,
        }
        for c in same_position
    ]
    matrix = _vectorize(rows)
    scaled = StandardScaler().fit_transform(matrix)

    prospect_vec = scaled[0:1]
    candidate_vecs = scaled[1:]
    similarities = cosine_similarity(prospect_vec, candidate_vecs)[0]

    scored = sorted(zip(same_position, similarities), key=lambda x: x[1], reverse=True)[:top_n]

    results = []
    for candidate, sim in scored:
        pct = round(float(max(0, min(1, (sim + 1) / 2))) * 100, 1)
        results.append(
            ComparisonResult(
                player_name=candidate.player_name,
                position=candidate.position,
                college=candidate.college,
                draft_year=candidate.draft_year,
                similarity=pct,
            )
        )
    return results
