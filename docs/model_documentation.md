# Model Documentation

This document covers the two places The Draft Room uses machine learning, in
addition to the rule-based analytics engine documented in
`scoring_methodology.md`.

## 1. Historical Player Comparison Engine

`backend/app/ml/comparisons.py`, served at
`GET /api/prospects/{id}/comparisons`.

**Purpose:** find the historical players whose *pre-draft* profile most
closely resembles a current prospect's — not to predict outcomes.

**Method:**
1. Features: age, height (in), weight (lbs), 40-yard dash, and a college
   production percentile score — all restricted to the same position.
2. `sklearn.preprocessing.StandardScaler` normalizes each feature to zero
   mean / unit variance across the comparison pool, so no single feature
   (e.g., weight, on a scale of hundreds) dominates the distance metric.
3. `sklearn.metrics.pairwise.cosine_similarity` computes similarity between
   the prospect's feature vector and every historical candidate's; the top 3
   are returned with a 0–100% similarity score.

**What this is not:** a prediction. Every comparison in the UI is paired
with the fixed disclaimer *"These players had similar measurable and
production profiles entering the NFL"* — never "this prospect will become
Player X."

## 2. NFL Outcome Prediction

`backend/app/ml/outcome_model.py`, `app/ml/outcome_features.py`,
trained by `scripts/train_outcome_model.py`, served at
`GET /api/prospects/{id}/outcome-prediction` and
`GET /api/model/performance`.

### Outcome label definitions

Three binary outcome tiers, computed from `nfl_outcomes` (post-draft
participation data) and used **only as training labels**:

| Label | Definition |
|---|---|
| `started` | Became a consistent NFL starter |
| `productive_starter` | Started **and** cleared a higher performance bar |
| `long_term_contributor` | Remained a meaningful roster contributor across multiple seasons |

In this repository's synthetic demo dataset, these three booleans are
generated directly (see the "DEMO DATA DISCLOSURE" comment block in
`scripts/generate_demo_data.py`) as a noisy function of each historical
player's latent "talent" value, specifically so that outcome is *not*
perfectly predictable from pre-draft measurables — draft outcomes are
genuinely uncertain, and a leakage-free model trained on real data would
show a similarly imperfect (not perfect) fit. When connecting a real
historical dataset, replace this generator with your own rule, e.g.
`started = (starts ≥ 8 in ≥ 2 of the first 4 NFL seasons)`, computed from
real season-by-season participation.

### Data leakage prevention (read this before changing the model)

This is the most important constraint on this part of the codebase:

> **Training features may only include information that was knowable
> before the player was drafted.**

Concretely, `app/ml/outcome_features.py::FEATURE_COLUMNS` is:

```
age, height_inches, weight_lbs, forty_yard_dash, college_production_score,
draft_pick, draft_round, position_<QB..S> (one-hot)
```

`draft_pick`/`draft_round` are included because they are determined *at* the
draft (a function of team evaluations up to that point), not after it — they
are not post-hoc outcome data.

**Never add to this feature list:** NFL rookie statistics, NFL career
statistics, future Pro Bowls/All-Pro selections, second-contract value, or
anything else that could only be known after the player took an NFL snap.
`nfl_outcomes` (including `games`, `starts`, and `performance_metrics`) is
loaded only to build the label columns in
`scripts/train_outcome_model.py::load_training_rows` — it is deliberately
never joined into the feature frame.

Both the training script and the live prediction path
(`app/ml/outcome_model.py::predict_probabilities`) call the *same*
`build_feature_frame()` function in `outcome_features.py`, specifically so
the two can never silently drift into using different (and possibly
leaky) feature sets.

### Model

- **Algorithm:** `sklearn.ensemble.RandomForestClassifier`
  (`n_estimators=200, max_depth=6, min_samples_leaf=3,
  class_weight="balanced"`), chosen for robustness to a small, noisy,
  nonlinear demo dataset over a linear model like Logistic Regression.
- **Preprocessing:** numeric features go through median imputation +
  `StandardScaler`; position is already one-hot encoded upstream.
- **One independent model per outcome label** — `started`,
  `productive_starter`, `long_term_contributor` are each a separate
  binary classifier, not a shared multi-output model, so each can be
  evaluated and reasoned about independently.
- **Evaluation:** a stratified 75/25 train/test split;
  accuracy, precision, recall, F1, and ROC-AUC are computed on the held-out
  25% and written to `models/metrics.json`, which is what
  `GET /api/model/performance` and the "Data & Model" page in the UI serve.

### Output

`GET /api/prospects/{id}/outcome-prediction` returns three probabilities
(0–100%), always paired with the note *"Model estimate based on pre-draft
data only. Not a guarantee of NFL outcome."* These are model estimates, not
facts, and the UI never presents them otherwise.

### Limitations (be honest about these)

- The historical dataset shipped with this repo is **small (275 rows) and
  synthetic** — see `docs/data_sources.md`. The metrics you'll see are
  illustrative of the pipeline working correctly, not a claim about
  real-world predictive power.
- Historical performance does not guarantee future predictive accuracy —
  this line appears verbatim next to every metrics display in the UI.
- A production deployment would need materially more historical rows (ideally
  every draftable prospect from ~10+ real draft classes) before these
  probabilities should inform any real decision.
