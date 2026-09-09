"""
Trains the NFL Outcome Prediction models (Feature 9 / Phase 4).

Reads historical, pre-draft-only prospect features from PostgreSQL
(`historical_draft_results`, joined to `players`), and outcome LABELS from
`nfl_outcomes` (used only as labels — see app/ml/outcome_features.py for the
leakage-prevention rationale). Trains one RandomForestClassifier per outcome
tier, evaluates on a held-out split, and writes:
  models/outcome_<label>.joblib   (one per label)
  models/metrics.json             (evaluation metrics + metadata)

Run (from repo root, backend virtualenv active):
    python scripts/train_outcome_model.py

NOTE: this repo's historical data is a small, synthetic demo dataset (see
docs/data_sources.md). The metrics this script produces are illustrative of
the pipeline, not a claim about real-world predictive accuracy.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(os.environ.get("BACKEND_DIR", ROOT / "backend"))
sys.path.insert(0, str(BACKEND_DIR))

from app.database.session import SessionLocal  # noqa: E402
from app.ml.outcome_features import FEATURE_COLUMNS, LABELS, NUMERIC_FEATURES, build_feature_frame  # noqa: E402
from app.models.historical import HistoricalDraftResult, NflOutcome  # noqa: E402

MODELS_DIR = Path(os.environ.get("MODELS_DIR", ROOT / "models"))
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def load_training_rows() -> tuple[list[dict], dict[str, list[bool]]]:
    db = SessionLocal()
    try:
        results = (
            db.query(HistoricalDraftResult)
            .filter(HistoricalDraftResult.player_id.isnot(None))
            .all()
        )
        rows, labels = [], {label: [] for label in LABELS}
        for r in results:
            outcome = (
                db.query(NflOutcome)
                .filter(NflOutcome.player_id == r.player_id)
                .order_by(NflOutcome.season.desc())
                .first()
            )
            if outcome is None or not outcome.performance_metrics:
                continue
            rows.append({
                "age": r.age,
                "height_inches": r.height_inches,
                "weight_lbs": r.weight_lbs,
                "forty_yard_dash": r.forty_yard_dash,
                "college_production_score": r.college_production_score,
                "draft_pick": r.draft_pick,
                "draft_round": r.draft_round,
                "position": r.position,
            })
            for label in LABELS:
                labels[label].append(bool(outcome.performance_metrics.get(label, False)))
        return rows, labels
    finally:
        db.close()


def build_pipeline() -> Pipeline:
    onehot_cols = [c for c in FEATURE_COLUMNS if c not in NUMERIC_FEATURES]
    preprocessor = ColumnTransformer([
        ("numeric", Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]), NUMERIC_FEATURES),
        ("position", "passthrough", onehot_cols),
    ])
    return Pipeline([
        ("preprocess", preprocessor),
        ("classifier", RandomForestClassifier(
            n_estimators=200, max_depth=6, min_samples_leaf=3,
            class_weight="balanced", random_state=42,
        )),
    ])


def run():
    print("== Training NFL Outcome Prediction models ==")
    rows, labels = load_training_rows()
    if len(rows) < 20:
        print(f"Only {len(rows)} labeled historical rows found — run scripts/ingest.py first. Aborting.")
        return

    frame = build_feature_frame(rows)
    metrics_out = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "n_samples": len(rows),
        "feature_columns": FEATURE_COLUMNS,
        "disclaimer": (
            "Trained on a small, synthetic demo historical dataset (see docs/data_sources.md). "
            "These metrics describe the pipeline's behavior on demo data and are NOT a claim of "
            "real-world predictive accuracy. Historical performance does not guarantee future "
            "predictive accuracy."
        ),
        "labels": {},
    }

    for label in LABELS:
        y = pd.Series(labels[label])
        if y.nunique() < 2:
            print(f"  [skip] {label}: only one class present in demo data")
            continue
        X_train, X_test, y_train, y_test = train_test_split(
            frame, y, test_size=0.25, random_state=42, stratify=y
        )
        pipeline = build_pipeline()
        pipeline.fit(X_train, y_train)

        y_pred = pipeline.predict(X_test)
        y_proba = pipeline.predict_proba(X_test)[:, list(pipeline.classes_).index(True)]

        label_metrics = {
            "accuracy": round(accuracy_score(y_test, y_pred), 3),
            "precision": round(precision_score(y_test, y_pred, zero_division=0), 3),
            "recall": round(recall_score(y_test, y_pred, zero_division=0), 3),
            "f1": round(f1_score(y_test, y_pred, zero_division=0), 3),
            "roc_auc": round(roc_auc_score(y_test, y_proba), 3) if y_test.nunique() > 1 else None,
            "n_train": len(X_train),
            "n_test": len(X_test),
            "positive_rate": round(float(y.mean()), 3),
        }
        metrics_out["labels"][label] = label_metrics
        joblib.dump(pipeline, MODELS_DIR / f"outcome_{label}.joblib")
        print(f"  -> {label}: {label_metrics}")

    (MODELS_DIR / "metrics.json").write_text(json.dumps(metrics_out, indent=2))
    print(f"== Saved models + metrics to {MODELS_DIR} ==")


if __name__ == "__main__":
    run()
