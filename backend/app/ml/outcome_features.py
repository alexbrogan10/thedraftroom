"""
Single source of truth for the NFL Outcome Prediction model's feature
schema, imported by both the training script (scripts/train_outcome_model.py)
and the live prediction path (app/ml/outcome_model.py) so they can never
silently drift apart.

Every field here is knowable BEFORE a player is drafted. See
docs/model_documentation.md for the full data-leakage-prevention rationale.
"""
from __future__ import annotations

import pandas as pd

POSITIONS = ["QB", "RB", "WR", "TE", "OT", "IOL", "EDGE", "IDL", "LB", "CB", "S"]

NUMERIC_FEATURES = [
    "age",
    "height_inches",
    "weight_lbs",
    "forty_yard_dash",
    "college_production_score",
    "draft_pick",
    "draft_round",
]

FEATURE_COLUMNS = NUMERIC_FEATURES + [f"position_{p}" for p in POSITIONS]

LABELS = ["started", "productive_starter", "long_term_contributor"]


def build_feature_frame(rows: list[dict]) -> pd.DataFrame:
    """rows: list of dicts with keys from NUMERIC_FEATURES + 'position'."""
    df = pd.DataFrame(rows)
    for col in NUMERIC_FEATURES:
        if col not in df:
            df[col] = None
        df[col] = pd.to_numeric(df[col], errors="coerce")

    for position in POSITIONS:
        df[f"position_{position}"] = (df.get("position") == position).astype(int)

    return df[FEATURE_COLUMNS]
