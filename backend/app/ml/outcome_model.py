"""
NFL Outcome Prediction model.

Predicts the probability that a prospect reaches each of three configurable
outcome tiers (see docs/model_documentation.md for exact label definitions):
  - started: became a consistent NFL starter
  - productive_starter: started AND cleared a higher performance bar
  - long_term_contributor: remained a meaningful contributor across seasons

DATA LEAKAGE PREVENTION: training features are restricted to information
that exists BEFORE the draft (age, height, weight, 40 time, college
production percentile, draft pick/round). Outcome data (`nfl_outcomes`) is
used only to build the training LABELS, never as an input feature. See
`app/ml/outcome_features.py` for the single shared feature-builder used by
both training and inference, so the two can never drift apart.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import joblib

from app.ml.outcome_features import LABELS

MODELS_DIR = Path(os.environ.get("MODELS_DIR", Path(__file__).resolve().parents[3] / "models"))

_cache: dict | None = None


def models_available() -> bool:
    return (MODELS_DIR / "metrics.json").exists()


def _load() -> dict:
    global _cache
    if _cache is not None:
        return _cache
    pipelines = {}
    for label in LABELS:
        path = MODELS_DIR / f"outcome_{label}.joblib"
        if path.exists():
            pipelines[label] = joblib.load(path)
    metrics = {}
    metrics_path = MODELS_DIR / "metrics.json"
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text())
    _cache = {"pipelines": pipelines, "metrics": metrics}
    return _cache


def get_metrics() -> dict:
    return _load()["metrics"]


def predict_probabilities(feature_row: dict) -> dict[str, float] | None:
    from app.ml.outcome_features import build_feature_frame

    state = _load()
    if not state["pipelines"]:
        return None
    frame = build_feature_frame([feature_row])
    results = {}
    for label, pipeline in state["pipelines"].items():
        proba = pipeline.predict_proba(frame)[0]
        classes = list(pipeline.classes_)
        idx = classes.index(True) if True in classes else classes.index(1)
        results[label] = round(float(proba[idx]) * 100, 1)
    return results
